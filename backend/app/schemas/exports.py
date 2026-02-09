"""Pydantic schemas for HD export endpoints."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class HDExportRequest(BaseModel):
    """Request to export styled/AI/processed image in HD."""

    source_type: str = Field(..., description="Source type: styled, ai_generated, or processed")
    source_job_id: UUID = Field(..., description="Source job ID (StyleJob or ProcessingJob)")


class ExportJobResponse(BaseModel):
    """HD export job status response."""

    id: UUID
    status: str
    progress: int = Field(ge=0, le=100)
    current_step: Optional[str] = None
    is_paid: bool
    result_url: Optional[str] = None  # Presigned URL (only if completed)
    result_width: Optional[int] = None
    result_height: Optional[int] = None
    file_size_bytes: Optional[int] = None
    processing_time_ms: Optional[int] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        """Pydantic config."""
        from_attributes = True


class ExportJobListResponse(BaseModel):
    """List of export jobs with pagination."""

    items: list[ExportJobResponse]
    total: int
