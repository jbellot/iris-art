"""Processing job service for creating and managing AI processing jobs."""

from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.photo import Photo
from app.models.processing_job import ProcessingJob
from app.schemas.processing import JobStatusResponse
from app.storage.s3 import s3_client


async def create_processing_job(
    db: AsyncSession, user_id: UUID, photo_id: UUID
) -> ProcessingJob:
    """Create a new processing job for a photo.

    Args:
        db: Database session
        user_id: User ID for authorization
        photo_id: Photo ID to process

    Returns:
        Created ProcessingJob instance

    Raises:
        ValueError: If photo doesn't exist or doesn't belong to user
    """
    # Validate photo exists and belongs to user
    result = await db.execute(
        select(Photo).where(Photo.id == photo_id, Photo.user_id == user_id)
    )
    photo = result.scalar_one_or_none()

    if not photo:
        raise ValueError("Photo not found or access denied")

    # Create job
    job = ProcessingJob(
        user_id=user_id,
        photo_id=photo_id,
        status="pending",
        progress=0,
        attempt_count=0,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    return job


async def get_job(
    db: AsyncSession, user_id: UUID, job_id: UUID
) -> Optional[ProcessingJob]:
    """Get a processing job by ID (user-scoped).

    Args:
        db: Database session
        user_id: User ID for authorization
        job_id: Job ID to retrieve

    Returns:
        ProcessingJob or None if not found/not authorized
    """
    result = await db.execute(
        select(ProcessingJob).where(
            ProcessingJob.id == job_id, ProcessingJob.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def get_jobs_for_photo(
    db: AsyncSession, user_id: UUID, photo_id: UUID
) -> list[ProcessingJob]:
    """Get all processing jobs for a specific photo.

    Args:
        db: Database session
        user_id: User ID for authorization
        photo_id: Photo ID

    Returns:
        List of ProcessingJob instances
    """
    result = await db.execute(
        select(ProcessingJob)
        .where(ProcessingJob.photo_id == photo_id, ProcessingJob.user_id == user_id)
        .order_by(ProcessingJob.created_at.desc())
    )
    return list(result.scalars().all())


async def update_job_status(
    db: AsyncSession, job_id: UUID, status: str, **kwargs
) -> None:
    """Update job status and additional fields.

    Args:
        db: Database session
        job_id: Job ID to update
        status: New status value
        **kwargs: Additional fields to update (current_step, progress, error_type, etc.)
    """
    result = await db.execute(select(ProcessingJob).where(ProcessingJob.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        return

    job.status = status
    for key, value in kwargs.items():
        if hasattr(job, key):
            setattr(job, key, value)

    await db.commit()


async def get_user_jobs(
    db: AsyncSession, user_id: UUID, page: int = 1, page_size: int = 20
) -> Tuple[list[ProcessingJob], int]:
    """Get paginated list of user's processing jobs.

    Args:
        db: Database session
        user_id: User ID
        page: Page number (1-indexed)
        page_size: Items per page

    Returns:
        Tuple of (jobs list, total count)
    """
    # Get total count
    count_result = await db.execute(
        select(func.count()).select_from(ProcessingJob).where(ProcessingJob.user_id == user_id)
    )
    total = count_result.scalar() or 0

    # Get paginated jobs
    offset = (page - 1) * page_size
    result = await db.execute(
        select(ProcessingJob)
        .where(ProcessingJob.user_id == user_id)
        .order_by(ProcessingJob.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    jobs = list(result.scalars().all())

    return jobs, total


async def generate_job_response_with_urls(
    db: AsyncSession, job: ProcessingJob
) -> JobStatusResponse:
    """Generate job status response with presigned URLs.

    Args:
        db: Database session
        job: ProcessingJob instance

    Returns:
        JobStatusResponse with presigned URLs
    """
    # Get original photo S3 key
    result = await db.execute(select(Photo).where(Photo.id == job.photo_id))
    photo = result.scalar_one_or_none()

    # Generate presigned URLs
    result_url = None
    if job.result_s3_key:
        result_url = s3_client.generate_presigned_url(job.result_s3_key, expiry=3600)

    original_url = None
    if photo and photo.s3_key:
        original_url = s3_client.generate_presigned_url(photo.s3_key, expiry=3600)

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        current_step=job.current_step,
        progress=job.progress,
        created_at=job.created_at,
        updated_at=job.updated_at,
        websocket_url=f"/ws/jobs/{job.id}",
        error_type=job.error_type,
        error_message=job.error_message,
        suggestion=job.suggestion,
        attempt_count=job.attempt_count,
        result_url=result_url,
        original_url=original_url,
        processing_time_ms=job.processing_time_ms,
        result_width=job.result_width,
        result_height=job.result_height,
        quality_score=job.quality_score,
    )
