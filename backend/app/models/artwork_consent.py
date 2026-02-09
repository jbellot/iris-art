"""ArtworkConsent model for per-artwork permission tracking."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.circle import Circle
    from app.models.photo import Photo
    from app.models.user import User


class ArtworkConsent(Base):
    """ArtworkConsent model for tracking per-artwork, per-grantee, per-purpose consent."""

    __tablename__ = "artwork_consents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    artwork_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("photos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    grantor_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    grantee_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    circle_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("circles.id", ondelete="CASCADE"),
        nullable=True,
    )
    purpose: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    artwork: Mapped["Photo"] = relationship("Photo", foreign_keys=[artwork_id])
    grantor: Mapped["User"] = relationship("User", foreign_keys=[grantor_user_id])
    grantee: Mapped["User"] = relationship("User", foreign_keys=[grantee_user_id])
    circle: Mapped[Optional["Circle"]] = relationship("Circle", foreign_keys=[circle_id])

    __table_args__ = (
        UniqueConstraint(
            "artwork_id",
            "grantee_user_id",
            "purpose",
            name="uq_consent_artwork_grantee_purpose",
        ),
    )

    def __repr__(self) -> str:
        return f"<ArtworkConsent(id={self.id}, artwork_id={self.artwork_id}, status={self.status})>"
