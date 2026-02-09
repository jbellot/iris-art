"""Circle schemas for API requests and responses."""

from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field


class CircleCreateRequest(BaseModel):
    """Request to create a new circle."""

    name: str = Field(..., min_length=1, max_length=50, description="Circle name")


class CircleResponse(BaseModel):
    """Circle response with membership info."""

    id: UUID
    name: str
    role: str
    member_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CircleMemberResponse(BaseModel):
    """Circle member response."""

    user_id: UUID
    email: str
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class CircleDetailResponse(BaseModel):
    """Circle detail response with members list."""

    id: UUID
    name: str
    role: str
    member_count: int
    created_at: datetime
    members: List[CircleMemberResponse]

    model_config = {"from_attributes": True}


class InviteCreateResponse(BaseModel):
    """Response with invite token and URL."""

    invite_url: str
    token: str
    expires_in_days: int


class InviteAcceptRequest(BaseModel):
    """Request to accept an invite."""

    token: str = Field(..., description="Invite token")


class InviteInfoResponse(BaseModel):
    """Invite preview info response."""

    circle_id: UUID
    circle_name: str
    inviter_email: str
