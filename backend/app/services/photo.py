"""Photo service for managing photo uploads and metadata."""

import uuid
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.photo import Photo
from app.schemas.photo import PhotoRead
from app.storage.s3 import s3_client


async def create_photo_upload(
    db: AsyncSession, user_id: uuid.UUID, content_type: str = "image/jpeg"
) -> tuple[str, uuid.UUID, str]:
    """Create photo record and generate presigned upload URL.

    Args:
        db: Database session
        user_id: User UUID
        content_type: MIME type (default: image/jpeg)

    Returns:
        Tuple of (presigned_url, photo_id, s3_key)
    """
    # Generate photo ID and S3 key
    photo_id = uuid.uuid4()
    file_extension = "jpg" if content_type == "image/jpeg" else "png"
    s3_key = f"iris/{user_id}/{photo_id}.{file_extension}"

    # Create photo record with pending status
    photo = Photo(
        id=photo_id,
        user_id=user_id,
        s3_key=s3_key,
        content_type=content_type,
        upload_status="pending",
    )
    db.add(photo)
    await db.commit()
    await db.refresh(photo)

    # Generate presigned PUT URL (1 hour expiry)
    presigned_url = s3_client.generate_presigned_put_url(
        s3_key, content_type=content_type, expiry=3600
    )

    return presigned_url, photo_id, s3_key


async def confirm_photo_upload(
    db: AsyncSession,
    user_id: uuid.UUID,
    photo_id: uuid.UUID,
    file_size: int,
    width: int,
    height: int,
) -> Optional[Photo]:
    """Confirm photo upload and update metadata.

    Args:
        db: Database session
        user_id: User UUID (for authorization)
        photo_id: Photo UUID
        file_size: File size in bytes
        width: Image width
        height: Image height

    Returns:
        Updated photo or None if not found
    """
    stmt = select(Photo).where(Photo.id == photo_id, Photo.user_id == user_id)
    result = await db.execute(stmt)
    photo = result.scalar_one_or_none()

    if not photo:
        return None

    # Update photo metadata
    photo.upload_status = "uploaded"
    photo.file_size = file_size
    photo.width = width
    photo.height = height

    await db.commit()
    await db.refresh(photo)

    return photo


async def list_user_photos(
    db: AsyncSession, user_id: uuid.UUID, page: int = 1, page_size: int = 20
) -> tuple[List[Photo], int]:
    """List user's photos with pagination.

    Args:
        db: Database session
        user_id: User UUID
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Tuple of (photos, total_count)
    """
    # Get total count
    count_stmt = select(func.count()).select_from(Photo).where(Photo.user_id == user_id)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Get paginated photos ordered by created_at DESC
    offset = (page - 1) * page_size
    stmt = (
        select(Photo)
        .where(Photo.user_id == user_id)
        .order_by(Photo.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    photos = list(result.scalars().all())

    return photos, total


async def get_photo(
    db: AsyncSession, user_id: uuid.UUID, photo_id: uuid.UUID
) -> Optional[Photo]:
    """Get single photo by ID.

    Args:
        db: Database session
        user_id: User UUID (for authorization)
        photo_id: Photo UUID

    Returns:
        Photo or None if not found
    """
    stmt = select(Photo).where(Photo.id == photo_id, Photo.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def delete_photo(
    db: AsyncSession, user_id: uuid.UUID, photo_id: uuid.UUID
) -> bool:
    """Delete photo from database and S3.

    Args:
        db: Database session
        user_id: User UUID (for authorization)
        photo_id: Photo UUID

    Returns:
        True if deleted, False if not found
    """
    photo = await get_photo(db, user_id, photo_id)
    if not photo:
        return False

    # Delete from S3
    s3_client.delete_file(photo.s3_key)
    if photo.thumbnail_s3_key:
        s3_client.delete_file(photo.thumbnail_s3_key)

    # Delete from database
    await db.delete(photo)
    await db.commit()

    return True


def generate_photo_read_with_urls(photo: Photo, url_expiry: int = 3600) -> PhotoRead:
    """Generate PhotoRead schema with presigned URLs.

    Args:
        photo: Photo model instance
        url_expiry: URL expiry time in seconds

    Returns:
        PhotoRead schema with presigned URLs
    """
    # Generate presigned GET URLs
    original_url = s3_client.generate_presigned_url(photo.s3_key, expiry=url_expiry)
    thumbnail_url = None
    if photo.thumbnail_s3_key:
        thumbnail_url = s3_client.generate_presigned_url(
            photo.thumbnail_s3_key, expiry=url_expiry
        )

    return PhotoRead(
        id=photo.id,
        user_id=photo.user_id,
        s3_key=photo.s3_key,
        thumbnail_url=thumbnail_url,
        original_url=original_url,
        width=photo.width,
        height=photo.height,
        file_size=photo.file_size,
        upload_status=photo.upload_status,
        created_at=photo.created_at,
    )
