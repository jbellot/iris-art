"""User management API endpoints."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_session
from app.models.user import User
from app.schemas.privacy import AccountDeletionRequest, AccountDeletionResponse
from app.schemas.user import UserRead
from app.services.user import delete_user_account
from app.storage.s3 import s3_client

logger = logging.getLogger(__name__)

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


@router.delete("/me", response_model=AccountDeletionResponse)
async def delete_current_user_account(
    deletion_request: AccountDeletionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> AccountDeletionResponse:
    """Delete current user account and all associated data (GDPR Article 17).

    This implements the "Right to be Forgotten" by removing:
    - All S3 objects (iris images, generated art, exports)
    - All refresh tokens from Redis
    - All consent records from database
    - User record from database

    Request body:
    - confirm: Must be true (safety check against accidental deletion)

    Returns:
        Deletion confirmation with timestamp

    Requires:
        Authentication
    """
    # Safety check: require explicit confirmation
    if not deletion_request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Account deletion requires {"confirm": true} in request body',
        )

    deleted_at = datetime.now(timezone.utc)

    # Delete account and all data
    await delete_user_account(
        db=db,
        user_id=current_user.id,
        s3_client=s3_client,
    )

    logger.info(f"Account deleted via API: user_id={current_user.id}")

    return AccountDeletionResponse(
        message="Account and all associated data have been permanently deleted",
        deleted_at=deleted_at,
    )
