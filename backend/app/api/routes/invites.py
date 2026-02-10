"""Invite API routes for circle invitations."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.db import get_session
from app.core.security import redis_client
from app.models.user import User
from app.schemas.circles import (
    CircleResponse,
    InviteAcceptRequest,
    InviteCreateResponse,
    InviteInfoResponse,
)
from app.services import circle_service, invite_service

router = APIRouter(prefix="/api/v1/circles", tags=["invites"])


@router.post(
    "/{circle_id}/invite",
    response_model=InviteCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invite(
    circle_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Generate an invite link for a circle.

    Rate limited to 5 invites per circle per hour.
    """
    # Verify user is an active member
    await circle_service.verify_active_membership(circle_id, current_user.id, db)

    # Check rate limit (5 per circle per hour)
    rate_key = f"invite_rate:{circle_id}:{current_user.id}"
    count = await redis_client.get(rate_key)

    if count and int(count) >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 5 invites per hour per circle.",
        )

    # Generate token
    token = await invite_service.generate_invite_token(circle_id, current_user.id)

    # Increment rate limit counter
    if not count:
        await redis_client.setex(rate_key, 3600, "1")  # 1 hour TTL
    else:
        await redis_client.incr(rate_key)

    # Build invite URL (this would be the mobile deep link in production)
    invite_url = f"irisvue://invite/{token}"

    return InviteCreateResponse(
        invite_url=invite_url,
        token=token,
        expires_in_days=invite_service.INVITE_EXPIRES_DAYS,
    )


@router.get("/invites/{token}/info", response_model=InviteInfoResponse)
async def get_invite_info(
    token: str,
    db: AsyncSession = Depends(get_session),
):
    """Get invite preview info without accepting."""
    return await invite_service.get_invite_info(token, db)


@router.post("/invites/accept", response_model=CircleResponse)
async def accept_invite(
    request: InviteAcceptRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Accept an invite and join a circle."""
    circle_info = await invite_service.accept_invite(
        request.token, current_user.id, db
    )

    # Get user's role (should be "member" for new joins)
    circles = await circle_service.get_user_circles(current_user.id, db)
    circle_detail = next((c for c in circles if c["id"] == circle_info["id"]), None)

    if circle_detail:
        return CircleResponse(**circle_detail)

    # Fallback
    return CircleResponse(
        id=circle_info["id"],
        name=circle_info["name"],
        role="member",
        member_count=circle_info["member_count"],
        created_at=None,  # Not available from accept_invite return
    )
