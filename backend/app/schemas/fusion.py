"""Fusion and composition schemas for API requests and responses."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class FusionCreateRequest(BaseModel):
    """Request to create a fusion artwork."""

    artwork_ids: List[UUID] = Field(..., min_length=2, max_length=4)
    circle_id: Optional[UUID] = None
    blend_mode: str = Field(default="poisson", description="poisson or alpha")

    @field_validator("blend_mode")
    @classmethod
    def validate_blend_mode(cls, v: str) -> str:
        if v not in ["poisson", "alpha"]:
            raise ValueError("blend_mode must be 'poisson' or 'alpha'")
        return v


class CompositionCreateRequest(BaseModel):
    """Request to create a composition artwork."""

    artwork_ids: List[UUID] = Field(..., min_length=2, max_length=4)
    circle_id: Optional[UUID] = None
    layout: str = Field(default="horizontal", description="horizontal, vertical, or grid_2x2")

    @field_validator("layout")
    @classmethod
    def validate_layout(cls, v: str) -> str:
        if v not in ["horizontal", "vertical", "grid_2x2"]:
            raise ValueError("layout must be 'horizontal', 'vertical', or 'grid_2x2'")
        return v


class FusionResponse(BaseModel):
    """Response for fusion/composition creation."""

    id: UUID
    creator_id: UUID
    fusion_type: str
    blend_mode: Optional[str]
    status: str
    result_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    source_artwork_ids: List[str]
    created_at: datetime
    completed_at: Optional[datetime] = None
    websocket_url: str

    model_config = {"from_attributes": True}


class FusionStatusResponse(BaseModel):
    """Fusion/composition status response."""

    id: UUID
    status: str
    progress: int = Field(default=0, ge=0, le=100)
    current_step: Optional[str] = None
    result_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None

    model_config = {"from_attributes": True}


class ConsentRequiredResponse(BaseModel):
    """Response when consent is required before fusion/composition."""

    status: str = "consent_required"
    pending: List[UUID] = Field(..., description="List of artwork_ids requiring consent")
    message: str = "Consent required for one or more artworks"
