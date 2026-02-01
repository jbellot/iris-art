"""Photo schemas for API requests and responses."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PhotoRead(BaseModel):
    """Photo read schema with presigned URLs."""

    id: UUID
    user_id: UUID
    s3_key: str
    thumbnail_url: Optional[str] = None
    original_url: str
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    upload_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PhotoListResponse(BaseModel):
    """Paginated photo list response."""

    items: List[PhotoRead]
    total: int
    page: int
    page_size: int


class PresignedUploadResponse(BaseModel):
    """Response with presigned upload URL."""

    upload_url: str
    photo_id: UUID
    s3_key: str


class PhotoUploadComplete(BaseModel):
    """Request to confirm photo upload completion."""

    file_size: int = Field(..., gt=0, description="File size in bytes")
    width: int = Field(..., gt=0, description="Image width in pixels")
    height: int = Field(..., gt=0, description="Image height in pixels")
