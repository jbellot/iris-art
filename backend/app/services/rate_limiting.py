"""Rate limiting service for AI generation quotas."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = logging.getLogger(__name__)


class RateLimitService:
    """Service for managing monthly AI generation rate limits."""

    @staticmethod
    def _get_current_month() -> str:
        """Get current month in YYYY-MM format."""
        return datetime.utcnow().strftime("%Y-%m")

    @staticmethod
    def _get_reset_date() -> datetime:
        """Get first day of next month (reset date)."""
        now = datetime.utcnow()
        if now.month == 12:
            return datetime(now.year + 1, 1, 1)
        return datetime(now.year, now.month + 1, 1)

    @staticmethod
    async def check_rate_limit(
        db: AsyncSession,
        user: User,
        limit: int = 3,
    ) -> Tuple[bool, int, int]:
        """Check if user is within rate limit for AI generations.

        Args:
            db: Database session
            user: User instance
            limit: Monthly generation limit for free users (default 3)

        Returns:
            Tuple of (is_allowed, current_count, limit)
        """
        # Premium users have no limits
        if user.is_premium:
            return (True, 0, 0)

        current_month = RateLimitService._get_current_month()

        # Reset count if month has changed
        if user.last_reset_month != current_month:
            user.monthly_ai_count = 0
            user.last_reset_month = current_month
            await db.commit()
            logger.info(f"Reset monthly AI count for user {user.id} (new month: {current_month})")

        # Check if within limit
        is_allowed = user.monthly_ai_count < limit
        return (is_allowed, user.monthly_ai_count, limit)

    @staticmethod
    async def increment_usage(db: AsyncSession, user: User) -> int:
        """Increment user's monthly AI generation count.

        Args:
            db: Database session
            user: User instance

        Returns:
            New count value
        """
        current_month = RateLimitService._get_current_month()

        # Reset if month changed
        if user.last_reset_month != current_month:
            user.monthly_ai_count = 0
            user.last_reset_month = current_month

        # Increment count
        user.monthly_ai_count += 1
        await db.commit()

        logger.info(f"Incremented AI count for user {user.id}: {user.monthly_ai_count}")
        return user.monthly_ai_count

    @staticmethod
    async def get_status(db: AsyncSession, user: User, limit: int = 3) -> Dict:
        """Get rate limit status for user.

        Args:
            db: Database session
            user: User instance
            limit: Monthly generation limit for free users (default 3)

        Returns:
            Dictionary with current_usage, limit, reset_date, is_premium
        """
        is_allowed, current_usage, user_limit = await RateLimitService.check_rate_limit(
            db, user, limit
        )

        reset_date = RateLimitService._get_reset_date()

        return {
            "current_usage": current_usage if not user.is_premium else 0,
            "limit": limit if not user.is_premium else 0,
            "reset_date": reset_date.isoformat(),
            "is_premium": user.is_premium,
        }
