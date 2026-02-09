"""FusionArtwork model for tracking fusion and composition results."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.circle import Circle
    from app.models.user import User


class FusionArtwork(Base):
    """FusionArtwork model for fusion and composition metadata."""

    __tablename__ = "fusion_artworks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    circle_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("circles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_artwork_ids: Mapped[list] = mapped_column(
        JSON, nullable=False, comment="List of photo UUIDs used in fusion/composition"
    )
    fusion_type: Mapped[str] = mapped_column(
        String, nullable=False, comment="fusion or composition"
    )
    blend_mode: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        comment="poisson/alpha for fusion, horizontal/vertical/grid_2x2 for composition",
    )
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    result_s3_key: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    thumbnail_s3_key: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="fusion_artworks")
    circle: Mapped[Optional["Circle"]] = relationship("Circle", foreign_keys=[circle_id])

    def __repr__(self) -> str:
        return f"<FusionArtwork(id={self.id}, type={self.fusion_type}, status={self.status})>"
