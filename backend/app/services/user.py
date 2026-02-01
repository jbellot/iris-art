"""User account management service layer."""

import json
import logging
import uuid
from datetime import datetime, timezone
from io import BytesIO
from typing import Optional
from zipfile import ZipFile

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import revoke_all_user_tokens
from app.models.consent import ConsentRecord
from app.models.user import User
from app.storage.s3 import S3Client

logger = logging.getLogger(__name__)


async def delete_user_account(
    db: AsyncSession,
    user_id: uuid.UUID,
    s3_client: S3Client,
) -> None:
    """Completely delete user account and all associated data (GDPR Article 17).

    This function implements the "Right to be Forgotten" by removing:
    - All S3 objects (iris images, generated art, exports)
    - All refresh tokens from Redis
    - All consent records from database
    - User record from database

    Args:
        db: Database session
        user_id: User UUID to delete
        s3_client: S3 client for deleting files

    Raises:
        Exception: If deletion fails at any step
    """
    user_id_str = str(user_id)

    logger.info(f"Starting account deletion for user_id={user_id_str}")

    try:
        # Step 1: Delete all S3 objects for user
        # Pattern: iris/{user_id}/, art/{user_id}/, exports/{user_id}/
        for prefix in [f"iris/{user_id_str}/", f"art/{user_id_str}/", f"exports/{user_id_str}/"]:
            s3_client.delete_user_files(prefix)
            logger.debug(f"Deleted S3 objects with prefix: {prefix}")

        # Step 2: Revoke all refresh tokens from Redis
        await revoke_all_user_tokens(user_id_str)
        logger.debug(f"Revoked all refresh tokens for user_id={user_id_str}")

        # Step 3: Delete all consent records (CASCADE should handle this, but explicit is safer)
        await db.execute(
            ConsentRecord.__table__.delete().where(ConsentRecord.user_id == user_id)
        )
        logger.debug(f"Deleted consent records for user_id={user_id_str}")

        # Step 4: Delete user record
        await db.execute(User.__table__.delete().where(User.id == user_id))
        logger.debug(f"Deleted user record for user_id={user_id_str}")

        # Step 5: Commit transaction
        await db.commit()

        # Step 6: Log deletion for compliance audit trail (ONLY log user_id, NOT personal data)
        logger.info(
            f"Account deletion complete: user_id={user_id_str}, "
            f"deleted_at={datetime.now(timezone.utc).isoformat()}"
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"Account deletion failed for user_id={user_id_str}: {e}")
        raise


async def export_user_data(
    db: AsyncSession,
    user_id: uuid.UUID,
    s3_client: S3Client,
) -> str:
    """Generate GDPR data export for user (Article 20: Right to Data Portability).

    Creates a ZIP file containing:
    - JSON manifest with user profile, consents, and metadata
    - Presigned URLs to S3 objects (iris images, art)

    Args:
        db: Database session
        user_id: User UUID
        s3_client: S3 client for listing files and generating URLs

    Returns:
        Presigned URL to download the export ZIP (valid for 24 hours)

    Raises:
        Exception: If export generation fails
    """
    user_id_str = str(user_id)

    logger.info(f"Starting data export for user_id={user_id_str}")

    try:
        # Step 1: Fetch user profile
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User not found: {user_id_str}")

        user_data = {
            "id": user_id_str,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "is_verified": user.is_verified,
            "auth_provider": user.auth_provider,
        }

        # Step 2: Fetch all consent records
        result = await db.execute(
            select(ConsentRecord)
            .where(ConsentRecord.user_id == user_id)
            .order_by(ConsentRecord.created_at.desc())
        )
        consent_records = result.scalars().all()

        consents_data = [
            {
                "id": str(consent.id),
                "consent_type": consent.consent_type,
                "jurisdiction": consent.jurisdiction,
                "granted": consent.granted,
                "granted_at": consent.granted_at.isoformat() if consent.granted_at else None,
                "withdrawn_at": consent.withdrawn_at.isoformat() if consent.withdrawn_at else None,
                "ip_address": consent.ip_address,
                "consent_text_version": consent.consent_text_version,
                "created_at": consent.created_at.isoformat() if consent.created_at else None,
            }
            for consent in consent_records
        ]

        # Step 3: List all S3 objects for user and generate presigned URLs
        s3_files = []
        for prefix in [f"iris/{user_id_str}/", f"art/{user_id_str}/"]:
            try:
                # List objects with prefix
                paginator = s3_client.client.get_paginator("list_objects_v2")
                pages = paginator.paginate(Bucket=s3_client.bucket_name, Prefix=prefix)

                for page in pages:
                    if "Contents" in page:
                        for obj in page["Contents"]:
                            key = obj["Key"]
                            # Generate presigned URL (1 hour expiry)
                            presigned_url = s3_client.generate_presigned_url(key, expiry=3600)
                            s3_files.append({
                                "key": key,
                                "size": obj["Size"],
                                "last_modified": obj["LastModified"].isoformat(),
                                "download_url": presigned_url,
                            })
            except Exception as e:
                logger.warning(f"Error listing S3 objects for prefix {prefix}: {e}")

        # Step 4: Create JSON manifest
        manifest = {
            "export_generated_at": datetime.now(timezone.utc).isoformat(),
            "user": user_data,
            "consents": consents_data,
            "files": s3_files,
            "file_count": len(s3_files),
        }

        # Step 5: Create ZIP file with manifest
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, "w") as zip_file:
            # Add JSON manifest
            manifest_json = json.dumps(manifest, indent=2)
            zip_file.writestr("user_data_manifest.json", manifest_json)

            # Add README
            readme = (
                f"IrisVue Data Export\n"
                f"===================\n\n"
                f"Generated: {manifest['export_generated_at']}\n"
                f"User ID: {user_id_str}\n"
                f"Email: {user_data['email']}\n\n"
                f"This export contains all your personal data stored in IrisVue:\n\n"
                f"1. user_data_manifest.json - Complete data export in JSON format\n"
                f"   - User profile information\n"
                f"   - Consent records with audit trail\n"
                f"   - List of files with presigned download URLs\n\n"
                f"Files ({len(s3_files)} total):\n"
                f"- Download links are valid for 1 hour from export generation\n"
                f"- Links are in the manifest JSON under 'files' -> 'download_url'\n\n"
                f"For questions, contact support.\n"
            )
            zip_file.writestr("README.txt", readme)

        zip_buffer.seek(0)

        # Step 6: Upload ZIP to S3 export path
        export_key = f"exports/{user_id_str}/data_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip"
        s3_client.upload_file(
            key=export_key,
            data=zip_buffer.getvalue(),
            content_type="application/zip",
            server_side_encryption=False,  # Disable for MinIO without KMS
        )

        # Step 7: Generate presigned URL for ZIP download (24 hours)
        download_url = s3_client.generate_presigned_url(export_key, expiry=86400)

        logger.info(f"Data export complete for user_id={user_id_str}")

        return download_url

    except Exception as e:
        logger.error(f"Data export failed for user_id={user_id_str}: {e}")
        raise
