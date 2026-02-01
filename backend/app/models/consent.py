"""Consent record model for privacy compliance."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ConsentRecord(Base):
    """Record of user consent for privacy compliance (GDPR, BIPA, CCPA)."""

    __tablename__ = "consent_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Consent details
    consent_type: Mapped[str] = mapped_column(
        String, nullable=False
    )  # biometric_capture, data_processing, marketing
    jurisdiction: Mapped[str] = mapped_column(
        String, nullable=False
    )  # gdpr, bipa, ccpa, generic
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Timestamps
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Audit trail
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    consent_text_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="consent_records")

    def __repr__(self) -> str:
        return f"<ConsentRecord(id={self.id}, user_id={self.user_id}, type={self.consent_type}, granted={self.granted})>"
