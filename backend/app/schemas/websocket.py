"""WebSocket message schemas for real-time progress updates."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ProgressMessage(BaseModel):
    """Real-time progress update message.

    Sent periodically during processing to keep client informed.
    """

    job_id: str = Field(..., description="Processing job ID")
    status: Literal["pending", "processing", "completed", "failed"] = Field(
        ..., description="Current job status"
    )
    progress: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    step: str = Field(..., description="User-facing step name (magical, non-technical)")
    timestamp: datetime = Field(..., description="Update timestamp (ISO 8601)")


class CompletionMessage(ProgressMessage):
    """Job completion message with final results.

    Sent once when processing completes successfully.
    """

    result_url: str = Field(..., description="Presigned URL for enhanced result image")
    processing_time_ms: int = Field(..., description="Total processing time in milliseconds")
    result_width: int = Field(..., description="Enhanced image width in pixels")
    result_height: int = Field(..., description="Enhanced image height in pixels")


class ErrorMessage(ProgressMessage):
    """Job failure message with classified error.

    Sent once when processing fails permanently.
    """

    error_type: Literal["quality_issue", "transient_error", "server_error"] = Field(
        ..., description="Error classification for user action guidance"
    )
    message: str = Field(..., description="User-friendly error message")
    suggestion: Optional[str] = Field(None, description="Actionable suggestion for user")
