"""Health check endpoints."""

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
