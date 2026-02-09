"""Pydantic schemas for style transfer API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class StylePresetResponse(BaseModel):
    """Response schema for a single style preset."""

    id: UUID
    name: str
    display_name: str
    description: str
    category: str
    tier: str
    thumbnail_url: str | None = None
    sort_order: int

    model_config = {"from_attributes": True}


class StyleListResponse(BaseModel):
    """Response schema for grouped style presets."""

    free: list[StylePresetResponse]
    premium: list[StylePresetResponse]


class StyleJobSubmitRequest(BaseModel):
    """Request schema for submitting a style transfer job."""

    photo_id: UUID = Field(..., description="Photo ID to apply style to")
    style_preset_id: UUID = Field(..., description="Style preset to apply")
    processing_job_id: UUID | None = Field(
        None, description="Optional processing job ID to use processed iris result"
    )


class StyleJobResponse(BaseModel):
    """Response schema for style job status."""

    id: UUID
    status: str
    progress: int
    current_step: str | None = None
    preview_url: str | None = None
    result_url: str | None = None
    style_preset: StylePresetResponse
    processing_time_ms: int | None = None
    error_type: str | None = None
    error_message: str | None = None
    created_at: datetime
    websocket_url: str | None = None

    model_config = {"from_attributes": True}


class StyleJobListResponse(BaseModel):
    """Response schema for paginated list of style jobs."""

    items: list[StyleJobResponse]
    total: int
