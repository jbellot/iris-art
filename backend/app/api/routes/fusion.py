"""Fusion and composition API routes."""

from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_session
from app.models.user import User
from app.schemas.fusion import (
    CompositionCreateRequest,
    ConsentRequiredResponse,
    FusionCreateRequest,
    FusionResponse,
    FusionStatusResponse,
)
from app.services.fusion_service import (
    get_fusion_status,
    get_user_fusions,
    submit_composition,
    submit_fusion,
)

router = APIRouter(prefix="/api/v1", tags=["fusion"])


@router.post("/fusion", response_model=FusionResponse | ConsentRequiredResponse, status_code=status.HTTP_201_CREATED)
async def create_fusion(
    request: FusionCreateRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Create a fusion artwork using Poisson blending.

    Args:
        request: Fusion creation request
        db: Database session
        current_user: Authenticated user

    Returns:
        FusionResponse or ConsentRequiredResponse

    Raises:
        HTTPException: If validation fails
    """
    result = await submit_fusion(
        artwork_ids=request.artwork_ids,
        creator_id=current_user.id,
        circle_id=request.circle_id,
        blend_mode=request.blend_mode,
        db=db,
    )

    if result["status"] == "consent_required":
        return ConsentRequiredResponse(
            status="consent_required",
            pending=result["pending"],
            message=result["message"],
        )

    return result["fusion"]


@router.post("/composition", response_model=FusionResponse | ConsentRequiredResponse, status_code=status.HTTP_201_CREATED)
async def create_composition(
    request: CompositionCreateRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Create a composition artwork using side-by-side layout.

    Args:
        request: Composition creation request
        db: Database session
        current_user: Authenticated user

    Returns:
        FusionResponse or ConsentRequiredResponse

    Raises:
        HTTPException: If validation fails
    """
    result = await submit_composition(
        artwork_ids=request.artwork_ids,
        creator_id=current_user.id,
        circle_id=request.circle_id,
        layout=request.layout,
        db=db,
    )

    if result["status"] == "consent_required":
        return ConsentRequiredResponse(
            status="consent_required",
            pending=result["pending"],
            message=result["message"],
        )

    return result["fusion"]


@router.get("/fusion/{fusion_id}", response_model=FusionStatusResponse)
async def get_fusion(
    fusion_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> FusionStatusResponse:
    """Get fusion/composition status.

    Args:
        fusion_id: Fusion ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Fusion status with presigned URLs

    Raises:
        HTTPException: If fusion not found or access denied
    """
    return await get_fusion_status(fusion_id, current_user.id, db)


@router.get("/fusion", response_model=List[FusionResponse])
async def list_fusions(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> List[FusionResponse]:
    """List user's fusions and compositions.

    Args:
        db: Database session
        current_user: Authenticated user
        offset: Pagination offset
        limit: Pagination limit

    Returns:
        List of fusion responses
    """
    return await get_user_fusions(current_user.id, db, offset, limit)


@router.get("/circles/{circle_id}/fusions", response_model=List[FusionResponse])
async def list_circle_fusions(
    circle_id: UUID,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> List[FusionResponse]:
    """List fusions created in a circle context.

    Note: For MVP, this returns the same as list_fusions.
    Future enhancement: filter by circle_id and check membership.

    Args:
        circle_id: Circle ID
        db: Database session
        current_user: Authenticated user
        offset: Pagination offset
        limit: Pagination limit

    Returns:
        List of fusion responses
    """
    # MVP: Just return user's fusions
    # TODO: Filter by circle_id and verify membership
    return await get_user_fusions(current_user.id, db, offset, limit)
