"""Processing API routes for AI image processing jobs."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_session
from app.models.user import User
from app.schemas.processing import (
    BatchJobResponse,
    BatchJobSubmitRequest,
    JobResponse,
    JobStatusResponse,
    JobSubmitRequest,
)
from app.services.processing import (
    create_processing_job,
    generate_job_response_with_urls,
    get_job,
    get_user_jobs,
)
from app.workers.tasks.processing import process_iris_pipeline

router = APIRouter(prefix="/api/v1/processing", tags=["processing"])


@router.post("/submit", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def submit_processing_job(
    request: JobSubmitRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> JobResponse:
    """Submit a photo for AI processing.

    Args:
        request: Job submission request with photo_id
        db: Database session
        current_user: Authenticated user

    Returns:
        JobResponse with job_id and websocket_url

    Raises:
        HTTPException: If photo not found or not owned by user
    """
    try:
        # Create processing job
        job = await create_processing_job(db, current_user.id, request.photo_id)

        # Submit to Celery with high priority
        process_iris_pipeline.apply_async(
            args=[str(job.id), str(request.photo_id), str(current_user.id)],
            task_id=str(job.id),
            queue="high_priority",
        )

        return JobResponse(
            job_id=job.id,
            status=job.status,
            current_step=job.current_step,
            progress=job.progress,
            created_at=job.created_at,
            websocket_url=f"/ws/jobs/{job.id}",
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/batch", response_model=BatchJobResponse, status_code=status.HTTP_201_CREATED)
async def submit_batch_processing(
    request: BatchJobSubmitRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> BatchJobResponse:
    """Submit multiple photos for batch processing.

    Args:
        request: Batch submission with up to 10 photo_ids
        db: Database session
        current_user: Authenticated user

    Returns:
        BatchJobResponse with list of created jobs
    """
    jobs = []

    for idx, photo_id in enumerate(request.photo_ids):
        try:
            # Create job
            job = await create_processing_job(db, current_user.id, photo_id)

            # Submit with descending priority (first = 9, last = 0)
            priority = len(request.photo_ids) - idx - 1
            process_iris_pipeline.apply_async(
                args=[str(job.id), str(photo_id), str(current_user.id)],
                task_id=str(job.id),
                queue="high_priority",
                priority=priority,
            )

            jobs.append(
                JobResponse(
                    job_id=job.id,
                    status=job.status,
                    current_step=job.current_step,
                    progress=job.progress,
                    created_at=job.created_at,
                    websocket_url=f"/ws/jobs/{job.id}",
                )
            )

        except ValueError:
            # Skip photos that don't exist or aren't owned by user
            continue

    if not jobs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid photos found for processing",
        )

    return BatchJobResponse(jobs=jobs)


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> JobStatusResponse:
    """Get detailed status of a processing job.

    Args:
        job_id: Processing job ID
        db: Database session
        current_user: Authenticated user

    Returns:
        JobStatusResponse with full details and presigned URLs

    Raises:
        HTTPException: If job not found or not owned by user
    """
    job = await get_job(db, current_user.id, job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return await generate_job_response_with_urls(db, job)


@router.get("/jobs", response_model=list[JobStatusResponse])
async def list_processing_jobs(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> list[JobStatusResponse]:
    """List user's processing jobs (paginated).

    Args:
        db: Database session
        current_user: Authenticated user
        page: Page number (default: 1)
        page_size: Items per page (default: 20, max: 100)

    Returns:
        List of JobStatusResponse
    """
    jobs, _ = await get_user_jobs(db, current_user.id, page, page_size)

    # Generate responses with presigned URLs
    responses = []
    for job in jobs:
        response = await generate_job_response_with_urls(db, job)
        responses.append(response)

    return responses


@router.post("/jobs/{job_id}/reprocess", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def reprocess_job(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> JobResponse:
    """Reprocess a job (creates new job for same photo).

    Args:
        job_id: Original job ID
        db: Database session
        current_user: Authenticated user

    Returns:
        JobResponse for new job

    Raises:
        HTTPException: If original job not found or not owned by user
    """
    # Get original job
    original_job = await get_job(db, current_user.id, job_id)

    if not original_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original job not found",
        )

    # Create new job for same photo
    try:
        new_job = await create_processing_job(db, current_user.id, original_job.photo_id)

        # Submit to Celery
        process_iris_pipeline.apply_async(
            args=[str(new_job.id), str(original_job.photo_id), str(current_user.id)],
            task_id=str(new_job.id),
            queue="high_priority",
        )

        return JobResponse(
            job_id=new_job.id,
            status=new_job.status,
            current_step=new_job.current_step,
            progress=new_job.progress,
            created_at=new_job.created_at,
            websocket_url=f"/ws/jobs/{new_job.id}",
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
