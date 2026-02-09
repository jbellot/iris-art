"""Consent service for managing artwork usage permissions."""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.artwork_consent import ArtworkConsent
from app.models.circle import Circle
from app.models.photo import Photo
from app.models.user import User
from app.schemas.consent import ConsentResponse, PendingConsentResponse
from app.storage.s3 import S3Client


async def request_consent(
    artwork_ids: List[uuid.UUID],
    requester_id: uuid.UUID,
    purpose: str,
    circle_id: Optional[uuid.UUID],
    db: AsyncSession,
) -> Dict[str, List]:
    """Request consent for artwork usage.

    Args:
        artwork_ids: List of artwork IDs to request consent for
        requester_id: User ID requesting consent
        purpose: Purpose of usage (fusion or composition)
        circle_id: Optional circle ID for scoped consent
        db: Database session

    Returns:
        Dict with 'created' (list of new consent records) and 'already_granted' (list of artwork IDs)

    Raises:
        HTTPException: If artwork not found
    """
    created_consents = []
    already_granted = []

    for artwork_id in artwork_ids:
        # Get photo with owner
        result = await db.execute(
            select(Photo).where(Photo.id == artwork_id)
        )
        photo = result.scalar_one_or_none()

        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artwork {artwork_id} not found"
            )

        # Skip if requester owns the artwork (self-consent is implicit)
        if photo.user_id == requester_id:
            already_granted.append(artwork_id)
            continue

        # Check for existing granted consent
        existing_granted = await db.execute(
            select(ArtworkConsent)
            .where(
                and_(
                    ArtworkConsent.artwork_id == artwork_id,
                    ArtworkConsent.grantee_user_id == requester_id,
                    ArtworkConsent.purpose == purpose,
                    ArtworkConsent.status == "granted"
                )
            )
        )
        if existing_granted.scalar_one_or_none():
            already_granted.append(artwork_id)
            continue

        # Check for existing pending consent (skip if already pending)
        existing_pending = await db.execute(
            select(ArtworkConsent)
            .where(
                and_(
                    ArtworkConsent.artwork_id == artwork_id,
                    ArtworkConsent.grantee_user_id == requester_id,
                    ArtworkConsent.purpose == purpose,
                    ArtworkConsent.status == "pending"
                )
            )
        )
        if existing_pending.scalar_one_or_none():
            continue

        # Create new consent request
        consent = ArtworkConsent(
            artwork_id=artwork_id,
            grantor_user_id=photo.user_id,
            grantee_user_id=requester_id,
            circle_id=circle_id,
            purpose=purpose,
            status="pending",
        )
        db.add(consent)
        created_consents.append(consent)

    await db.commit()

    # Refresh to get IDs
    for consent in created_consents:
        await db.refresh(consent)

    return {
        "created": [ConsentResponse.model_validate(c) for c in created_consents],
        "already_granted": already_granted,
    }


async def grant_consent(
    consent_id: uuid.UUID, grantor_id: uuid.UUID, db: AsyncSession
) -> ConsentResponse:
    """Grant consent for artwork usage.

    Args:
        consent_id: ID of the consent request
        grantor_id: User ID granting consent (must be artwork owner)
        db: Database session

    Returns:
        Updated consent response

    Raises:
        HTTPException: If consent not found or user is not grantor
    """
    # Get consent with artwork
    result = await db.execute(
        select(ArtworkConsent)
        .options(selectinload(ArtworkConsent.artwork))
        .where(ArtworkConsent.id == consent_id)
    )
    consent = result.scalar_one_or_none()

    if not consent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent request not found"
        )

    # Verify grantor owns the artwork
    if consent.grantor_user_id != grantor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only grant consent for your own artwork"
        )

    # Update consent
    consent.status = "granted"
    consent.decided_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(consent)

    return ConsentResponse.model_validate(consent)


async def deny_consent(
    consent_id: uuid.UUID, grantor_id: uuid.UUID, db: AsyncSession
) -> ConsentResponse:
    """Deny consent for artwork usage.

    Args:
        consent_id: ID of the consent request
        grantor_id: User ID denying consent (must be artwork owner)
        db: Database session

    Returns:
        Updated consent response

    Raises:
        HTTPException: If consent not found or user is not grantor
    """
    # Get consent
    result = await db.execute(
        select(ArtworkConsent).where(ArtworkConsent.id == consent_id)
    )
    consent = result.scalar_one_or_none()

    if not consent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent request not found"
        )

    # Verify grantor owns the artwork
    if consent.grantor_user_id != grantor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only deny consent for your own artwork"
        )

    # Update consent
    consent.status = "denied"
    consent.decided_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(consent)

    return ConsentResponse.model_validate(consent)


async def revoke_consent(
    consent_id: uuid.UUID, grantor_id: uuid.UUID, db: AsyncSession
) -> ConsentResponse:
    """Revoke previously granted consent.

    Args:
        consent_id: ID of the consent to revoke
        grantor_id: User ID revoking consent (must be artwork owner)
        db: Database session

    Returns:
        Updated consent response

    Raises:
        HTTPException: If consent not found, not granted, or user is not grantor
    """
    # Get consent
    result = await db.execute(
        select(ArtworkConsent).where(ArtworkConsent.id == consent_id)
    )
    consent = result.scalar_one_or_none()

    if not consent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent not found"
        )

    # Verify grantor owns the artwork
    if consent.grantor_user_id != grantor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only revoke consent for your own artwork"
        )

    # Only revoke if currently granted
    if consent.status != "granted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only revoke granted consent"
        )

    # Update consent
    consent.status = "revoked"
    consent.decided_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(consent)

    return ConsentResponse.model_validate(consent)


async def check_all_consents_granted(
    artwork_ids: List[uuid.UUID],
    requester_id: uuid.UUID,
    purpose: str,
    db: AsyncSession,
) -> bool:
    """Check if all consents are granted for given artworks.

    For artworks owned by requester, consent is implicit (always granted).
    For artworks owned by others, checks for granted consent.

    Args:
        artwork_ids: List of artwork IDs to check
        requester_id: User ID requesting usage
        purpose: Purpose of usage (fusion or composition)
        db: Database session

    Returns:
        True if all consents are granted, False otherwise
    """
    for artwork_id in artwork_ids:
        # Get photo to check ownership
        result = await db.execute(
            select(Photo).where(Photo.id == artwork_id)
        )
        photo = result.scalar_one_or_none()

        if not photo:
            return False

        # Skip if requester owns artwork (implicit consent)
        if photo.user_id == requester_id:
            continue

        # Check for granted consent
        consent_result = await db.execute(
            select(ArtworkConsent)
            .where(
                and_(
                    ArtworkConsent.artwork_id == artwork_id,
                    ArtworkConsent.grantee_user_id == requester_id,
                    ArtworkConsent.purpose == purpose,
                    ArtworkConsent.status == "granted"
                )
            )
        )
        consent = consent_result.scalar_one_or_none()

        if not consent:
            return False

    return True


async def get_pending_consents_for_user(
    user_id: uuid.UUID, db: AsyncSession
) -> List[PendingConsentResponse]:
    """Get all pending consent requests for a user (as grantor).

    Args:
        user_id: User ID (as grantor/artwork owner)
        db: Database session

    Returns:
        List of pending consent responses with artwork preview URLs
    """
    # Get pending consents with related data
    result = await db.execute(
        select(ArtworkConsent)
        .options(
            selectinload(ArtworkConsent.artwork),
            selectinload(ArtworkConsent.grantee),
            selectinload(ArtworkConsent.circle),
        )
        .where(
            and_(
                ArtworkConsent.grantor_user_id == user_id,
                ArtworkConsent.status == "pending"
            )
        )
        .order_by(ArtworkConsent.requested_at.desc())
    )
    consents = result.scalars().all()

    # Generate presigned URLs for artwork previews
    s3_client = S3Client()
    pending_consents = []

    for consent in consents:
        # Generate presigned URL for thumbnail or original
        s3_key = consent.artwork.thumbnail_s3_key or consent.artwork.s3_key
        preview_url = s3_client.generate_presigned_url(s3_key, expiry=3600)

        pending_consents.append(
            PendingConsentResponse(
                id=consent.id,
                artwork_id=consent.artwork_id,
                artwork_preview_url=preview_url,
                grantee_email=consent.grantee.email,
                purpose=consent.purpose,
                circle_name=consent.circle.name if consent.circle else None,
                requested_at=consent.requested_at,
            )
        )

    return pending_consents


async def get_consent_status(
    artwork_ids: List[uuid.UUID],
    requester_id: uuid.UUID,
    purpose: str,
    db: AsyncSession,
) -> Dict[str, str]:
    """Get consent status for multiple artworks.

    Args:
        artwork_ids: List of artwork IDs to check
        requester_id: User ID requesting status
        purpose: Purpose of usage (fusion or composition)
        db: Database session

    Returns:
        Dict mapping artwork_id to status: "self", "granted", "pending", "denied", "none"
    """
    status_map = {}

    for artwork_id in artwork_ids:
        # Get photo to check ownership
        result = await db.execute(
            select(Photo).where(Photo.id == artwork_id)
        )
        photo = result.scalar_one_or_none()

        if not photo:
            status_map[str(artwork_id)] = "none"
            continue

        # Check if requester owns artwork
        if photo.user_id == requester_id:
            status_map[str(artwork_id)] = "self"
            continue

        # Check for consent
        consent_result = await db.execute(
            select(ArtworkConsent)
            .where(
                and_(
                    ArtworkConsent.artwork_id == artwork_id,
                    ArtworkConsent.grantee_user_id == requester_id,
                    ArtworkConsent.purpose == purpose,
                )
            )
            .order_by(ArtworkConsent.requested_at.desc())
        )
        consent = consent_result.scalar_one_or_none()

        if consent:
            status_map[str(artwork_id)] = consent.status
        else:
            status_map[str(artwork_id)] = "none"

    return status_map
