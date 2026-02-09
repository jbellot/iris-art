"""User model for authentication and authorization."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # OAuth provider fields
    auth_provider: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    auth_provider_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    consent_records: Mapped[List["ConsentRecord"]] = relationship(
        "ConsentRecord", back_populates="user", cascade="all, delete-orphan"
    )
    consent_grants: Mapped[List["ArtworkConsent"]] = relationship(
        "ArtworkConsent",
        back_populates="grantor",
        foreign_keys="[ArtworkConsent.grantor_user_id]",
        cascade="all, delete-orphan",
    )
    consent_requests: Mapped[List["ArtworkConsent"]] = relationship(
        "ArtworkConsent",
        back_populates="grantee",
        foreign_keys="[ArtworkConsent.grantee_user_id]",
        cascade="all, delete-orphan",
    )
    photos: Mapped[List["Photo"]] = relationship(
        "Photo", back_populates="user", cascade="all, delete-orphan"
    )
    processing_jobs: Mapped[List["ProcessingJob"]] = relationship(
        "ProcessingJob", back_populates="user", cascade="all, delete-orphan"
    )
    style_jobs: Mapped[List["StyleJob"]] = relationship(
        "StyleJob", back_populates="user", cascade="all, delete-orphan"
    )
    export_jobs: Mapped[List["ExportJob"]] = relationship(
        "ExportJob", back_populates="user", cascade="all, delete-orphan"
    )
    circle_memberships: Mapped[List["CircleMembership"]] = relationship(
        "CircleMembership", back_populates="user", cascade="all, delete-orphan"
    )
    fusion_artworks: Mapped[List["FusionArtwork"]] = relationship(
        "FusionArtwork", back_populates="creator", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
