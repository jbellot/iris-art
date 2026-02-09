"""Consent API routes for artwork usage permissions."""

from typing import Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.user import User
from app.schemas.consent import (
    ConsentDecision,
    ConsentRequestCreate,
    ConsentResponse,
    ConsentStatusResponse,
    PendingConsentResponse,
)
from app.services import consent_service

router = APIRouter(prefix="/consent", tags=["consent"])


@router.post("/request", response_model=Dict[str, List])
async def request_consent(
    request: ConsentRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Request consent for artwork usage.

    Returns dict with:
    - created: List of newly created consent requests
    - already_granted: List of artwork IDs that are already granted or self-owned
    """
    result = await consent_service.request_consent(
        artwork_ids=request.artwork_ids,
        requester_id=current_user.id,
        purpose=request.purpose,
        circle_id=request.circle_id,
        db=db,
    )
    return result


@router.get("/pending", response_model=List[PendingConsentResponse])
async def get_pending_consents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get all pending consent requests for current user (as grantor)."""
    return await consent_service.get_pending_consents_for_user(current_user.id, db)


@router.post("/{consent_id}/decide", response_model=ConsentResponse)
async def decide_consent(
    consent_id: UUID,
    decision: ConsentDecision,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Grant or deny a consent request."""
    if decision.status == "granted":
        return await consent_service.grant_consent(consent_id, current_user.id, db)
    else:
        return await consent_service.deny_consent(consent_id, current_user.id, db)


@router.post("/{consent_id}/revoke", response_model=ConsentResponse)
async def revoke_consent(
    consent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Revoke a previously granted consent."""
    return await consent_service.revoke_consent(consent_id, current_user.id, db)


@router.get("/status", response_model=Dict[str, str])
async def get_consent_status(
    artwork_ids: List[UUID] = Query(..., description="List of artwork IDs to check"),
    purpose: str = Query(..., description="Purpose: fusion or composition"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get consent status for multiple artworks.

    Returns dict mapping artwork_id to status:
    - "self": User owns the artwork (implicit consent)
    - "granted": Consent has been granted
    - "pending": Consent request is pending
    - "denied": Consent was denied
    - "revoked": Consent was revoked
    - "none": No consent request exists
    """
    return await consent_service.get_consent_status(
        artwork_ids=artwork_ids,
        requester_id=current_user.id,
        purpose=purpose,
        db=db,
    )
