"""Purchase-related API endpoints."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_session
from app.models.user import User
from app.schemas.purchases import RateLimitStatusResponse, SubscriberStatusResponse
from app.services.purchases import verify_subscriber_status
from app.services.rate_limiting import RateLimitService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/rate-limit-status", response_model=RateLimitStatusResponse)
async def get_rate_limit_status(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> RateLimitStatusResponse:
    """Get current rate limit status for authenticated user.

    Returns monthly AI generation quota information including:
    - Current usage count
    - Monthly limit (3 for free users, 0 for premium)
    - Reset date (first day of next month)
    - Premium status

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        Rate limit status
    """
    status = await RateLimitService.get_status(db, user, limit=3)

    return RateLimitStatusResponse(
        current_usage=status["current_usage"],
        limit=status["limit"],
        reset_date=status["reset_date"],
        is_premium=status["is_premium"],
    )


@router.get("/subscriber-status", response_model=SubscriberStatusResponse)
async def get_subscriber_status(
    user: User = Depends(get_current_active_user),
) -> SubscriberStatusResponse:
    """Get RevenueCat subscriber status for authenticated user.

    Queries RevenueCat API to get current entitlements and subscription status.

    Args:
        user: Current authenticated user

    Returns:
        Subscriber status with entitlements
    """
    try:
        revenuecat_user_id = str(user.id)
        subscriber_data = await verify_subscriber_status(revenuecat_user_id)

        entitlements = subscriber_data.get("subscriber", {}).get("entitlements", {})
        active_entitlements = [
            ent_id for ent_id, ent_data in entitlements.items()
            if ent_data.get("expires_date") is None or ent_data.get("expires_date") > "now"
        ]

        has_active_subscription = bool(
            subscriber_data.get("subscriber", {}).get("subscriptions", {})
        )

        return SubscriberStatusResponse(
            is_premium=user.is_premium,
            entitlements=active_entitlements,
            has_active_subscription=has_active_subscription,
        )

    except Exception as e:
        logger.error(f"Error fetching subscriber status: {e}")
        # Return user's database state if API call fails
        return SubscriberStatusResponse(
            is_premium=user.is_premium,
            entitlements=[],
            has_active_subscription=False,
        )
