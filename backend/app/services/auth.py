"""Authentication service layer with business logic."""

from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_password_reset_token,
    generate_verification_token,
    get_password_hash,
    revoke_all_user_tokens,
    revoke_refresh_token,
    verify_apple_token,
    verify_google_token,
    verify_password,
    verify_password_reset_token,
    verify_refresh_token,
    verify_verification_token,
)
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.workers.tasks.email import send_password_reset_email, send_verification_email


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User:
    """Register a new user with email and password.

    Args:
        db: Database session
        email: User email address
        password: Plain text password

    Returns:
        Created user object

    Raises:
        HTTPException: If email already exists
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        is_active=True,
        is_verified=False,
    )

    db.add(user)
    await db.flush()  # Flush to get user.id without committing
    await db.refresh(user)

    # Send verification email (async Celery task)
    verification_token = generate_verification_token(email)
    send_verification_email.delay(email, verification_token)

    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    """Authenticate a user with email and password.

    Args:
        db: Database session
        email: User email address
        password: Plain text password

    Returns:
        User object if authentication successful, None otherwise
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        return None

    if not user.hashed_password:
        # OAuth user without password
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> TokenResponse:
    """Login user and create access + refresh tokens.

    Args:
        db: Database session
        email: User email address
        password: Plain text password

    Returns:
        TokenResponse with access and refresh tokens

    Raises:
        HTTPException: If authentication fails or user is inactive
    """
    user = await authenticate_user(db, email, password)

    if not user:
        # Generic error message to prevent email enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Create tokens
    access_token = create_access_token(
        data={"user_id": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = await create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


async def refresh_tokens(refresh_token: str) -> TokenResponse:
    """Create new access token using refresh token.

    Args:
        refresh_token: Valid refresh token

    Returns:
        TokenResponse with new access token and same refresh token

    Raises:
        HTTPException: If refresh token is invalid or revoked
    """
    # Verify refresh token and get user_id
    user_id = await verify_refresh_token(refresh_token)

    # Create new access token
    access_token = create_access_token(
        data={"user_id": user_id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # Optionally rotate refresh token (keeping same one for simplicity)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


async def verify_email(
    db: AsyncSession,
    token: str,
) -> User:
    """Verify user email with verification token.

    Args:
        db: Database session
        token: Email verification token

    Returns:
        Updated user object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Verify token and extract email
    email = verify_verification_token(token, max_age=86400)  # 24 hours

    # Find user by email
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update verification status
    user.is_verified = True
    await db.flush()
    await db.refresh(user)

    return user


async def request_password_reset(
    db: AsyncSession,
    email: str,
) -> None:
    """Request password reset and send reset email.

    Args:
        db: Database session
        email: User email address

    Note:
        Always returns success to prevent email enumeration
    """
    # Check if user exists
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # Only send email if user exists
    if user:
        reset_token = generate_password_reset_token(email)
        send_password_reset_email.delay(email, reset_token)

    # Always return success (prevent email enumeration)


async def reset_password(
    db: AsyncSession,
    token: str,
    new_password: str,
) -> None:
    """Reset user password with reset token.

    Args:
        db: Database session
        token: Password reset token
        new_password: New plain text password

    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Verify token and extract email
    email = verify_password_reset_token(token, max_age=3600)  # 1 hour

    # Find user by email
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update password
    user.hashed_password = get_password_hash(new_password)
    await db.flush()

    # Revoke all refresh tokens for security
    await revoke_all_user_tokens(str(user.id))


async def apple_sign_in(
    db: AsyncSession,
    identity_token: str,
) -> TokenResponse:
    """Sign in with Apple identity token.

    Args:
        db: Database session
        identity_token: Apple identity token (JWT)

    Returns:
        TokenResponse with access and refresh tokens

    Raises:
        HTTPException: If token is invalid
    """
    # Verify Apple token
    apple_data = await verify_apple_token(identity_token)
    apple_id = apple_data["sub"]
    email = apple_data.get("email")  # May be None with "Hide My Email"

    # Find or create user by auth_provider_id (stable identifier)
    result = await db.execute(
        select(User).where(
            User.auth_provider == "apple",
            User.auth_provider_id == apple_id,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        # Create new user
        if not email:
            # If email is hidden, generate a placeholder
            email = f"apple_{apple_id}@privaterelay.appleid.com"

        user = User(
            email=email,
            auth_provider="apple",
            auth_provider_id=apple_id,
            is_active=True,
            is_verified=True,  # Trust Apple verification
            hashed_password=None,  # OAuth user has no password
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Create tokens
    access_token = create_access_token(
        data={"user_id": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = await create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


async def google_sign_in(
    db: AsyncSession,
    id_token: str,
) -> TokenResponse:
    """Sign in with Google ID token.

    Args:
        db: Database session
        id_token: Google ID token (JWT)

    Returns:
        TokenResponse with access and refresh tokens

    Raises:
        HTTPException: If token is invalid
    """
    # Verify Google token
    google_data = await verify_google_token(id_token)
    google_id = google_data["sub"]
    email = google_data["email"]

    # Find or create user by auth_provider_id
    result = await db.execute(
        select(User).where(
            User.auth_provider == "google",
            User.auth_provider_id == google_id,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        # Create new user
        user = User(
            email=email,
            auth_provider="google",
            auth_provider_id=google_id,
            is_active=True,
            is_verified=True,  # Trust Google verification
            hashed_password=None,  # OAuth user has no password
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Create tokens
    access_token = create_access_token(
        data={"user_id": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = await create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


async def logout_user(
    user_id: str,
    refresh_token: str,
) -> None:
    """Logout user by revoking refresh token.

    Args:
        user_id: User ID
        refresh_token: Refresh token to revoke
    """
    await revoke_refresh_token(user_id, refresh_token)
