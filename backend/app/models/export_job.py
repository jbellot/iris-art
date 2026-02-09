"""ExportJob model for tracking HD export requests."""

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ExportSourceType(str, enum.Enum):
    """Source type for HD export."""

    STYLED = "styled"
    AI_GENERATED = "ai_generated"
    PROCESSED = "processed"


class ExportJobStatus(str, enum.Enum):
    """Status enum for HD export jobs."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportJob(Base):
    """HD export job tracking.

    Each job upscales a styled, AI-generated, or processed image to HD
    resolution (2048x2048) and applies watermark based on payment status.

    Attributes:
        id: UUID primary key
        user_id: FK to users table
        source_type: Type of source image (styled, ai_generated, processed)
        source_job_id: UUID of source job (StyleJob or ProcessingJob)
        source_s3_key: S3 key of source image to upscale
        status: Job status (pending, processing, completed, failed)
        progress: Progress percentage (0-100)
        current_step: Current processing step (user-facing)
        celery_task_id: Celery task ID for tracking
        is_paid: Whether user paid for watermark-free export
        result_s3_key: S3 key for HD export result
        result_width: Result image width in pixels
        result_height: Result image height in pixels
        file_size_bytes: Result file size in bytes
        processing_time_ms: Total processing time in milliseconds
        error_type: Error classification (quality_issue, transient_error, server_error)
        error_message: User-facing error message
        created_at: Job creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "export_jobs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    source_type: Mapped[ExportSourceType] = mapped_column(Enum(ExportSourceType), nullable=False)
    source_job_id: Mapped[UUID] = mapped_column(String(36), nullable=False, index=True)
    source_s3_key: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ExportJobStatus] = mapped_column(
        Enum(ExportJobStatus), nullable=False, default=ExportJobStatus.PENDING
    )
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_step: Mapped[str | None] = mapped_column(String(100), nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    result_s3_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="export_jobs")

    def __repr__(self) -> str:
        """String representation."""
        return f"<ExportJob {self.id} ({self.status.value})>"
