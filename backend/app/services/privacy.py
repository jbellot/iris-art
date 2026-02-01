"""Privacy compliance service layer with jurisdiction detection and consent management."""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consent import ConsentRecord

logger = logging.getLogger(__name__)


class Jurisdiction(str, Enum):
    """Privacy jurisdiction types."""

    GDPR = "gdpr"  # European Union
    BIPA = "bipa"  # Illinois Biometric Information Privacy Act
    CCPA = "ccpa"  # California Consumer Privacy Act
    GENERIC = "generic"  # Default fallback


# EU country codes for GDPR
EU_COUNTRIES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE",
    # Include EEA countries
    "IS", "LI", "NO",
    # Include UK for now (similar requirements)
    "GB",
}


async def detect_jurisdiction_from_ip(ip_address: str) -> Jurisdiction:
    """Detect jurisdiction from IP address using free IP geolocation API.

    For production, replace with GeoIP2/MaxMind database for better performance
    and reliability.

    Args:
        ip_address: IP address to geolocate

    Returns:
        Detected jurisdiction
    """
    # Skip detection for localhost/private IPs
    if ip_address in ("127.0.0.1", "localhost", "::1") or ip_address.startswith("192.168."):
        logger.info(f"Localhost IP detected: {ip_address}, defaulting to GENERIC")
        return Jurisdiction.GENERIC

    try:
        # Use ip-api.com for development (free, rate-limited: 45 req/min)
        # For production, use MaxMind GeoIP2 database or similar
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(
                f"http://ip-api.com/json/{ip_address}",
                params={"fields": "status,countryCode,regionCode"},
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success":
                logger.warning(f"IP geolocation failed for {ip_address}")
                return Jurisdiction.GENERIC

            country_code = data.get("countryCode", "").upper()
            region_code = data.get("regionCode", "").upper()

            # Check BIPA (Illinois only)
            if country_code == "US" and region_code == "IL":
                return Jurisdiction.BIPA

            # Check CCPA (California)
            if country_code == "US" and region_code == "CA":
                return Jurisdiction.CCPA

            # Check GDPR (EU/EEA countries)
            if country_code in EU_COUNTRIES:
                return Jurisdiction.GDPR

            return Jurisdiction.GENERIC

    except Exception as e:
        logger.error(f"IP geolocation error for {ip_address}: {e}")
        return Jurisdiction.GENERIC


def detect_jurisdiction(
    ip_address: str,
    country_code: Optional[str] = None,
    state_code: Optional[str] = None,
) -> Jurisdiction:
    """Detect jurisdiction from IP and optional device locale parameters.

    Priority:
    1. Use country_code + state_code from mobile device if provided (most reliable)
    2. Fall back to IP-based detection
    3. Default to GENERIC if uncertain

    Args:
        ip_address: Client IP address
        country_code: Optional ISO 3166-1 alpha-2 country code from device
        state_code: Optional state/region code from device

    Returns:
        Detected jurisdiction
    """
    # Priority: Use device-provided location if available (more reliable than IP)
    if country_code:
        country_code = country_code.upper()

        # Check BIPA (Illinois only)
        if country_code == "US" and state_code and state_code.upper() == "IL":
            return Jurisdiction.BIPA

        # Check CCPA (California)
        if country_code == "US" and state_code and state_code.upper() == "CA":
            return Jurisdiction.CCPA

        # Check GDPR (EU/EEA countries)
        if country_code in EU_COUNTRIES:
            return Jurisdiction.GDPR

        # Default for other countries
        return Jurisdiction.GENERIC

    # Fallback: IP-based detection (requires async call, so return GENERIC for sync context)
    # For async flow, use detect_jurisdiction_from_ip directly
    logger.info(f"No country_code provided, falling back to IP detection for {ip_address}")
    return Jurisdiction.GENERIC


def get_consent_requirements(jurisdiction: Jurisdiction) -> dict:
    """Get jurisdiction-specific consent requirements and text.

    Args:
        jurisdiction: Privacy jurisdiction

    Returns:
        Dictionary with consent requirements and consent text
    """
    if jurisdiction == Jurisdiction.GDPR:
        return {
            "explicit_consent": True,
            "purpose_disclosure": True,
            "retention_policy": True,
            "right_to_withdraw": True,
            "data_minimization": True,
            "consent_text": (
                "GDPR Biometric Data Consent\n\n"
                "We will collect and process your iris biometric data for the following purposes:\n"
                "- Creating artistic visualizations of your iris patterns\n"
                "- Generating personalized iris art products\n\n"
                "Legal basis: Your explicit consent (GDPR Article 9(2)(a))\n\n"
                "Data retention: Your iris images and processed data will be retained as long as your "
                "account is active. You may request deletion at any time through account settings.\n\n"
                "Your rights: You have the right to withdraw this consent at any time, request access to "
                "your data, request deletion (right to be forgotten), and data portability.\n\n"
                "Data minimization: We only collect iris biometric data necessary for art generation. "
                "No other facial features or personally identifiable information from images is stored.\n\n"
                "By granting consent, you acknowledge that you have read and understood this notice."
            ),
        }
    elif jurisdiction == Jurisdiction.BIPA:
        return {
            "explicit_consent": True,
            "purpose_disclosure": True,
            "retention_policy": True,
            "right_to_withdraw": True,
            "written_consent": True,
            "retention_schedule": True,
            "no_profit_from_data": True,
            "consent_text": (
                "Illinois Biometric Information Privacy Act (BIPA) Consent\n\n"
                "Written Consent Requirement: Under Illinois BIPA, we must obtain your written consent "
                "(electronic signature is valid) before collecting your biometric identifier (iris scan).\n\n"
                "Purpose: We will collect your iris biometric data specifically and solely for:\n"
                "- Creating artistic visualizations of your iris patterns\n"
                "- Generating personalized iris art products you request\n\n"
                "Retention Schedule: Your iris biometric data will be permanently deleted:\n"
                "- When you delete your account, OR\n"
                "- When the initial purpose for collecting the data is satisfied (art generation complete), OR\n"
                "- Within 3 years of your last interaction, whichever occurs first\n\n"
                "No Sale or Profit: We will NEVER sell, lease, trade, or profit from your biometric data. "
                "Your iris data is used ONLY for generating your requested art.\n\n"
                "Data Protection: Your biometric data is encrypted at rest and in transit. Access is "
                "restricted to authorized systems only.\n\n"
                "Your Rights: You may withdraw consent and request deletion at any time through account settings.\n\n"
                "By providing consent, you acknowledge this written notice and agree to iris data collection "
                "under these terms."
            ),
        }
    elif jurisdiction == Jurisdiction.CCPA:
        return {
            "explicit_consent": True,
            "purpose_disclosure": True,
            "retention_policy": True,
            "right_to_withdraw": True,
            "notice_at_collection": True,
            "opt_out_right": True,
            "deletion_right": True,
            "consent_text": (
                "California Consumer Privacy Act (CCPA) Notice and Consent\n\n"
                "Notice at Collection: We are collecting your iris biometric data (category: biometric information).\n\n"
                "Purpose: Your iris data will be used to:\n"
                "- Create artistic visualizations of your iris patterns\n"
                "- Generate personalized iris art products\n\n"
                "Categories of Data: Iris biometric identifier from photos you provide.\n\n"
                "Retention: We retain your iris data while your account is active. You may request deletion "
                "at any time.\n\n"
                "Your CCPA Rights:\n"
                "- Right to know what personal information is collected\n"
                "- Right to delete your personal information\n"
                "- Right to opt-out of sale (we do NOT sell biometric data)\n"
                "- Right to non-discrimination for exercising these rights\n\n"
                "No Sale: We do NOT sell your biometric information.\n\n"
                "Contact: Exercise your rights through account settings or contact support.\n\n"
                "By granting consent, you acknowledge this notice and agree to biometric data collection."
            ),
        }
    else:  # GENERIC
        return {
            "explicit_consent": True,
            "purpose_disclosure": True,
            "retention_policy": True,
            "right_to_withdraw": True,
            "consent_text": (
                "Biometric Data Consent\n\n"
                "Purpose: We will collect your iris biometric data to create artistic visualizations "
                "and personalized iris art products.\n\n"
                "Retention: Your iris data is retained while your account is active. You may request "
                "deletion at any time through account settings.\n\n"
                "Your Rights: You may withdraw consent and delete your data at any time.\n\n"
                "By granting consent, you acknowledge and agree to this iris data collection."
            ),
        }


async def grant_consent(
    db: AsyncSession,
    user_id: str,
    consent_type: str,
    jurisdiction: str,
    ip_address: str,
    consent_text_version: str,
) -> ConsentRecord:
    """Grant consent and create audit trail record.

    Args:
        db: Database session
        user_id: User UUID
        consent_type: Type of consent (e.g., "biometric_capture", "data_processing")
        jurisdiction: Jurisdiction code
        ip_address: Client IP address for audit trail
        consent_text_version: Version of consent text shown to user

    Returns:
        Created consent record

    Raises:
        HTTPException: If consent_type is invalid
    """
    # Validate consent_type
    valid_consent_types = {"biometric_capture", "data_processing", "marketing"}
    if consent_type not in valid_consent_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid consent_type. Must be one of: {', '.join(valid_consent_types)}",
        )

    # Create consent record with full audit trail
    consent_record = ConsentRecord(
        user_id=user_id,
        consent_type=consent_type,
        jurisdiction=jurisdiction,
        granted=True,
        granted_at=datetime.now(timezone.utc),
        ip_address=ip_address,
        consent_text_version=consent_text_version,
    )

    db.add(consent_record)
    await db.flush()
    await db.refresh(consent_record)

    logger.info(
        f"Consent granted: user_id={user_id}, type={consent_type}, "
        f"jurisdiction={jurisdiction}, version={consent_text_version}"
    )

    return consent_record


async def withdraw_consent(
    db: AsyncSession,
    user_id: str,
    consent_id: str,
) -> ConsentRecord:
    """Withdraw consent by setting withdrawn_at timestamp.

    NOTE: Does NOT delete the consent record (audit trail must be preserved).

    Args:
        db: Database session
        user_id: User UUID
        consent_id: Consent record UUID

    Returns:
        Updated consent record

    Raises:
        HTTPException: If consent not found or not owned by user
    """
    result = await db.execute(
        select(ConsentRecord).where(
            ConsentRecord.id == consent_id,
            ConsentRecord.user_id == user_id,
        )
    )
    consent_record = result.scalar_one_or_none()

    if not consent_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent record not found",
        )

    # Set withdrawn timestamp (preserves record for audit trail)
    consent_record.withdrawn_at = datetime.now(timezone.utc)
    consent_record.granted = False

    await db.flush()
    await db.refresh(consent_record)

    logger.info(f"Consent withdrawn: user_id={user_id}, consent_id={consent_id}")

    return consent_record


async def get_user_consents(
    db: AsyncSession,
    user_id: str,
) -> list[ConsentRecord]:
    """Get all consent records for a user.

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        List of consent records
    """
    result = await db.execute(
        select(ConsentRecord)
        .where(ConsentRecord.user_id == user_id)
        .order_by(ConsentRecord.created_at.desc())
    )
    return list(result.scalars().all())


async def has_biometric_consent(
    db: AsyncSession,
    user_id: str,
) -> bool:
    """Check if user has active biometric consent.

    This is the gate that will be checked before any iris capture in Phase 2.

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        True if user has active biometric consent, False otherwise
    """
    result = await db.execute(
        select(ConsentRecord).where(
            ConsentRecord.user_id == user_id,
            ConsentRecord.consent_type == "biometric_capture",
            ConsentRecord.granted == True,
            ConsentRecord.withdrawn_at == None,
        )
    )
    consent = result.scalar_one_or_none()
    return consent is not None
