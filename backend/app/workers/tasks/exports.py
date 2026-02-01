"""Celery tasks for data export."""

import logging
import uuid

from app.core.db import async_session_maker
from app.core.security import redis_client
from app.services.user import export_user_data
from app.storage.s3 import s3_client
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="export_user_data")
def export_user_data_task(user_id: str) -> None:
    """Celery task to generate user data export.

    Stores result URL in Redis with 24-hour TTL under key: export:{user_id}

    Args:
        user_id: User UUID as string
    """
    import asyncio

    logger.info(f"Starting data export task for user_id={user_id}")

    try:
        # Convert to UUID
        user_uuid = uuid.UUID(user_id)

        # Run async export function in event loop
        async def _run_export():
            async with async_session_maker() as db:
                try:
                    download_url = await export_user_data(db, user_uuid, s3_client)
                    return download_url
                except Exception as e:
                    await db.rollback()
                    raise

        # Execute async function
        download_url = asyncio.run(_run_export())

        # Store result in Redis with 24-hour TTL
        redis_key = f"export:{user_id}"
        asyncio.run(redis_client.setex(redis_key, 86400, download_url))

        logger.info(f"Data export task complete for user_id={user_id}")

    except Exception as e:
        logger.error(f"Data export task failed for user_id={user_id}: {e}")
        # Store error in Redis
        redis_key = f"export:{user_id}"
        asyncio.run(redis_client.setex(redis_key, 86400, f"ERROR: {str(e)}"))
        raise
