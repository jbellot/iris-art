"""Invite service for generating and validating circle invite tokens."""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import redis_client
from app.models.circle import Circle
from app.models.circle_membership import CircleMembership
from app.models.user import User

# Token serializer for invite links
invite_serializer = URLSafeTimedSerializer(
    settings.SECRET_KEY, salt="circle-invite"
)

# Token expiry
INVITE_MAX_AGE = 604800  # 7 days in seconds
INVITE_EXPIRES_DAYS = 7


async def generate_invite_token(circle_id: uuid.UUID, inviter_id: uuid.UUID) -> str:
    """Generate an invite token for a circle.

    Args:
        circle_id: ID of the circle
        inviter_id: ID of the user creating the invite

    Returns:
        str: Serialized invite token
    """
    payload = {
        "circle_id": str(circle_id),
        "inviter_id": str(inviter_id)
    }
    return invite_serializer.dumps(payload)


async def validate_invite_token(token: str) -> dict:
    """Validate an invite token and return payload.

    Args:
        token: Invite token string

    Returns:
        dict: Payload with circle_id and inviter_id

    Raises:
        ValueError: If token is invalid or expired
    """
    try:
        payload = invite_serializer.loads(token, max_age=INVITE_MAX_AGE)

        # Check if token has been used
        used = await redis_client.get(f"used_invite:{token}")
        if used:
            raise ValueError("This invite link has already been used")

        return payload
    except SignatureExpired:
        raise ValueError("This invite link has expired")
    except BadSignature:
        raise ValueError("Invalid invite link")


async def mark_token_used(token: str) -> None:
    """Mark an invite token as used in Redis.

    Args:
        token: Invite token to mark as used
    """
    # Store with 30-day TTL (longer than token validity for safety)
    await redis_client.setex(f"used_invite:{token}", 2592000, "1")


async def accept_invite(
    token: str, user_id: uuid.UUID, db: AsyncSession
) -> dict:
    """Accept an invite and join a circle.

    Args:
        token: Invite token
        user_id: ID of the user accepting
        db: Database session

    Returns:
        dict: Circle info

    Raises:
        HTTPException: If validation fails or circle is full
    """
    # Validate token
    try:
        payload = await validate_invite_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    circle_id = uuid.UUID(payload["circle_id"])

    # Check circle exists
    circle = await db.get(Circle, circle_id)
    if not circle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Circle not found"
        )

    # Check if user is already a member
    existing = await db.execute(
        select(CircleMembership)
        .where(
            and_(
                CircleMembership.circle_id == circle_id,
                CircleMembership.user_id == user_id
            )
        )
    )
    existing_membership = existing.scalar_one_or_none()

    if existing_membership:
        if existing_membership.left_at is None:
            # Already an active member
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already a member of this circle"
            )
        else:
            # Check if they were removed by owner (vs self-leave)
            # If removed by owner, check if membership was deleted within a reasonable timeframe
            # For simplicity, we'll allow rejoining if they left themselves
            # but block if explicitly removed (which we'll infer from the presence of the record)
            # In a more complex system, we'd track who caused the left_at update
            # For MVP, allow rejoining after leaving
            existing_membership.left_at = None
            existing_membership.joined_at = datetime.now(timezone.utc)
            await db.commit()
            await mark_token_used(token)

            return {
                "id": circle.id,
                "name": circle.name,
                "member_count": await _get_member_count(circle_id, db)
            }

    # Check circle member limit
    member_count = await _get_member_count(circle_id, db)
    if member_count >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Circle is full (maximum 10 members)"
        )

    # Check user isn't in too many circles
    user_circle_count = await db.scalar(
        select(func.count(CircleMembership.id))
        .where(
            and_(
                CircleMembership.user_id == user_id,
                CircleMembership.left_at.is_(None)
            )
        )
    )

    if user_circle_count and user_circle_count >= 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can only be a member of 20 circles at a time"
        )

    # Create membership
    membership = CircleMembership(
        circle_id=circle_id,
        user_id=user_id,
        role="member"
    )
    db.add(membership)
    await db.commit()

    # Mark token as used
    await mark_token_used(token)

    return {
        "id": circle.id,
        "name": circle.name,
        "member_count": member_count + 1
    }


async def get_invite_info(token: str, db: AsyncSession) -> dict:
    """Get invite preview info without joining.

    Args:
        token: Invite token
        db: Database session

    Returns:
        dict: Circle and inviter info

    Raises:
        HTTPException: If token is invalid
    """
    # Validate token
    try:
        payload = await validate_invite_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    circle_id = uuid.UUID(payload["circle_id"])
    inviter_id = uuid.UUID(payload["inviter_id"])

    # Get circle
    circle = await db.get(Circle, circle_id)
    if not circle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Circle not found"
        )

    # Get inviter
    inviter = await db.get(User, inviter_id)
    inviter_email = inviter.email if inviter else "Unknown"

    return {
        "circle_id": circle.id,
        "circle_name": circle.name,
        "inviter_email": inviter_email
    }


async def _get_member_count(circle_id: uuid.UUID, db: AsyncSession) -> int:
    """Get count of active members in a circle.

    Args:
        circle_id: ID of the circle
        db: Database session

    Returns:
        int: Number of active members
    """
    count = await db.scalar(
        select(func.count(CircleMembership.id))
        .where(
            and_(
                CircleMembership.circle_id == circle_id,
                CircleMembership.left_at.is_(None)
            )
        )
    )
    return count or 0
