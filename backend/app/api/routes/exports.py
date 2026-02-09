"""API routes for HD exports."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_session
from app.models.user import User
from app.schemas.exports import (
    ExportJobListResponse,
    ExportJobResponse,
    HDExportRequest,
)
from app.services.exports import (
    create_export_job,
    generate_export_response_with_url,
    get_export_job,
    list_export_jobs,
)
from app.workers.tasks.hd_export import export_hd_image

router = APIRouter(prefix="/api/v1/exports", tags=["exports"])


@router.post("/hd", response_model=ExportJobResponse, status_code=status.HTTP_201_CREATED)
async def request_hd_export(
    request: HDExportRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ExportJobResponse:
    """Request HD export of styled, AI-generated, or processed image.

    Creates an export job and dispatches Celery task for upscaling and watermarking.

    Args:
        request: HD export request
        db: Database session
        current_user: Authenticated user

    Returns:
        ExportJobResponse with job details

    Raises:
        HTTPException: If source job not found or not completed
    """
    try:
        # Create export job
        job = await create_export_job(
            db,
            current_user.id,
            request.source_type,
            request.source_job_id,
        )

        # Submit to Celery (default queue - not high priority)
        export_hd_image.apply_async(
            args=[
                str(job.id),
                str(current_user.id),
                job.source_s3_key,
                job.is_paid,
            ],
            task_id=str(job.id),
            queue="default",
        )

        # Update job with Celery task ID
        job.celery_task_id = str(job.id)
        await db.commit()
        await db.refresh(job)

        return await generate_export_response_with_url(db, job)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/jobs/{job_id}", response_model=ExportJobResponse)
async def get_export_job_status(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ExportJobResponse:
    """Get detailed status of an HD export job.

    Args:
        job_id: Export job ID
        db: Database session
        current_user: Authenticated user

    Returns:
        ExportJobResponse with full details and presigned URL

    Raises:
        HTTPException: If job not found or not owned by user
    """
    job = await get_export_job(db, job_id, current_user.id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export job not found",
        )

    return await generate_export_response_with_url(db, job)


@router.get("/jobs", response_model=ExportJobListResponse)
async def list_export_jobs_endpoint(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ExportJobListResponse:
    """List user's HD export jobs (paginated).

    Args:
        db: Database session
        current_user: Authenticated user
        page: Page number (default: 1)
        page_size: Items per page (default: 20, max: 100)

    Returns:
        ExportJobListResponse with items and total count
    """
    offset = (page - 1) * page_size
    jobs, total = await list_export_jobs(
        db,
        current_user.id,
        limit=page_size,
        offset=offset,
    )

    # Generate responses with presigned URLs
    responses = []
    for job in jobs:
        response = await generate_export_response_with_url(db, job)
        responses.append(response)

    return ExportJobListResponse(items=responses, total=total)
