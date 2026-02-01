"""User management API endpoints."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.user import UserRead

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current user profile.

    Args:
        current_user: Current authenticated and active user

    Returns:
        Current user data

    Raises:
        HTTPException: If user is not authenticated (401) or inactive (403)
    """
    return current_user


# Placeholder for DELETE /me endpoint
# Will be implemented in Plan 03 (Privacy & GDPR) with full data deletion
