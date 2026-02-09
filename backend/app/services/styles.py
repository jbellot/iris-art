"""Service layer for style transfer operations."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.photo import Photo
from app.models.processing_job import ProcessingJob
from app.models.style_job import StyleJob, StyleJobStatus
from app.models.style_preset import StylePreset, StyleTier
from app.schemas.styles import StyleJobResponse, StylePresetResponse
from app.storage.s3 import s3_client

logger = logging.getLogger(__name__)


async def list_presets(db: AsyncSession, active_only: bool = True) -> dict[str, list[StylePreset]]:
    """List all style presets grouped by tier.

    Args:
        db: Database session
        active_only: Only return active presets (default: True)

    Returns:
        Dictionary with 'free' and 'premium' keys containing lists of presets
    """
    query = select(StylePreset)

    if active_only:
        query = query.where(StylePreset.is_active == True)  # noqa: E712

    query = query.order_by(StylePreset.tier, StylePreset.sort_order)

    result = await db.execute(query)
    presets = result.scalars().all()

    # Group by tier
    free_presets = [p for p in presets if p.tier == StyleTier.FREE]
    premium_presets = [p for p in presets if p.tier == StyleTier.PREMIUM]

    return {"free": free_presets, "premium": premium_presets}


async def get_preset(db: AsyncSession, preset_id: UUID) -> StylePreset | None:
    """Get a single style preset by ID.

    Args:
        db: Database session
        preset_id: Preset UUID

    Returns:
        StylePreset or None if not found
    """
    result = await db.execute(select(StylePreset).where(StylePreset.id == preset_id))
    return result.scalar_one_or_none()


async def create_style_job(
    db: AsyncSession,
    user_id: UUID,
    photo_id: UUID,
    style_preset_id: UUID,
    processing_job_id: UUID | None = None,
) -> StyleJob:
    """Create a new style transfer job.

    Args:
        db: Database session
        user_id: User ID
        photo_id: Photo ID to apply style to
        style_preset_id: Style preset to apply
        processing_job_id: Optional processing job ID to use processed result

    Returns:
        Created StyleJob

    Raises:
        ValueError: If photo not found or not owned by user, or preset not found
    """
    # Verify photo exists and belongs to user
    photo_result = await db.execute(
        select(Photo).where(Photo.id == photo_id, Photo.user_id == user_id)
    )
    photo = photo_result.scalar_one_or_none()

    if not photo:
        raise ValueError("Photo not found or not owned by user")

    # Verify style preset exists
    preset = await get_preset(db, style_preset_id)
    if not preset:
        raise ValueError("Style preset not found")

    # If processing_job_id provided, verify it exists and belongs to user
    if processing_job_id:
        job_result = await db.execute(
            select(ProcessingJob).where(
                ProcessingJob.id == processing_job_id,
                ProcessingJob.user_id == user_id,
                ProcessingJob.photo_id == photo_id,
            )
        )
        processing_job = job_result.scalar_one_or_none()

        if not processing_job:
            raise ValueError("Processing job not found or not owned by user")

    # Create style job
    style_job = StyleJob(
        user_id=user_id,
        photo_id=photo_id,
        processing_job_id=processing_job_id,
        style_preset_id=style_preset_id,
        status=StyleJobStatus.PENDING,
        progress=0,
    )

    db.add(style_job)
    await db.commit()
    await db.refresh(style_job)

    return style_job


async def get_style_job(db: AsyncSession, job_id: UUID, user_id: UUID) -> StyleJob | None:
    """Get a style job by ID with verification that it belongs to the user.

    Args:
        db: Database session
        job_id: Style job ID
        user_id: User ID for ownership verification

    Returns:
        StyleJob or None if not found or not owned by user
    """
    result = await db.execute(
        select(StyleJob)
        .options(selectinload(StyleJob.style_preset))
        .where(StyleJob.id == job_id, StyleJob.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def list_style_jobs(
    db: AsyncSession,
    user_id: UUID,
    photo_id: UUID | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[StyleJob], int]:
    """List user's style jobs with optional filtering.

    Args:
        db: Database session
        user_id: User ID
        photo_id: Optional photo ID filter
        limit: Maximum number of results
        offset: Offset for pagination

    Returns:
        Tuple of (list of jobs, total count)
    """
    query = select(StyleJob).options(selectinload(StyleJob.style_preset)).where(StyleJob.user_id == user_id)

    if photo_id:
        query = query.where(StyleJob.photo_id == photo_id)

    # Get total count
    count_result = await db.execute(select(StyleJob.id).where(StyleJob.user_id == user_id))
    total = len(count_result.all())

    # Get paginated results
    query = query.order_by(StyleJob.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    jobs = result.scalars().all()

    return list(jobs), total


async def generate_job_response_with_urls(db: AsyncSession, job: StyleJob) -> StyleJobResponse:
    """Generate StyleJobResponse with presigned URLs for S3 assets.

    Args:
        db: Database session
        job: StyleJob instance

    Returns:
        StyleJobResponse with presigned URLs
    """
    # Load style preset if not already loaded
    if not job.style_preset:
        await db.refresh(job, ["style_preset"])

    # Generate presigned URLs for preview and result
    preview_url = None
    if job.preview_s3_key:
        preview_url = s3_client.generate_presigned_url(job.preview_s3_key, expiration=3600)

    result_url = None
    if job.result_s3_key:
        result_url = s3_client.generate_presigned_url(job.result_s3_key, expiration=3600)

    # Generate presigned URL for style preset thumbnail
    thumbnail_url = None
    if job.style_preset.thumbnail_s3_key:
        thumbnail_url = s3_client.generate_presigned_url(job.style_preset.thumbnail_s3_key, expiration=3600)

    preset_response = StylePresetResponse(
        id=job.style_preset.id,
        name=job.style_preset.name,
        display_name=job.style_preset.display_name,
        description=job.style_preset.description,
        category=job.style_preset.category.value,
        tier=job.style_preset.tier.value,
        thumbnail_url=thumbnail_url,
        sort_order=job.style_preset.sort_order,
    )

    return StyleJobResponse(
        id=job.id,
        status=job.status.value,
        progress=job.progress,
        current_step=job.current_step,
        preview_url=preview_url,
        result_url=result_url,
        style_preset=preset_response,
        processing_time_ms=job.processing_time_ms,
        error_type=job.error_type,
        error_message=job.error_message,
        created_at=job.created_at,
        websocket_url=f"/ws/jobs/{job.id}",
    )
