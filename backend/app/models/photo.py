"""Photo model for iris image storage and metadata."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Photo(Base):
    """Photo model for storing iris image metadata."""

    __tablename__ = "photos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # S3 storage keys
    s3_key: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    thumbnail_s3_key: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # File metadata
    original_filename: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    content_type: Mapped[str] = mapped_column(String, default="image/jpeg", nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Image dimensions
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Upload status tracking
    upload_status: Mapped[str] = mapped_column(String, default="pending", nullable=False)

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
    user: Mapped["User"] = relationship("User", back_populates="photos")

    def __repr__(self) -> str:
        return f"<Photo(id={self.id}, user_id={self.user_id}, status={self.upload_status})>"
