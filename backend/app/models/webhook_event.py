"""WebhookEvent model for tracking webhook event processing and idempotency."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class WebhookEvent(Base):
    """Webhook event record for idempotency.

    Tracks all webhook events received from external services (e.g., RevenueCat)
    to ensure each event is processed exactly once, even if webhooks are retried.

    Attributes:
        id: UUID primary key
        event_id: External event ID (unique constraint for idempotency)
        event_type: Event type string (e.g., "INITIAL_PURCHASE", "RENEWAL")
        app_user_id: Application user identifier from webhook
        payload: Full webhook payload JSON
        processed_at: Timestamp when event was successfully processed
        created_at: Timestamp when event was first received
    """

    __tablename__ = "webhook_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    event_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    app_user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    processed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        """String representation."""
        return f"<WebhookEvent {self.event_id} ({self.event_type})>"
