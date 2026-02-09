"""StyleJob model for tracking style transfer requests."""

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class StyleJobStatus(str, enum.Enum):
    """Status enum for style transfer jobs."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class StyleJob(Base):
    """Style transfer job tracking.

    Each job applies a style preset to a processed iris photo,
    generating low-res preview and full-res result.

    Attributes:
        id: UUID primary key
        user_id: FK to users table
        photo_id: FK to photos table (source photo)
        processing_job_id: FK to processing_jobs (if applying to processed iris, else NULL)
        style_preset_id: FK to style_presets
        status: Job status (pending, processing, completed, failed)
        progress: Progress percentage (0-100)
        current_step: Current processing step (user-facing)
        celery_task_id: Celery task ID for tracking
        preview_s3_key: S3 key for low-res preview (256x256 JPEG)
        result_s3_key: S3 key for full-res result (1024x1024 JPEG)
        result_width: Result image width in pixels
        result_height: Result image height in pixels
        processing_time_ms: Total processing time in milliseconds
        error_type: Error classification (quality_issue, transient_error, server_error)
        error_message: User-facing error message
        created_at: Job creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "style_jobs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    photo_id: Mapped[UUID] = mapped_column(ForeignKey("photos.id"), nullable=False, index=True)
    processing_job_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("processing_jobs.id"), nullable=True, index=True
    )
    style_preset_id: Mapped[UUID | None] = mapped_column(ForeignKey("style_presets.id"), nullable=True, index=True)
    status: Mapped[StyleJobStatus] = mapped_column(Enum(StyleJobStatus), nullable=False, default=StyleJobStatus.PENDING)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_step: Mapped[str] = mapped_column(String(100), nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preview_s3_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result_s3_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="style_jobs")
    photo: Mapped["Photo"] = relationship("Photo", back_populates="style_jobs")
    style_preset: Mapped["StylePreset | None"] = relationship("StylePreset")
    processing_job: Mapped["ProcessingJob"] = relationship("ProcessingJob", back_populates="style_jobs")

    def __repr__(self) -> str:
        """String representation."""
        return f"<StyleJob {self.id} ({self.status.value})>"
