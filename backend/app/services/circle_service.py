"""Circle service for managing circles and memberships."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.circle import Circle
from app.models.circle_membership import CircleMembership
from app.models.user import User


async def create_circle(name: str, user_id: uuid.UUID, db: AsyncSession) -> Circle:
    """Create a new circle and add the creator as owner.

    Args:
        name: Circle name (1-50 characters)
        user_id: ID of the user creating the circle
        db: Database session

    Returns:
        Circle: The created circle

    Raises:
        HTTPException: If user is already in 20+ circles
    """
    # Validate user isn't in too many circles
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

    # Create circle
    circle = Circle(name=name, created_by=user_id)
    db.add(circle)
    await db.flush()

    # Add creator as owner
    membership = CircleMembership(
        circle_id=circle.id,
        user_id=user_id,
        role="owner"
    )
    db.add(membership)
    await db.commit()
    await db.refresh(circle)

    return circle


async def get_user_circles(user_id: uuid.UUID, db: AsyncSession) -> List[dict]:
    """Get all circles where user is an active member.

    Args:
        user_id: ID of the user
        db: Database session

    Returns:
        List of circle dicts with role and member_count
    """
    result = await db.execute(
        select(Circle, CircleMembership.role)
        .join(CircleMembership, Circle.id == CircleMembership.circle_id)
        .where(
            and_(
                CircleMembership.user_id == user_id,
                CircleMembership.left_at.is_(None)
            )
        )
        .order_by(Circle.created_at.desc())
    )

    circles = []
    for circle, role in result:
        # Count active members
        member_count = await db.scalar(
            select(func.count(CircleMembership.id))
            .where(
                and_(
                    CircleMembership.circle_id == circle.id,
                    CircleMembership.left_at.is_(None)
                )
            )
        )

        circles.append({
            "id": circle.id,
            "name": circle.name,
            "role": role,
            "member_count": member_count or 0,
            "created_at": circle.created_at
        })

    return circles


async def get_circle_detail(
    circle_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> dict:
    """Get circle detail with members list.

    Args:
        circle_id: ID of the circle
        user_id: ID of the user requesting
        db: Database session

    Returns:
        Circle detail dict with members list

    Raises:
        HTTPException: If user is not an active member or circle not found
    """
    # Verify membership
    membership = await verify_active_membership(circle_id, user_id, db)

    # Get circle with memberships
    result = await db.execute(
        select(Circle)
        .options(selectinload(Circle.memberships))
        .where(Circle.id == circle_id)
    )
    circle = result.scalar_one_or_none()

    if not circle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Circle not found"
        )

    # Get active members with user details
    members_result = await db.execute(
        select(CircleMembership, User.email)
        .join(User, CircleMembership.user_id == User.id)
        .where(
            and_(
                CircleMembership.circle_id == circle_id,
                CircleMembership.left_at.is_(None)
            )
        )
        .order_by(CircleMembership.joined_at)
    )

    members = [
        {
            "user_id": mem.user_id,
            "email": email,
            "role": mem.role,
            "joined_at": mem.joined_at
        }
        for mem, email in members_result
    ]

    return {
        "id": circle.id,
        "name": circle.name,
        "role": membership.role,
        "member_count": len(members),
        "created_at": circle.created_at,
        "members": members
    }


async def get_circle_members(
    circle_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> List[dict]:
    """Get active members of a circle.

    Args:
        circle_id: ID of the circle
        user_id: ID of the user requesting
        db: Database session

    Returns:
        List of member dicts

    Raises:
        HTTPException: If user is not an active member
    """
    # Verify membership
    await verify_active_membership(circle_id, user_id, db)

    # Get active members with user details
    result = await db.execute(
        select(CircleMembership, User.email)
        .join(User, CircleMembership.user_id == User.id)
        .where(
            and_(
                CircleMembership.circle_id == circle_id,
                CircleMembership.left_at.is_(None)
            )
        )
        .order_by(CircleMembership.joined_at)
    )

    return [
        {
            "user_id": mem.user_id,
            "email": email,
            "role": mem.role,
            "joined_at": mem.joined_at
        }
        for mem, email in result
    ]


async def leave_circle(
    circle_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> None:
    """Leave a circle (soft delete membership).

    If owner is leaving and other members exist, transfers ownership to oldest member.
    If owner is leaving and no other members exist, hard deletes the circle.

    Args:
        circle_id: ID of the circle
        user_id: ID of the user leaving
        db: Database session

    Raises:
        HTTPException: If user is not an active member
    """
    # Get user's membership
    membership = await verify_active_membership(circle_id, user_id, db)

    if membership.role == "owner":
        # Check if there are other active members
        other_members = await db.execute(
            select(CircleMembership)
            .where(
                and_(
                    CircleMembership.circle_id == circle_id,
                    CircleMembership.user_id != user_id,
                    CircleMembership.left_at.is_(None)
                )
            )
            .order_by(CircleMembership.joined_at)
            .limit(1)
        )
        next_owner = other_members.scalar_one_or_none()

        if next_owner:
            # Transfer ownership to oldest member
            next_owner.role = "owner"
            membership.left_at = datetime.now(timezone.utc)
            await db.commit()
        else:
            # No other members, delete the circle
            await db.delete(membership)
            circle = await db.get(Circle, circle_id)
            if circle:
                await db.delete(circle)
            await db.commit()
    else:
        # Regular member leaving
        membership.left_at = datetime.now(timezone.utc)
        await db.commit()


async def remove_member(
    circle_id: uuid.UUID,
    owner_id: uuid.UUID,
    target_user_id: uuid.UUID,
    db: AsyncSession
) -> None:
    """Remove a member from a circle (owner only).

    Args:
        circle_id: ID of the circle
        owner_id: ID of the owner removing the member
        target_user_id: ID of the user to remove
        db: Database session

    Raises:
        HTTPException: If requester is not owner, or trying to remove self
    """
    # Verify requester is owner
    owner_membership = await verify_active_membership(circle_id, owner_id, db)
    if owner_membership.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only circle owners can remove members"
        )

    # Cannot remove self
    if target_user_id == owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use leave endpoint to leave the circle"
        )

    # Get target membership
    target_membership = await verify_active_membership(circle_id, target_user_id, db)

    # Soft delete
    target_membership.left_at = datetime.now(timezone.utc)
    await db.commit()


async def verify_active_membership(
    circle_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> CircleMembership:
    """Verify user is an active member of a circle.

    Args:
        circle_id: ID of the circle
        user_id: ID of the user
        db: Database session

    Returns:
        CircleMembership: The active membership

    Raises:
        HTTPException: If user is not an active member
    """
    result = await db.execute(
        select(CircleMembership)
        .where(
            and_(
                CircleMembership.circle_id == circle_id,
                CircleMembership.user_id == user_id,
                CircleMembership.left_at.is_(None)
            )
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this circle"
        )

    return membership
