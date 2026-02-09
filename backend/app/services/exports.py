"""Service layer for HD export management."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.export_job import ExportJob, ExportSourceType
from app.models.processing_job import ProcessingJob
from app.models.style_job import StyleJob
from app.schemas.exports import ExportJobResponse
from app.storage.s3 import s3_client

logger = logging.getLogger(__name__)


async def create_export_job(
    db: AsyncSession,
    user_id: UUID,
    source_type: str,
    source_job_id: UUID,
) -> ExportJob:
    """Create a new HD export job.

    Looks up the source image S3 key from the source job and creates
    an ExportJob record.

    Args:
        db: Database session
        user_id: User ID
        source_type: Source type (styled, ai_generated, processed)
        source_job_id: Source job ID

    Returns:
        Created ExportJob

    Raises:
        ValueError: If source job not found or not completed
    """
    # Validate source type
    try:
        source_type_enum = ExportSourceType(source_type)
    except ValueError:
        raise ValueError(f"Invalid source type: {source_type}")

    # Look up source S3 key based on source type
    source_s3_key = None

    if source_type_enum in (ExportSourceType.STYLED, ExportSourceType.AI_GENERATED):
        # Source is a StyleJob
        result = await db.execute(
            select(StyleJob).where(
                StyleJob.id == source_job_id,
                StyleJob.user_id == user_id,
            )
        )
        style_job = result.scalar_one_or_none()

        if not style_job:
            raise ValueError("Style job not found")

        if style_job.status != "completed" or not style_job.result_s3_key:
            raise ValueError("Style job not completed")

        source_s3_key = style_job.result_s3_key

    elif source_type_enum == ExportSourceType.PROCESSED:
        # Source is a ProcessingJob
        result = await db.execute(
            select(ProcessingJob).where(
                ProcessingJob.id == source_job_id,
                ProcessingJob.user_id == user_id,
            )
        )
        processing_job = result.scalar_one_or_none()

        if not processing_job:
            raise ValueError("Processing job not found")

        if processing_job.status != "completed" or not processing_job.result_s3_key:
            raise ValueError("Processing job not completed")

        source_s3_key = processing_job.result_s3_key

    if not source_s3_key:
        raise ValueError("Source image not found")

    # Create export job
    export_job = ExportJob(
        user_id=user_id,
        source_type=source_type_enum,
        source_job_id=source_job_id,
        source_s3_key=source_s3_key,
        is_paid=False,  # Default: free export with watermark
    )

    db.add(export_job)
    await db.commit()
    await db.refresh(export_job)

    logger.info(f"Created export job {export_job.id} for user {user_id}")
    return export_job


async def get_export_job(
    db: AsyncSession,
    job_id: UUID,
    user_id: UUID,
) -> ExportJob | None:
    """Get export job by ID.

    Args:
        db: Database session
        job_id: Export job ID
        user_id: User ID (for ownership check)

    Returns:
        ExportJob or None if not found
    """
    result = await db.execute(
        select(ExportJob).where(
            ExportJob.id == job_id,
            ExportJob.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def list_export_jobs(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[ExportJob], int]:
    """List user's export jobs (paginated).

    Args:
        db: Database session
        user_id: User ID
        limit: Maximum number of jobs to return
        offset: Offset for pagination

    Returns:
        Tuple of (jobs list, total count)
    """
    # Get total count
    from sqlalchemy import func

    count_result = await db.execute(
        select(func.count(ExportJob.id)).where(ExportJob.user_id == user_id)
    )
    total = count_result.scalar() or 0

    # Get paginated jobs
    result = await db.execute(
        select(ExportJob)
        .where(ExportJob.user_id == user_id)
        .order_by(ExportJob.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    jobs = list(result.scalars().all())

    return jobs, total


async def mark_as_paid(
    db: AsyncSession,
    job_id: UUID,
    user_id: UUID,
) -> ExportJob:
    """Mark export job as paid (called by payment webhook in Phase 6).

    Args:
        db: Database session
        job_id: Export job ID
        user_id: User ID

    Returns:
        Updated ExportJob

    Raises:
        ValueError: If job not found
    """
    job = await get_export_job(db, job_id, user_id)

    if not job:
        raise ValueError("Export job not found")

    job.is_paid = True
    await db.commit()
    await db.refresh(job)

    logger.info(f"Marked export job {job_id} as paid")
    return job


async def generate_export_response_with_url(
    db: AsyncSession,
    job: ExportJob,
) -> ExportJobResponse:
    """Generate ExportJobResponse with presigned result URL.

    Args:
        db: Database session
        job: ExportJob

    Returns:
        ExportJobResponse with presigned URL if completed
    """
    result_url = None

    if job.status == "completed" and job.result_s3_key:
        # Generate presigned URL (expires in 1 hour)
        result_url = s3_client.generate_presigned_url(
            job.result_s3_key,
            expiration=3600,
        )

    return ExportJobResponse(
        id=job.id,
        status=job.status.value,
        progress=job.progress,
        current_step=job.current_step,
        is_paid=job.is_paid,
        result_url=result_url,
        result_width=job.result_width,
        result_height=job.result_height,
        file_size_bytes=job.file_size_bytes,
        processing_time_ms=job.processing_time_ms,
        error_type=job.error_type,
        error_message=job.error_message,
    )
