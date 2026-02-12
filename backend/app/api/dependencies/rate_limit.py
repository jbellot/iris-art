"""Rate limiting dependencies for FastAPI endpoints."""

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_session
from app.models.user import User
from app.services.rate_limiting import RateLimitService


async def check_ai_generation_limit(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> User:
    """Check if user is within AI generation rate limit.

    Premium users always pass through.
    Free users are limited to 3 generations per month.

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        User instance if allowed

    Raises:
        HTTPException 429: If rate limit exceeded
    """
    # Premium users bypass rate limiting
    if user.is_premium:
        return user

    # Check rate limit for free users
    is_allowed, current_usage, limit = await RateLimitService.check_rate_limit(db, user, limit=3)

    if not is_allowed:
        reset_date = RateLimitService._get_reset_date()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": f"You've reached your monthly limit of {limit} AI generations. Upgrade to premium for unlimited access.",
                "current_usage": current_usage,
                "limit": limit,
                "reset_date": reset_date.isoformat(),
                "upgrade_available": True,
            },
        )

    return user
