"""Security utilities for password hashing, JWT tokens, and OAuth verification."""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
import redis.asyncio as aioredis
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pwdlib import PasswordHash

from app.core.config import settings

# Password hashing with Argon2
password_hash = PasswordHash.recommended()

# OAuth2 scheme for Bearer tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Redis client for refresh token storage
redis_client = aioredis.from_url(
    settings.CELERY_BROKER_URL,
    encoding="utf-8",
    decode_responses=True,
)

# Token serializers for email verification and password reset
verification_serializer = URLSafeTimedSerializer(
    settings.SECRET_KEY, salt="email-verification"
)
password_reset_serializer = URLSafeTimedSerializer(
    settings.SECRET_KEY, salt="password-reset"
)

# Cache for OAuth provider public keys (kid -> key, timestamp)
_oauth_key_cache: dict[str, tuple[Any, float]] = {}
_CACHE_TTL = 86400  # 24 hours


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using Argon2."""
    return password_hash.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token.

    Args:
        data: Dictionary containing user_id and other claims
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({
        "exp": expire,
        "sub": str(data.get("user_id")),
        "type": "access",
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


async def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token and store its hash in Redis.

    Args:
        user_id: User ID to encode in the token

    Returns:
        Encoded JWT refresh token string
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
    }

    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

    # Store token hash in Redis
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    redis_key = f"refresh_token:{user_id}:{token_hash}"
    ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400

    await redis_client.setex(redis_key, ttl_seconds, "1")

    return token


async def verify_refresh_token(token: str) -> str:
    """Verify a refresh token and return the user_id.

    Args:
        token: JWT refresh token string

    Returns:
        User ID extracted from the token

    Raises:
        HTTPException: If token is invalid or revoked
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        # Check if token exists in Redis (not revoked)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        redis_key = f"refresh_token:{user_id}:{token_hash}"

        exists = await redis_client.exists(redis_key)
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token revoked or expired",
            )

        return user_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


async def revoke_refresh_token(user_id: str, token: str) -> None:
    """Revoke a specific refresh token.

    Args:
        user_id: User ID owning the token
        token: JWT refresh token to revoke
    """
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    redis_key = f"refresh_token:{user_id}:{token_hash}"
    await redis_client.delete(redis_key)


async def revoke_all_user_tokens(user_id: str) -> None:
    """Revoke all refresh tokens for a user.

    Args:
        user_id: User ID whose tokens should be revoked
    """
    # Find all keys matching the pattern
    pattern = f"refresh_token:{user_id}:*"
    cursor = 0

    # Use SCAN to iterate through keys
    while True:
        cursor, keys = await redis_client.scan(cursor, match=pattern, count=100)
        if keys:
            await redis_client.delete(*keys)
        if cursor == 0:
            break


def generate_verification_token(email: str) -> str:
    """Generate an email verification token.

    Args:
        email: Email address to encode in the token

    Returns:
        URL-safe verification token
    """
    return verification_serializer.dumps(email)


def verify_verification_token(token: str, max_age: int = 3600) -> str:
    """Verify an email verification token.

    Args:
        token: URL-safe verification token
        max_age: Maximum age in seconds (default: 1 hour)

    Returns:
        Email address extracted from the token

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        email = verification_serializer.loads(token, max_age=max_age)
        return email
    except SignatureExpired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Verification token expired",
        )
    except BadSignature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification token",
        )


def generate_password_reset_token(email: str) -> str:
    """Generate a password reset token.

    Args:
        email: Email address to encode in the token

    Returns:
        URL-safe reset token
    """
    return password_reset_serializer.dumps(email)


def verify_password_reset_token(token: str, max_age: int = 3600) -> str:
    """Verify a password reset token.

    Args:
        token: URL-safe reset token
        max_age: Maximum age in seconds (default: 1 hour)

    Returns:
        Email address extracted from the token

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        email = password_reset_serializer.loads(token, max_age=max_age)
        return email
    except SignatureExpired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Reset token expired",
        )
    except BadSignature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid reset token",
        )


async def get_oauth_public_keys(url: str) -> dict:
    """Fetch OAuth provider's public keys (JWKs) with caching.

    Args:
        url: URL to fetch JWKs from

    Returns:
        Dictionary mapping kid to JWK
    """
    import httpx

    # Check cache
    now = datetime.now(timezone.utc).timestamp()
    if url in _oauth_key_cache:
        keys, timestamp = _oauth_key_cache[url]
        if now - timestamp < _CACHE_TTL:
            return keys

    # Fetch fresh keys
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        jwks = response.json()

    # Build kid -> key mapping
    keys = {key["kid"]: key for key in jwks.get("keys", [])}
    _oauth_key_cache[url] = (keys, now)

    return keys


async def verify_apple_token(identity_token: str) -> dict:
    """Verify Apple Sign In identity token.

    Args:
        identity_token: JWT identity token from Apple

    Returns:
        Dictionary with user info (sub, email)

    Raises:
        HTTPException: If token is invalid
    """
    try:
        # Decode header to get kid
        unverified_header = jwt.get_unverified_header(identity_token)
        kid = unverified_header.get("kid")

        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Apple token: missing kid",
            )

        # Fetch Apple's public keys
        keys = await get_oauth_public_keys("https://appleid.apple.com/auth/keys")

        if kid not in keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Apple token: unknown kid",
            )

        # Convert JWK to PEM and verify
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(keys[kid]))

        payload = jwt.decode(
            identity_token,
            public_key,
            algorithms=["RS256"],
            audience=settings.APPLE_CLIENT_ID if hasattr(settings, "APPLE_CLIENT_ID") else None,
            issuer="https://appleid.apple.com",
        )

        return {
            "sub": payload.get("sub"),
            "email": payload.get("email"),  # May be None with "Hide My Email"
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Apple token expired",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Apple token: {str(e)}",
        )


async def verify_google_token(id_token: str) -> dict:
    """Verify Google Sign In ID token.

    Args:
        id_token: JWT ID token from Google

    Returns:
        Dictionary with user info (sub, email)

    Raises:
        HTTPException: If token is invalid
    """
    try:
        # Decode header to get kid
        unverified_header = jwt.get_unverified_header(id_token)
        kid = unverified_header.get("kid")

        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token: missing kid",
            )

        # Fetch Google's public keys
        keys = await get_oauth_public_keys(
            "https://www.googleapis.com/oauth2/v3/certs"
        )

        if kid not in keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token: unknown kid",
            )

        # Convert JWK to PEM and verify
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(keys[kid]))

        payload = jwt.decode(
            id_token,
            public_key,
            algorithms=["RS256"],
            audience=settings.GOOGLE_CLIENT_ID if hasattr(settings, "GOOGLE_CLIENT_ID") else None,
            issuer="https://accounts.google.com",
        )

        return {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token expired",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}",
        )
