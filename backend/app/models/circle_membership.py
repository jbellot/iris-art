"""CircleMembership model for circle member relationships."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.circle import Circle
    from app.models.user import User


class CircleMembership(Base):
    """CircleMembership model for tracking circle members."""

    __tablename__ = "circle_memberships"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    circle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("circles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String, default="member", nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    left_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    circle: Mapped["Circle"] = relationship("Circle", back_populates="memberships")
    user: Mapped["User"] = relationship("User", back_populates="circle_memberships")

    __table_args__ = (UniqueConstraint("circle_id", "user_id", name="uq_circle_user"),)

    def __repr__(self) -> str:
        return f"<CircleMembership(circle_id={self.circle_id}, user_id={self.user_id}, role={self.role})>"
