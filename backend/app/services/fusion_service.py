"""Fusion service for creating and managing fusion/composition artworks."""

import uuid
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.fusion_artwork import FusionArtwork
from app.models.photo import Photo
from app.models.processing_job import ProcessingJob
from app.models.style_job import StyleJob
from app.schemas.fusion import ConsentRequiredResponse, FusionResponse, FusionStatusResponse
from app.services.consent_service import check_all_consents_granted
from app.storage.s3 import S3Client
from app.workers.celery_app import celery_app


async def submit_fusion(
    artwork_ids: List[uuid.UUID],
    creator_id: uuid.UUID,
    circle_id: Optional[uuid.UUID],
    blend_mode: str,
    db: AsyncSession,
) -> Dict:
    """Submit a fusion artwork creation request.

    Args:
        artwork_ids: List of 2-4 photo IDs to fuse
        creator_id: User creating the fusion
        circle_id: Optional circle context
        blend_mode: "poisson" or "alpha"
        db: Database session

    Returns:
        Dict with fusion response or consent_required status

    Raises:
        HTTPException: If validation fails
    """
    # Validate artwork count
    if len(artwork_ids) < 2 or len(artwork_ids) > 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fusion requires 2-4 artworks"
        )

    # Validate all artworks exist and are processed
    for artwork_id in artwork_ids:
        result = await db.execute(
            select(Photo).where(Photo.id == artwork_id)
        )
        photo = result.scalar_one_or_none()

        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artwork {artwork_id} not found"
            )

        # Check if photo has been processed (has at least one completed processing job or style job)
        processing_result = await db.execute(
            select(ProcessingJob)
            .where(
                ProcessingJob.photo_id == artwork_id,
                ProcessingJob.status == "completed"
            )
            .limit(1)
        )
        has_processing = processing_result.scalar_one_or_none() is not None

        style_result = await db.execute(
            select(StyleJob)
            .where(
                StyleJob.photo_id == artwork_id,
                StyleJob.status == "completed"
            )
            .limit(1)
        )
        has_style = style_result.scalar_one_or_none() is not None

        if not has_processing and not has_style:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Artwork {artwork_id} has not been processed yet"
            )

    # Check consent for fusion
    all_granted = await check_all_consents_granted(
        artwork_ids, creator_id, "fusion", db
    )

    if not all_granted:
        # Find which artworks need consent
        pending = []
        for artwork_id in artwork_ids:
            result = await db.execute(
                select(Photo).where(Photo.id == artwork_id)
            )
            photo = result.scalar_one_or_none()

            # Skip self-owned artworks
            if photo and photo.user_id != creator_id:
                pending.append(artwork_id)

        return {
            "status": "consent_required",
            "pending": pending,
            "message": "Consent required for one or more artworks"
        }

    # Create fusion artwork record
    fusion = FusionArtwork(
        creator_id=creator_id,
        circle_id=circle_id,
        source_artwork_ids=[str(aid) for aid in artwork_ids],
        fusion_type="fusion",
        blend_mode=blend_mode,
        status="pending",
    )
    db.add(fusion)
    await db.commit()
    await db.refresh(fusion)

    # Submit Celery task
    celery_app.send_task(
        "app.workers.tasks.fusion_blending.create_fusion_artwork",
        args=[str(fusion.id), [str(aid) for aid in artwork_ids], blend_mode],
        task_id=str(fusion.id),
    )

    return {
        "status": "success",
        "fusion": FusionResponse(
            id=fusion.id,
            creator_id=fusion.creator_id,
            fusion_type=fusion.fusion_type,
            blend_mode=fusion.blend_mode,
            status=fusion.status,
            result_url=None,
            thumbnail_url=None,
            source_artwork_ids=fusion.source_artwork_ids,
            created_at=fusion.created_at,
            completed_at=fusion.completed_at,
            websocket_url=f"/ws/jobs/{fusion.id}",
        )
    }


async def submit_composition(
    artwork_ids: List[uuid.UUID],
    creator_id: uuid.UUID,
    circle_id: Optional[uuid.UUID],
    layout: str,
    db: AsyncSession,
) -> Dict:
    """Submit a composition artwork creation request.

    Args:
        artwork_ids: List of 2-4 photo IDs to compose
        creator_id: User creating the composition
        circle_id: Optional circle context
        layout: "horizontal", "vertical", or "grid_2x2"
        db: Database session

    Returns:
        Dict with fusion response or consent_required status

    Raises:
        HTTPException: If validation fails
    """
    # Validate artwork count
    if len(artwork_ids) < 2 or len(artwork_ids) > 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Composition requires 2-4 artworks"
        )

    # Validate all artworks exist and are processed
    for artwork_id in artwork_ids:
        result = await db.execute(
            select(Photo).where(Photo.id == artwork_id)
        )
        photo = result.scalar_one_or_none()

        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artwork {artwork_id} not found"
            )

        # Check if photo has been processed
        processing_result = await db.execute(
            select(ProcessingJob)
            .where(
                ProcessingJob.photo_id == artwork_id,
                ProcessingJob.status == "completed"
            )
            .limit(1)
        )
        has_processing = processing_result.scalar_one_or_none() is not None

        style_result = await db.execute(
            select(StyleJob)
            .where(
                StyleJob.photo_id == artwork_id,
                StyleJob.status == "completed"
            )
            .limit(1)
        )
        has_style = style_result.scalar_one_or_none() is not None

        if not has_processing and not has_style:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Artwork {artwork_id} has not been processed yet"
            )

    # Check consent for composition
    all_granted = await check_all_consents_granted(
        artwork_ids, creator_id, "composition", db
    )

    if not all_granted:
        # Find which artworks need consent
        pending = []
        for artwork_id in artwork_ids:
            result = await db.execute(
                select(Photo).where(Photo.id == artwork_id)
            )
            photo = result.scalar_one_or_none()

            # Skip self-owned artworks
            if photo and photo.user_id != creator_id:
                pending.append(artwork_id)

        return {
            "status": "consent_required",
            "pending": pending,
            "message": "Consent required for one or more artworks"
        }

    # Create fusion artwork record (type=composition)
    fusion = FusionArtwork(
        creator_id=creator_id,
        circle_id=circle_id,
        source_artwork_ids=[str(aid) for aid in artwork_ids],
        fusion_type="composition",
        blend_mode=layout,  # Store layout in blend_mode field
        status="pending",
    )
    db.add(fusion)
    await db.commit()
    await db.refresh(fusion)

    # Submit Celery task
    celery_app.send_task(
        "app.workers.tasks.composition.create_composition",
        args=[str(fusion.id), [str(aid) for aid in artwork_ids], layout],
        task_id=str(fusion.id),
    )

    return {
        "status": "success",
        "fusion": FusionResponse(
            id=fusion.id,
            creator_id=fusion.creator_id,
            fusion_type=fusion.fusion_type,
            blend_mode=fusion.blend_mode,
            status=fusion.status,
            result_url=None,
            thumbnail_url=None,
            source_artwork_ids=fusion.source_artwork_ids,
            created_at=fusion.created_at,
            completed_at=fusion.completed_at,
            websocket_url=f"/ws/jobs/{fusion.id}",
        )
    }


async def get_fusion_status(
    fusion_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> FusionStatusResponse:
    """Get fusion/composition status.

    Args:
        fusion_id: Fusion ID
        user_id: User ID (for authorization)
        db: Database session

    Returns:
        Fusion status response with presigned URLs

    Raises:
        HTTPException: If fusion not found or access denied
    """
    result = await db.execute(
        select(FusionArtwork).where(FusionArtwork.id == fusion_id)
    )
    fusion = result.scalar_one_or_none()

    if not fusion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fusion not found"
        )

    # Check authorization (creator or circle member)
    # For MVP, only check creator
    if fusion.creator_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Generate presigned URLs if completed
    s3_client = S3Client()
    result_url = None
    thumbnail_url = None

    if fusion.status == "completed" and fusion.result_s3_key:
        result_url = s3_client.generate_presigned_url(fusion.result_s3_key, expiry=3600)
        if fusion.thumbnail_s3_key:
            thumbnail_url = s3_client.generate_presigned_url(fusion.thumbnail_s3_key, expiry=3600)

    # Calculate progress from status
    progress_map = {
        "pending": 0,
        "processing": 50,
        "completed": 100,
        "failed": 0,
    }
    progress = progress_map.get(fusion.status, 0)

    return FusionStatusResponse(
        id=fusion.id,
        status=fusion.status,
        progress=progress,
        current_step=fusion.status,
        result_url=result_url,
        thumbnail_url=thumbnail_url,
        error_message=fusion.error_message,
        processing_time_ms=fusion.processing_time_ms,
    )


async def get_user_fusions(
    user_id: uuid.UUID, db: AsyncSession, offset: int = 0, limit: int = 20
) -> List[FusionResponse]:
    """Get list of user's fusions/compositions.

    Args:
        user_id: User ID
        db: Database session
        offset: Pagination offset
        limit: Pagination limit

    Returns:
        List of fusion responses with presigned URLs
    """
    result = await db.execute(
        select(FusionArtwork)
        .where(FusionArtwork.creator_id == user_id)
        .order_by(FusionArtwork.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    fusions = result.scalars().all()

    # Generate presigned URLs
    s3_client = S3Client()
    responses = []

    for fusion in fusions:
        result_url = None
        thumbnail_url = None

        if fusion.status == "completed" and fusion.result_s3_key:
            result_url = s3_client.generate_presigned_url(fusion.result_s3_key, expiry=3600)
            if fusion.thumbnail_s3_key:
                thumbnail_url = s3_client.generate_presigned_url(fusion.thumbnail_s3_key, expiry=3600)

        responses.append(
            FusionResponse(
                id=fusion.id,
                creator_id=fusion.creator_id,
                fusion_type=fusion.fusion_type,
                blend_mode=fusion.blend_mode,
                status=fusion.status,
                result_url=result_url,
                thumbnail_url=thumbnail_url,
                source_artwork_ids=fusion.source_artwork_ids,
                created_at=fusion.created_at,
                completed_at=fusion.completed_at,
                websocket_url=f"/ws/jobs/{fusion.id}",
            )
        )

    return responses
