"""Photo API routes for upload and gallery management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_session
from app.models.user import User
from app.schemas.photo import (
    PhotoListResponse,
    PhotoRead,
    PhotoUploadComplete,
    PresignedUploadResponse,
)
from app.services.photo import (
    confirm_photo_upload,
    create_photo_upload,
    delete_photo,
    generate_photo_read_with_urls,
    get_photo,
    list_user_photos,
)

router = APIRouter(prefix="/api/v1/photos", tags=["photos"])


@router.post("/upload", response_model=PresignedUploadResponse, status_code=status.HTTP_201_CREATED)
async def request_photo_upload(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    content_type: str = "image/jpeg",
) -> PresignedUploadResponse:
    """Request a presigned URL for direct photo upload to S3.

    The mobile app should:
    1. Call this endpoint to get a presigned PUT URL
    2. Upload the photo directly to S3 using that URL
    3. Call /photos/{photo_id}/confirm after successful upload
    """
    presigned_url, photo_id, s3_key = await create_photo_upload(
        db, current_user.id, content_type
    )

    return PresignedUploadResponse(
        upload_url=presigned_url,
        photo_id=photo_id,
        s3_key=s3_key,
    )


@router.post("/{photo_id}/confirm", response_model=PhotoRead)
async def confirm_upload(
    photo_id: UUID,
    payload: PhotoUploadComplete,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> PhotoRead:
    """Confirm that photo upload to S3 is complete and update metadata."""
    photo = await confirm_photo_upload(
        db,
        current_user.id,
        photo_id,
        payload.file_size,
        payload.width,
        payload.height,
    )

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found or access denied",
        )

    return generate_photo_read_with_urls(photo)


@router.get("", response_model=PhotoListResponse)
async def get_user_photos(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PhotoListResponse:
    """Get paginated list of user's photos."""
    photos, total = await list_user_photos(db, current_user.id, page, page_size)

    # Generate PhotoRead instances with presigned URLs
    photo_reads = [generate_photo_read_with_urls(photo) for photo in photos]

    return PhotoListResponse(
        items=photo_reads,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{photo_id}", response_model=PhotoRead)
async def get_single_photo(
    photo_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> PhotoRead:
    """Get single photo details with presigned URLs."""
    photo = await get_photo(db, current_user.id, photo_id)

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found or access denied",
        )

    return generate_photo_read_with_urls(photo)


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_photo(
    photo_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    """Delete photo from S3 and database."""
    deleted = await delete_photo(db, current_user.id, photo_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found or access denied",
        )
