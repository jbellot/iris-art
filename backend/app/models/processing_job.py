"""ProcessingJob model for tracking AI image processing jobs."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ProcessingJob(Base):
    """ProcessingJob model for tracking AI processing pipeline execution."""

    __tablename__ = "processing_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    photo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("photos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Job status tracking
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    current_step: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Error handling and classification
    error_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    suggestion: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Result storage
    result_s3_key: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    mask_s3_key: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Performance and quality metrics
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    result_width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    result_height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Celery integration
    celery_task_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="processing_jobs")
    photo: Mapped["Photo"] = relationship("Photo", back_populates="processing_jobs")
    style_jobs: Mapped[List["StyleJob"]] = relationship(
        "StyleJob", back_populates="processing_job", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ProcessingJob(id={self.id}, status={self.status}, step={self.current_step})>"
