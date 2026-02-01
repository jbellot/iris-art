"""Privacy compliance Pydantic schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ConsentRequirements(BaseModel):
    """Jurisdiction-specific consent requirements."""

    explicit_consent: bool
    purpose_disclosure: bool
    retention_policy: bool
    right_to_withdraw: bool
    consent_text: str
    # BIPA-specific
    no_profit_from_data: Optional[bool] = None
    retention_schedule: Optional[bool] = None
    written_consent: Optional[bool] = None
    # CCPA-specific
    notice_at_collection: Optional[bool] = None
    opt_out_right: Optional[bool] = None
    deletion_right: Optional[bool] = None
    # GDPR-specific
    data_minimization: Optional[bool] = None


class JurisdictionResponse(BaseModel):
    """Response containing jurisdiction and consent requirements."""

    jurisdiction: str = Field(..., description="Detected jurisdiction code")
    consent_requirements: ConsentRequirements


class ConsentGrantRequest(BaseModel):
    """Request to grant consent."""

    consent_type: str = Field(
        ...,
        description="Type of consent: biometric_capture, data_processing",
    )
    jurisdiction: str = Field(..., description="Jurisdiction code")
    consent_text_version: str = Field(..., description="Version of consent text shown to user")


class ConsentGrantResponse(BaseModel):
    """Response after granting consent."""

    id: UUID
    consent_type: str
    jurisdiction: str
    granted: bool
    granted_at: datetime

    class Config:
        from_attributes = True


class ConsentWithdrawRequest(BaseModel):
    """Request to withdraw consent."""

    consent_id: UUID


class ConsentListResponse(BaseModel):
    """Response containing list of user consents."""

    consents: list[ConsentGrantResponse]


class DataExportResponse(BaseModel):
    """Response for data export request."""

    message: str
    export_url: Optional[str] = None
    status: str = Field(..., description="Export status: pending, ready, expired")


class AccountDeletionRequest(BaseModel):
    """Request to delete account (requires confirmation)."""

    confirm: bool = Field(..., description="Must be true to confirm deletion")


class AccountDeletionResponse(BaseModel):
    """Response after account deletion."""

    message: str
    deleted_at: datetime
