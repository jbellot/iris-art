"""S3-compatible storage client with encryption support."""

from typing import Optional

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings


class S3Client:
    """S3-compatible storage client for MinIO/AWS S3."""

    def __init__(self):
        """Initialize S3 client from settings."""
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=Config(signature_version="s3v4"),
        )
        self.bucket_name = settings.S3_BUCKET_NAME

    def ensure_bucket(self, bucket: Optional[str] = None) -> None:
        """Create bucket if it doesn't exist."""
        bucket = bucket or self.bucket_name
        try:
            self.client.head_bucket(Bucket=bucket)
        except ClientError:
            # Bucket doesn't exist, create it
            self.client.create_bucket(Bucket=bucket)

    def upload_file(
        self, key: str, data: bytes, content_type: str = "application/octet-stream", server_side_encryption: bool = True
    ) -> None:
        """Upload file with optional server-side encryption.

        Args:
            key: S3 object key
            data: File data bytes
            content_type: MIME type
            server_side_encryption: Enable SSE-S3 (disable for MinIO without KMS)
        """
        put_args = {
            "Bucket": self.bucket_name,
            "Key": key,
            "Body": data,
            "ContentType": content_type,
        }

        # Only add ServerSideEncryption if enabled (MinIO without KMS doesn't support it)
        if server_side_encryption:
            put_args["ServerSideEncryption"] = "AES256"

        self.client.put_object(**put_args)

    def download_file(self, key: str) -> bytes:
        """Download file from storage."""
        response = self.client.get_object(Bucket=self.bucket_name, Key=key)
        return response["Body"].read()

    def delete_file(self, key: str) -> None:
        """Delete a single file."""
        self.client.delete_object(Bucket=self.bucket_name, Key=key)

    def delete_user_files(self, user_id_prefix: str) -> None:
        """Delete all files for a user (for GDPR compliance)."""
        # List all objects with the user's prefix
        paginator = self.client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.bucket_name, Prefix=user_id_prefix)

        for page in pages:
            if "Contents" in page:
                objects = [{"Key": obj["Key"]} for obj in page["Contents"]]
                if objects:
                    self.client.delete_objects(
                        Bucket=self.bucket_name, Delete={"Objects": objects}
                    )

    def generate_presigned_url(
        self, key: str, expiry: int = 3600
    ) -> str:
        """Generate a presigned URL for temporary access."""
        url = self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expiry,
        )
        return url


# Global S3 client instance
s3_client = S3Client()


def ensure_bucket(bucket: str) -> None:
    """Helper function to ensure bucket exists."""
    s3_client.ensure_bucket(bucket)
