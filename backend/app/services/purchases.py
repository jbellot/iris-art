"""Purchase service for RevenueCat integration."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.export_job import ExportJob, ExportJobStatus
from app.models.purchase import Purchase, PurchaseType
from app.models.user import User

logger = logging.getLogger(__name__)


async def verify_subscriber_status(revenuecat_user_id: str) -> Dict[str, Any]:
    """Verify subscriber status via RevenueCat REST API.

    Args:
        revenuecat_user_id: RevenueCat user identifier (app_user_id)

    Returns:
        Dictionary containing subscriber data from RevenueCat API

    Raises:
        httpx.HTTPStatusError: If API request fails
    """
    if not settings.REVENUECAT_API_KEY:
        logger.warning("REVENUECAT_API_KEY not configured, returning empty subscriber data")
        return {"subscriber": {"entitlements": {}}}

    url = f"https://api.revenuecat.com/v1/subscribers/{revenuecat_user_id}"
    headers = {
        "Authorization": f"Bearer {settings.REVENUECAT_API_KEY}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()


async def check_entitlement(db: AsyncSession, user_id: UUID, entitlement_id: str) -> bool:
    """Check if user has an active entitlement.

    Args:
        db: Database session
        user_id: User UUID
        entitlement_id: Entitlement identifier (e.g., "pro")

    Returns:
        True if user has active entitlement, False otherwise
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    # If user is premium in database, return True without API call
    if user.is_premium:
        return True

    # Otherwise check RevenueCat API
    try:
        revenuecat_user_id = str(user_id)
        subscriber_data = await verify_subscriber_status(revenuecat_user_id)
        entitlements = subscriber_data.get("subscriber", {}).get("entitlements", {})
        entitlement = entitlements.get(entitlement_id, {})
        return entitlement.get("expires_date") is None or entitlement.get("expires_date") > datetime.utcnow().isoformat()
    except Exception as e:
        logger.error(f"Error checking entitlement for user {user_id}: {e}")
        return False


async def handle_consumable_purchase(
    db: AsyncSession,
    user_id: UUID,
    event: Dict[str, Any],
    subscriber_data: Dict[str, Any],
) -> None:
    """Handle consumable purchase (HD export).

    Args:
        db: Database session
        user_id: User UUID
        event: RevenueCat webhook event data
        subscriber_data: Subscriber data from RevenueCat API
    """
    # Extract transaction data
    product_id = event.get("product_id", "hd_export")
    transaction_id = event.get("id", "")
    amount = event.get("price", 4.99)
    currency = event.get("currency", "EUR")
    revenuecat_event_id = event.get("id")

    # Check if purchase already recorded (idempotency)
    result = await db.execute(
        select(Purchase).filter(Purchase.transaction_id == transaction_id)
    )
    existing_purchase = result.scalar_one_or_none()

    if existing_purchase:
        logger.info(f"Purchase {transaction_id} already recorded, skipping")
        return

    # Record purchase
    purchase = Purchase(
        user_id=user_id,
        product_id=product_id,
        transaction_id=transaction_id,
        purchase_type=PurchaseType.CONSUMABLE,
        amount=amount,
        currency=currency,
        revenuecat_event_id=revenuecat_event_id,
    )
    db.add(purchase)

    # Find most recent unpaid export job for this user
    result = await db.execute(
        select(ExportJob)
        .filter(
            ExportJob.user_id == user_id,
            ExportJob.is_paid == False,
            ExportJob.status.in_([ExportJobStatus.PENDING, ExportJobStatus.PROCESSING]),
        )
        .order_by(ExportJob.created_at.desc())
    )
    export_job = result.scalar_one_or_none()

    if export_job:
        export_job.is_paid = True
        logger.info(f"Marked export job {export_job.id} as paid")

    await db.commit()
    logger.info(f"Recorded consumable purchase {purchase.id} for user {user_id}")


async def handle_non_consumable_purchase(
    db: AsyncSession,
    user_id: UUID,
    event: Dict[str, Any],
    subscriber_data: Dict[str, Any],
) -> None:
    """Handle non-consumable purchase (premium styles unlock).

    Args:
        db: Database session
        user_id: User UUID
        event: RevenueCat webhook event data
        subscriber_data: Subscriber data from RevenueCat API
    """
    # Extract transaction data
    product_id = event.get("product_id", "premium_styles")
    transaction_id = event.get("id", "")
    amount = event.get("price", 0.0)
    currency = event.get("currency", "EUR")
    revenuecat_event_id = event.get("id")

    # Check if purchase already recorded (idempotency)
    result = await db.execute(
        select(Purchase).filter(Purchase.transaction_id == transaction_id)
    )
    existing_purchase = result.scalar_one_or_none()

    if existing_purchase:
        logger.info(f"Purchase {transaction_id} already recorded, skipping")
        return

    # Record purchase
    purchase = Purchase(
        user_id=user_id,
        product_id=product_id,
        transaction_id=transaction_id,
        purchase_type=PurchaseType.NON_CONSUMABLE,
        amount=amount,
        currency=currency,
        revenuecat_event_id=revenuecat_event_id,
    )
    db.add(purchase)

    # Update user premium status
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if user:
        user.is_premium = True
        logger.info(f"Set user {user_id} to premium status")

    await db.commit()
    logger.info(f"Recorded non-consumable purchase {purchase.id} for user {user_id}")


async def handle_purchase_event(
    db: AsyncSession,
    event_type: str,
    app_user_id: str,
    event: Dict[str, Any],
    subscriber_data: Dict[str, Any],
) -> None:
    """Route webhook event to appropriate handler.

    Args:
        db: Database session
        event_type: RevenueCat event type
        app_user_id: RevenueCat app user ID
        event: Full webhook event payload
        subscriber_data: Subscriber data from RevenueCat API
    """
    try:
        user_id = UUID(app_user_id)
    except ValueError:
        logger.error(f"Invalid user ID format: {app_user_id}")
        return

    # Handle different event types
    if event_type == "NON_RENEWING_PURCHASE":
        # Consumable HD export purchase
        await handle_consumable_purchase(db, user_id, event, subscriber_data)
    elif event_type == "INITIAL_PURCHASE":
        # Non-consumable premium styles purchase
        await handle_non_consumable_purchase(db, user_id, event, subscriber_data)
    elif event_type == "EXPIRATION":
        # Handle subscription expiration (if applicable)
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_premium = False
            await db.commit()
            logger.info(f"Removed premium status for user {user_id} due to expiration")
    else:
        logger.info(f"Unhandled event type: {event_type}")
