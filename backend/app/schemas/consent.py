"""Consent schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ConsentRequestCreate(BaseModel):
    """Schema for requesting consent for artwork usage."""

    artwork_ids: List[UUID] = Field(..., min_length=1, max_length=10)
    purpose: str = Field(..., pattern="^(fusion|composition)$")
    circle_id: Optional[UUID] = None

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, v: str) -> str:
        """Validate purpose is either fusion or composition."""
        if v not in ["fusion", "composition"]:
            raise ValueError("Purpose must be 'fusion' or 'composition'")
        return v


class ConsentResponse(BaseModel):
    """Schema for consent response."""

    id: UUID
    artwork_id: UUID
    grantor_user_id: UUID
    grantee_user_id: UUID
    purpose: str
    status: str
    requested_at: datetime
    decided_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ConsentDecision(BaseModel):
    """Schema for granting or denying consent."""

    status: str = Field(..., pattern="^(granted|denied)$")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is either granted or denied."""
        if v not in ["granted", "denied"]:
            raise ValueError("Status must be 'granted' or 'denied'")
        return v


class PendingConsentResponse(BaseModel):
    """Schema for pending consent requests requiring action."""

    id: UUID
    artwork_id: UUID
    artwork_preview_url: str
    grantee_email: str
    purpose: str
    circle_name: Optional[str] = None
    requested_at: datetime

    model_config = {"from_attributes": True}


class ConsentStatusResponse(BaseModel):
    """Schema for consent status check response."""

    artwork_id: UUID
    status: str  # "self", "granted", "pending", "denied", "none"
