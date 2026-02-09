"""Circle API routes for CRUD operations."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.user import User
from app.schemas.circles import (
    CircleCreateRequest,
    CircleDetailResponse,
    CircleMemberResponse,
    CircleResponse,
    SharedGalleryItemResponse,
)
from app.services import circle_service

router = APIRouter(prefix="/circles", tags=["circles"])


@router.post("", response_model=CircleResponse, status_code=status.HTTP_201_CREATED)
async def create_circle(
    request: CircleCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Create a new circle."""
    circle = await circle_service.create_circle(request.name, current_user.id, db)

    # Get member count (should be 1 initially)
    circles = await circle_service.get_user_circles(current_user.id, db)
    circle_info = next((c for c in circles if c["id"] == circle.id), None)

    if not circle_info:
        # Fallback
        return CircleResponse(
            id=circle.id,
            name=circle.name,
            role="owner",
            member_count=1,
            created_at=circle.created_at,
        )

    return CircleResponse(**circle_info)


@router.get("", response_model=List[CircleResponse])
async def list_circles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """List all circles the user is a member of."""
    circles = await circle_service.get_user_circles(current_user.id, db)
    return [CircleResponse(**c) for c in circles]


@router.get("/{circle_id}", response_model=CircleDetailResponse)
async def get_circle(
    circle_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get circle detail with members list."""
    circle_detail = await circle_service.get_circle_detail(
        circle_id, current_user.id, db
    )
    return CircleDetailResponse(**circle_detail)


@router.get("/{circle_id}/members", response_model=List[CircleMemberResponse])
async def get_circle_members(
    circle_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get list of active members in a circle."""
    members = await circle_service.get_circle_members(circle_id, current_user.id, db)
    return [CircleMemberResponse(**m) for m in members]


@router.post("/{circle_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_circle(
    circle_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Leave a circle."""
    await circle_service.leave_circle(circle_id, current_user.id, db)


@router.delete(
    "/{circle_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_member(
    circle_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Remove a member from a circle (owner only)."""
    await circle_service.remove_member(circle_id, current_user.id, user_id, db)


@router.get("/{circle_id}/gallery", response_model=List[SharedGalleryItemResponse])
async def get_shared_gallery(
    circle_id: UUID,
    offset: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get shared gallery showing artwork from all active circle members."""
    gallery_items = await circle_service.get_shared_gallery(
        circle_id, current_user.id, db, offset, limit
    )
    return [SharedGalleryItemResponse(**item) for item in gallery_items]
