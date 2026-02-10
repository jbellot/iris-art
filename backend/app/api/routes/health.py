"""Health check endpoints."""

import boto3
from botocore.exceptions import ClientError
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from redis import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.api.deps import get_session
from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {"status": "healthy", "version": __version__}


@router.get("/health/db")
async def health_check_db(session: AsyncSession = Depends(get_session)) -> Dict[str, Any]:
    """Database health check."""
    try:
        result = await session.execute(text("SELECT 1"))
        result.scalar()
        return {"status": "healthy", "service": "database"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}",
        )


@router.get("/health/redis")
async def health_check_redis() -> Dict[str, Any]:
    """Redis health check."""
    try:
        redis_client = Redis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)
        redis_client.ping()
        redis_client.close()
        return {"status": "healthy", "service": "redis"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis connection failed: {str(e)}",
        )


@router.get("/health/liveness")
async def health_liveness() -> Dict[str, Any]:
    """Liveness probe for container orchestration.

    Simple endpoint to check if the application is alive and responding.
    Used by container orchestrators to decide when to restart containers.
    """
    return {"status": "alive"}


@router.get("/health/readiness")
async def health_readiness(session: AsyncSession = Depends(get_session)) -> Dict[str, Any]:
    """Readiness probe for container orchestration.

    Checks all critical dependencies (DB, Redis, Storage) to determine
    if the application is ready to serve traffic.
    """
    services_status = {}

    # Check database
    try:
        await session.execute(text("SELECT 1"))
        services_status["db"] = "ok"
    except Exception as e:
        services_status["db"] = f"error: {str(e)}"

    # Check Redis
    try:
        redis_client = Redis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)
        redis_client.ping()
        redis_client.close()
        services_status["redis"] = "ok"
    except Exception as e:
        services_status["redis"] = f"error: {str(e)}"

    # Check MinIO/S3 storage
    try:
        s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
        )
        # Try to head the bucket to verify access
        s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        services_status["storage"] = "ok"
    except ClientError as e:
        services_status["storage"] = f"error: {str(e)}"
    except Exception as e:
        services_status["storage"] = f"error: {str(e)}"

    # Check if all services are ok
    all_healthy = all(status == "ok" for status in services_status.values())

    if all_healthy:
        return {"status": "ready", **services_status}
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not ready", **services_status},
        )
