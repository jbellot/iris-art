"""StylePreset model for curated artistic style presets."""

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class StyleCategory(str, enum.Enum):
    """Style preset categories."""

    ABSTRACT = "abstract"
    WATERCOLOR = "watercolor"
    OIL_PAINTING = "oil_painting"
    GEOMETRIC = "geometric"
    COSMIC = "cosmic"
    NATURE = "nature"
    POP_ART = "pop_art"
    MINIMALIST = "minimalist"


class StyleTier(str, enum.Enum):
    """Style preset tiers (free vs premium)."""

    FREE = "free"
    PREMIUM = "premium"


class StylePreset(Base):
    """Curated artistic style presets for iris art transformation.

    Attributes:
        id: UUID primary key
        name: Unique internal style name (e.g., "cosmic_iris")
        display_name: User-facing display name (e.g., "Cosmic Iris")
        description: Brief description of style effect
        category: Style category enum
        tier: Free or premium tier
        thumbnail_s3_key: S3 path to style preview thumbnail (optional)
        model_s3_key: S3 path or local path to ONNX model weights
        sort_order: Display order within tier (lower = shown first)
        is_active: Whether style is currently available
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "style_presets"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[StyleCategory] = mapped_column(Enum(StyleCategory), nullable=False)
    tier: Mapped[StyleTier] = mapped_column(Enum(StyleTier), nullable=False, index=True)
    thumbnail_s3_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_s3_key: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        """String representation."""
        return f"<StylePreset {self.name} ({self.tier.value})>"
