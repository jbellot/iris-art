"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.user import User
from app.schemas.auth import (
    AppleSignInRequest,
    GoogleSignInRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.schemas.user import UserRead
from app.services.auth import (
    apple_sign_in,
    google_sign_in,
    login_user,
    logout_user,
    refresh_tokens,
    register_user,
    request_password_reset,
    reset_password,
    verify_email,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_session),
) -> User:
    """Register a new user with email and password.

    Args:
        data: Registration request with email and password
        db: Database session

    Returns:
        Created user object

    Raises:
        HTTPException: If email already exists (409)
    """
    user = await register_user(db, data.email, data.password)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Login with email and password (OAuth2 compatible).

    Args:
        form_data: OAuth2 form data (username=email, password)
        db: Database session

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: If credentials are invalid (401) or user is inactive (403)
    """
    return await login_user(db, form_data.username, form_data.password)


@router.post("/login/json", response_model=TokenResponse)
async def login_json(
    data: LoginRequest,
    db: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Login with email and password (JSON body).

    Args:
        data: Login request with email and password
        db: Database session

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: If credentials are invalid (401) or user is inactive (403)
    """
    return await login_user(db, data.email, data.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
) -> TokenResponse:
    """Refresh access token using refresh token.

    Args:
        data: Refresh request with refresh token

    Returns:
        New access token and same refresh token

    Raises:
        HTTPException: If refresh token is invalid or revoked (401)
    """
    return await refresh_tokens(data.refresh_token)


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email_endpoint(
    data: VerifyEmailRequest,
    db: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Verify user email with verification token.

    Args:
        data: Verification request with token
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid or expired (401) or user not found (404)
    """
    await verify_email(db, data.token)
    return MessageResponse(message="Email verified successfully")


@router.post("/request-password-reset", response_model=MessageResponse)
async def request_password_reset_endpoint(
    data: PasswordResetRequest,
    db: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Request password reset email.

    Args:
        data: Password reset request with email
        db: Database session

    Returns:
        Success message (always returns 200 to prevent email enumeration)

    Note:
        Always returns success even if email doesn't exist to prevent email enumeration.
    """
    await request_password_reset(db, data.email)
    return MessageResponse(
        message="If the email exists, a password reset link has been sent"
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password_endpoint(
    data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Reset password with reset token.

    Args:
        data: Password reset confirmation with token and new password
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid or expired (401) or user not found (404)
    """
    await reset_password(db, data.token, data.new_password)
    return MessageResponse(message="Password reset successfully")


@router.post("/apple", response_model=TokenResponse)
async def apple_signin(
    data: AppleSignInRequest,
    db: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Sign in with Apple identity token.

    Args:
        data: Apple sign-in request with identity token
        db: Database session

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: If token is invalid (401) or user is inactive (403)
    """
    return await apple_sign_in(db, data.identity_token)


@router.post("/google", response_model=TokenResponse)
async def google_signin(
    data: GoogleSignInRequest,
    db: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Sign in with Google ID token.

    Args:
        data: Google sign-in request with ID token
        db: Database session

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: If token is invalid (401) or user is inactive (403)
    """
    return await google_sign_in(db, data.id_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: LogoutRequest,
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """Logout by revoking refresh token.

    Args:
        data: Logout request with refresh token
        current_user: Current authenticated user

    Returns:
        Success message
    """
    await logout_user(str(current_user.id), data.refresh_token)
    return MessageResponse(message="Logged out successfully")
