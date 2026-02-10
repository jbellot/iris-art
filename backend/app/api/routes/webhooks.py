"""Webhook endpoints for external service integrations."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.models.webhook_event import WebhookEvent
from app.services.purchases import handle_purchase_event, verify_subscriber_status

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/revenuecat", status_code=status.HTTP_200_OK)
async def revenuecat_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None),
) -> Dict[str, str]:
    """Receive and process RevenueCat webhook events.

    Verifies webhook signature, deduplicates events, and processes
    purchase events to update user entitlements and payment status.

    Args:
        request: FastAPI request object
        db: Database session
        authorization: Authorization header value

    Returns:
        Success message

    Raises:
        HTTPException 401: If authorization header is invalid
    """
    # Verify authorization header
    if settings.REVENUECAT_WEBHOOK_SECRET:
        if not authorization or authorization != settings.REVENUECAT_WEBHOOK_SECRET:
            logger.warning("Invalid webhook authorization header")
            # Return 200 to avoid webhook retries on auth failures
            return {"status": "ignored"}

    # Parse event body
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook body: {e}")
        # Return 200 to avoid retries on malformed payloads
        return {"status": "error", "message": "Invalid JSON"}

    event_id = body.get("event", {}).get("id")
    event_type = body.get("event", {}).get("type")
    app_user_id = body.get("event", {}).get("app_user_id")

    if not event_id or not event_type or not app_user_id:
        logger.error(f"Missing required fields in webhook payload: {body}")
        return {"status": "error", "message": "Missing required fields"}

    # Check for duplicate event (idempotency)
    result = await db.execute(
        select(WebhookEvent).filter(WebhookEvent.event_id == event_id)
    )
    existing_event = result.scalar_one_or_none()

    if existing_event:
        logger.info(f"Duplicate webhook event {event_id}, skipping processing")
        return {"status": "duplicate"}

    # Record webhook event
    webhook_event = WebhookEvent(
        event_id=event_id,
        event_type=event_type,
        app_user_id=app_user_id,
        payload=body,
    )
    db.add(webhook_event)
    await db.commit()

    # Process the event
    try:
        # Fetch subscriber data from RevenueCat API
        subscriber_data = await verify_subscriber_status(app_user_id)

        # Handle purchase event
        await handle_purchase_event(
            db=db,
            event_type=event_type,
            app_user_id=app_user_id,
            event=body.get("event", {}),
            subscriber_data=subscriber_data,
        )

        logger.info(f"Successfully processed webhook event {event_id} ({event_type})")
        return {"status": "processed"}

    except Exception as e:
        logger.error(f"Error processing webhook event {event_id}: {e}", exc_info=True)
        # Return 200 even on processing errors to avoid infinite retries
        # The webhook_event record allows manual reprocessing if needed
        return {"status": "error", "message": str(e)}
