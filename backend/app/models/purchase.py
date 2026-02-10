"""Purchase model for tracking in-app purchase transactions."""

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class PurchaseType(str, enum.Enum):
    """Purchase type enum."""

    CONSUMABLE = "consumable"
    NON_CONSUMABLE = "non_consumable"


class Purchase(Base):
    """Purchase transaction record.

    Tracks all in-app purchases processed through RevenueCat, including
    consumable items (HD exports) and non-consumable items (premium styles).

    Attributes:
        id: UUID primary key
        user_id: FK to users table
        product_id: RevenueCat product identifier (e.g., "hd_export", "premium_styles")
        transaction_id: Store transaction ID (unique for deduplication)
        purchase_type: Type of purchase (consumable or non_consumable)
        amount: Purchase amount
        currency: Three-letter currency code (default EUR)
        revenuecat_event_id: RevenueCat webhook event ID (nullable for manual entries)
        created_at: Transaction timestamp
    """

    __tablename__ = "purchases"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    transaction_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    purchase_type: Mapped[PurchaseType] = mapped_column(String(50), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    revenuecat_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="purchases")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Purchase {self.id} ({self.product_id}, {self.amount} {self.currency})>"
