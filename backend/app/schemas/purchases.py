"""Purchase-related Pydantic schemas."""

from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel


class PurchaseResponse(BaseModel):
    """Response schema for purchase records."""

    id: UUID
    user_id: UUID
    product_id: str
    transaction_id: str
    purchase_type: str
    amount: float
    currency: str
    created_at: datetime

    model_config = {"from_attributes": True}


class HDExportPurchaseRequest(BaseModel):
    """Request schema for HD export purchase verification."""

    export_job_id: UUID


class RateLimitStatusResponse(BaseModel):
    """Response schema for rate limit status."""

    current_usage: int
    limit: int
    reset_date: str
    is_premium: bool


class SubscriberStatusResponse(BaseModel):
    """Response schema for RevenueCat subscriber status."""

    is_premium: bool
    entitlements: List[str]
    has_active_subscription: bool
