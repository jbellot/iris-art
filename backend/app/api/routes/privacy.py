"""Privacy compliance API endpoints."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_session
from app.models.user import User
from app.schemas.privacy import (
    AccountDeletionResponse,
    ConsentGrantRequest,
    ConsentGrantResponse,
    ConsentListResponse,
    DataExportResponse,
    JurisdictionResponse,
)
from app.services.privacy import (
    Jurisdiction,
    detect_jurisdiction,
    detect_jurisdiction_from_ip,
    get_consent_requirements,
    get_user_consents,
    grant_consent,
    has_biometric_consent,
    withdraw_consent,
)
from app.workers.tasks.exports import export_user_data_task
from app.core.security import redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/privacy", tags=["privacy"])


@router.get("/jurisdiction", response_model=JurisdictionResponse)
async def get_jurisdiction(
    request: Request,
    country_code: Optional[str] = None,
    state_code: Optional[str] = None,
) -> JurisdictionResponse:
    """Detect user's privacy jurisdiction and return consent requirements.

    Query parameters (optional, from mobile device):
    - country_code: ISO 3166-1 alpha-2 country code (e.g., "US", "DE", "FR")
    - state_code: State/region code (e.g., "IL", "CA")

    Returns:
        Jurisdiction code and jurisdiction-specific consent requirements

    Note:
        No authentication required - needed before user registers/consents
    """
    # Get client IP
    ip_address = request.client.host if request.client else "127.0.0.1"

    # Detect jurisdiction (prioritizes device locale if provided)
    if country_code:
        jurisdiction = detect_jurisdiction(ip_address, country_code, state_code)
    else:
        # Use IP-based detection (async)
        jurisdiction = await detect_jurisdiction_from_ip(ip_address)

    # Get consent requirements for jurisdiction
    requirements_dict = get_consent_requirements(jurisdiction)

    # Convert to ConsentRequirements schema
    from app.schemas.privacy import ConsentRequirements
    requirements = ConsentRequirements(**requirements_dict)

    return JurisdictionResponse(
        jurisdiction=jurisdiction.value,
        consent_requirements=requirements,
    )


@router.get("/consent", response_model=ConsentListResponse)
async def list_consents(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> ConsentListResponse:
    """Get all consent records for current user.

    Returns:
        List of user's consent records with audit trail

    Requires:
        Authentication
    """
    consents = await get_user_consents(db, str(current_user.id))

    consent_responses = [
        ConsentGrantResponse(
            id=consent.id,
            consent_type=consent.consent_type,
            jurisdiction=consent.jurisdiction,
            granted=consent.granted,
            granted_at=consent.granted_at,
        )
        for consent in consents
    ]

    return ConsentListResponse(consents=consent_responses)


@router.post("/consent", response_model=ConsentGrantResponse, status_code=status.HTTP_201_CREATED)
async def grant_user_consent(
    request: Request,
    consent_request: ConsentGrantRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> ConsentGrantResponse:
    """Grant consent with full audit trail.

    Request body:
    - consent_type: "biometric_capture" or "data_processing"
    - jurisdiction: Jurisdiction code (from /jurisdiction endpoint)
    - consent_text_version: Version of consent text shown to user (e.g., "v1.0")

    Returns:
        Created consent record

    Requires:
        Authentication
    """
    # Get client IP for audit trail
    ip_address = request.client.host if request.client else "127.0.0.1"

    # Grant consent
    consent_record = await grant_consent(
        db=db,
        user_id=str(current_user.id),
        consent_type=consent_request.consent_type,
        jurisdiction=consent_request.jurisdiction,
        ip_address=ip_address,
        consent_text_version=consent_request.consent_text_version,
    )

    return ConsentGrantResponse(
        id=consent_record.id,
        consent_type=consent_record.consent_type,
        jurisdiction=consent_record.jurisdiction,
        granted=consent_record.granted,
        granted_at=consent_record.granted_at,
    )


@router.post("/consent/{consent_id}/withdraw", response_model=ConsentGrantResponse)
async def withdraw_user_consent(
    consent_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> ConsentGrantResponse:
    """Withdraw previously granted consent.

    NOTE: This does NOT delete the consent record (audit trail is preserved).
    It sets withdrawn_at timestamp and granted=False.

    Path parameters:
    - consent_id: UUID of consent record to withdraw

    Returns:
        Updated consent record

    Requires:
        Authentication
    """
    # Withdraw consent
    consent_record = await withdraw_consent(
        db=db,
        user_id=str(current_user.id),
        consent_id=str(consent_id),
    )

    return ConsentGrantResponse(
        id=consent_record.id,
        consent_type=consent_record.consent_type,
        jurisdiction=consent_record.jurisdiction,
        granted=consent_record.granted,
        granted_at=consent_record.granted_at,
    )


@router.get("/consent/biometric-status")
async def get_biometric_consent_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Check if user has active biometric consent.

    This is the gate that mobile app checks before showing iris camera.

    Returns:
        {"has_consent": bool}

    Requires:
        Authentication
    """
    has_consent = await has_biometric_consent(db, str(current_user.id))

    return {"has_consent": has_consent}


@router.post("/data-export", response_model=DataExportResponse)
async def request_data_export(
    current_user: User = Depends(get_current_active_user),
) -> DataExportResponse:
    """Request GDPR data export (Article 20: Right to Data Portability).

    Dispatches Celery task to generate ZIP file with:
    - JSON manifest with user profile, consents, and metadata
    - Presigned URLs to download S3 files (iris images, art)

    Returns:
        Status message with "pending" status
        Use GET /data-export/status to check completion and get download URL

    Requires:
        Authentication
    """
    # Dispatch Celery task
    export_user_data_task.delay(str(current_user.id))

    logger.info(f"Data export requested for user_id={current_user.id}")

    return DataExportResponse(
        message="Data export is being generated. Check /data-export/status for completion.",
        status="pending",
    )


@router.get("/data-export/status", response_model=DataExportResponse)
async def get_data_export_status(
    current_user: User = Depends(get_current_active_user),
) -> DataExportResponse:
    """Check status of data export request.

    Returns:
        - status="pending": Export still being generated
        - status="ready": Export complete, download URL available
        - status="expired": Export expired or not found

    Requires:
        Authentication
    """
    # Check Redis for export result
    redis_key = f"export:{current_user.id}"
    result = await redis_client.get(redis_key)

    if not result:
        return DataExportResponse(
            message="No export found or export has expired. Request a new export.",
            status="expired",
        )

    if result.startswith("ERROR:"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export generation failed: {result}",
        )

    # Result is the presigned URL
    return DataExportResponse(
        message="Data export ready for download (valid for 24 hours)",
        export_url=result,
        status="ready",
    )
