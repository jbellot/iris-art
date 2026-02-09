"""Processing job schemas for API requests and responses."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class JobSubmitRequest(BaseModel):
    """Request to submit a photo for processing."""

    photo_id: UUID


class BatchJobSubmitRequest(BaseModel):
    """Request to submit multiple photos for batch processing."""

    photo_ids: List[UUID] = Field(..., max_length=10, description="Maximum 10 photos per batch")


class JobResponse(BaseModel):
    """Response for newly submitted job."""

    job_id: UUID
    status: str
    current_step: Optional[str] = None
    progress: int
    created_at: datetime
    websocket_url: str

    model_config = {"from_attributes": True}


class JobStatusResponse(BaseModel):
    """Full job status response with URLs and error details."""

    job_id: UUID
    status: str
    current_step: Optional[str] = None
    progress: int
    created_at: datetime
    updated_at: datetime
    websocket_url: str

    # Error details
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    suggestion: Optional[str] = None
    attempt_count: int

    # Result details
    result_url: Optional[str] = None
    original_url: Optional[str] = None
    processing_time_ms: Optional[int] = None
    result_width: Optional[int] = None
    result_height: Optional[int] = None
    quality_score: Optional[float] = None

    model_config = {"from_attributes": True}


class BatchJobResponse(BaseModel):
    """Response for batch job submission."""

    jobs: List[JobResponse]
