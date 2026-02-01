"""Database models for IrisVue."""

from app.core.db import Base
from app.models.consent import ConsentRecord
from app.models.photo import Photo
from app.models.user import User

__all__ = ["Base", "User", "ConsentRecord", "Photo"]
