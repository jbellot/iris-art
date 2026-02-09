"""API routes for artistic style transfer."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_session
from app.models.processing_job import ProcessingJob
from app.models.user import User
from app.schemas.styles import (
    StyleJobListResponse,
    StyleJobResponse,
    StyleJobSubmitRequest,
    StyleListResponse,
    StylePresetResponse,
)
from app.services.styles import (
    create_style_job,
    generate_job_response_with_urls,
    get_style_job,
    list_presets,
    list_style_jobs,
)
from app.storage.s3 import s3_client
from app.workers.tasks.ai_generation import generate_ai_art
from app.workers.tasks.style_transfer import apply_style_preset

router = APIRouter(prefix="/api/v1/styles", tags=["styles"])


@router.get("/presets", response_model=StyleListResponse)
async def get_style_presets(
    db: Annotated[AsyncSession, Depends(get_session)],
) -> StyleListResponse:
    """List all active style presets grouped by tier.

    Public endpoint - no authentication required for browsing styles.

    Returns:
        StyleListResponse with free and premium presets
    """
    presets = await list_presets(db, active_only=True)

    # Generate presigned URLs for thumbnails
    free_responses = []
    for preset in presets["free"]:
        thumbnail_url = None
        if preset.thumbnail_s3_key:
            thumbnail_url = s3_client.generate_presigned_url(preset.thumbnail_s3_key, expiration=3600)

        free_responses.append(
            StylePresetResponse(
                id=preset.id,
                name=preset.name,
                display_name=preset.display_name,
                description=preset.description,
                category=preset.category.value,
                tier=preset.tier.value,
                thumbnail_url=thumbnail_url,
                sort_order=preset.sort_order,
            )
        )

    premium_responses = []
    for preset in presets["premium"]:
        thumbnail_url = None
        if preset.thumbnail_s3_key:
            thumbnail_url = s3_client.generate_presigned_url(preset.thumbnail_s3_key, expiration=3600)

        premium_responses.append(
            StylePresetResponse(
                id=preset.id,
                name=preset.name,
                display_name=preset.display_name,
                description=preset.description,
                category=preset.category.value,
                tier=preset.tier.value,
                thumbnail_url=thumbnail_url,
                sort_order=preset.sort_order,
            )
        )

    return StyleListResponse(free=free_responses, premium=premium_responses)


@router.post("/apply", response_model=StyleJobResponse, status_code=status.HTTP_201_CREATED)
async def apply_style(
    request: StyleJobSubmitRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> StyleJobResponse:
    """Submit a style transfer job.

    Applies an artistic style preset to a photo (original or processed iris).

    Args:
        request: Style job submission request
        db: Database session
        current_user: Authenticated user

    Returns:
        StyleJobResponse with job details and WebSocket URL

    Raises:
        HTTPException: If photo, processing job, or preset not found
    """
    try:
        # Create style job
        job = await create_style_job(
            db,
            current_user.id,
            request.photo_id,
            request.style_preset_id,
            request.processing_job_id,
        )

        # Determine source image S3 key
        # If processing_job_id provided, use processed result; otherwise use original photo
        if request.processing_job_id:
            from sqlalchemy import select

            result = await db.execute(
                select(ProcessingJob).where(ProcessingJob.id == request.processing_job_id)
            )
            processing_job = result.scalar_one_or_none()

            if not processing_job or not processing_job.result_s3_key:
                raise ValueError("Processing job not found or not completed")

            photo_s3_key = processing_job.result_s3_key
        else:
            from sqlalchemy import select

            from app.models.photo import Photo

            result = await db.execute(select(Photo).where(Photo.id == request.photo_id))
            photo = result.scalar_one_or_none()

            if not photo:
                raise ValueError("Photo not found")

            photo_s3_key = photo.s3_key

        # Get style preset details for task
        from sqlalchemy import select

        from app.models.style_preset import StylePreset

        result = await db.execute(select(StylePreset).where(StylePreset.id == request.style_preset_id))
        preset = result.scalar_one_or_none()

        if not preset:
            raise ValueError("Style preset not found")

        # Submit to Celery with high priority
        apply_style_preset.apply_async(
            args=[
                str(job.id),
                str(current_user.id),
                photo_s3_key,
                preset.name,
                preset.model_s3_key,
            ],
            task_id=str(job.id),
            queue="high_priority",
        )

        return await generate_job_response_with_urls(db, job)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/jobs/{job_id}", response_model=StyleJobResponse)
async def get_job_status(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> StyleJobResponse:
    """Get detailed status of a style transfer job.

    Args:
        job_id: Style job ID
        db: Database session
        current_user: Authenticated user

    Returns:
        StyleJobResponse with full details and presigned URLs

    Raises:
        HTTPException: If job not found or not owned by user
    """
    job = await get_style_job(db, job_id, current_user.id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Style job not found",
        )

    return await generate_job_response_with_urls(db, job)


@router.get("/jobs", response_model=StyleJobListResponse)
async def list_jobs(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    photo_id: UUID | None = Query(None, description="Filter by photo ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> StyleJobListResponse:
    """List user's style transfer jobs (paginated).

    Args:
        db: Database session
        current_user: Authenticated user
        photo_id: Optional photo ID filter
        page: Page number (default: 1)
        page_size: Items per page (default: 20, max: 100)

    Returns:
        StyleJobListResponse with items and total count
    """
    offset = (page - 1) * page_size
    jobs, total = await list_style_jobs(
        db,
        current_user.id,
        photo_id=photo_id,
        limit=page_size,
        offset=offset,
    )

    # Generate responses with presigned URLs
    responses = []
    for job in jobs:
        response = await generate_job_response_with_urls(db, job)
        responses.append(response)

    return StyleJobListResponse(items=responses, total=total)


@router.post("/generate", response_model=StyleJobResponse, status_code=status.HTTP_201_CREATED)
async def generate_ai_art_endpoint(
    photo_id: UUID,
    processing_job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    prompt: str | None = None,
    style_hint: str | None = None,
) -> StyleJobResponse:
    """Submit AI art generation job.

    Generates a unique artistic composition from processed iris using
    Stable Diffusion SDXL Turbo with ControlNet guidance.

    Note: Reuses StyleJob model with style_preset_id=NULL to indicate AI generation.

    Args:
        photo_id: Photo ID
        processing_job_id: ProcessingJob ID (processed iris)
        db: Database session
        current_user: Authenticated user
        prompt: Optional user prompt for generation
        style_hint: Optional style hint (cosmic, abstract, watercolor, etc.)

    Returns:
        StyleJobResponse with job details and WebSocket URL

    Raises:
        HTTPException: If photo or processing job not found
    """
    from sqlalchemy import select

    from app.models.photo import Photo

    try:
        # Validate photo ownership
        result = await db.execute(
            select(Photo).where(
                Photo.id == photo_id,
                Photo.user_id == current_user.id,
            )
        )
        photo = result.scalar_one_or_none()

        if not photo:
            raise ValueError("Photo not found")

        # Validate processing job ownership
        result = await db.execute(
            select(ProcessingJob).where(
                ProcessingJob.id == processing_job_id,
                ProcessingJob.user_id == current_user.id,
            )
        )
        processing_job = result.scalar_one_or_none()

        if not processing_job or not processing_job.result_s3_key:
            raise ValueError("Processing job not found or not completed")

        # Create StyleJob with style_preset_id=NULL (indicates AI generation)
        from app.models.style_job import StyleJob

        ai_job = StyleJob(
            user_id=current_user.id,
            photo_id=photo_id,
            processing_job_id=processing_job_id,
            style_preset_id=None,  # NULL indicates AI generation
        )

        db.add(ai_job)
        await db.commit()
        await db.refresh(ai_job)

        # Submit to Celery with high priority
        generate_ai_art.apply_async(
            args=[
                str(ai_job.id),
                str(current_user.id),
                str(photo_id),
                str(processing_job_id),
                prompt,
                style_hint,
            ],
            task_id=str(ai_job.id),
            queue="high_priority",
        )

        # Update job with Celery task ID
        ai_job.celery_task_id = str(ai_job.id)
        await db.commit()
        await db.refresh(ai_job)

        return await generate_job_response_with_urls(db, ai_job)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
