"""WebSocket endpoints for real-time job progress streaming."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import jwt
from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import async_session_maker
from app.models.processing_job import ProcessingJob
from app.models.user import User
from app.storage.s3 import s3_client
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter()

# Map internal step names to magical, user-facing names
STEP_DISPLAY_NAMES = {
    "loading": "Preparing your image...",
    "segmenting": "Finding your iris...",
    "removing_reflections": "Removing reflections...",
    "enhancing": "Enhancing quality...",
    "saving": "Almost done...",
    "completed": "Complete!",
}

# WebSocket polling interval in seconds
POLL_INTERVAL = 0.5  # 500ms

# Maximum WebSocket connection duration in seconds
MAX_CONNECTION_TIME = 600  # 10 minutes


async def validate_token_and_get_user(token: str, db: AsyncSession) -> User:
    """Validate JWT token and retrieve user.

    Args:
        token: JWT access token from query parameter
        db: Database session

    Returns:
        User object if token is valid

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        if payload.get("type") != "access":
            raise credentials_exception

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError:
        raise credentials_exception

    # Fetch user from database
    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_job_from_db(db: AsyncSession, job_id: str) -> Optional[ProcessingJob]:
    """Fetch job from database.

    Args:
        db: Database session
        job_id: Job UUID as string

    Returns:
        ProcessingJob or None if not found
    """
    try:
        job_uuid = uuid.UUID(job_id)
    except (ValueError, AttributeError):
        return None

    result = await db.execute(select(ProcessingJob).where(ProcessingJob.id == job_uuid))
    return result.scalar_one_or_none()


def get_display_step_name(internal_step: Optional[str]) -> str:
    """Map internal step name to user-facing magical name.

    Args:
        internal_step: Internal step name from task

    Returns:
        User-facing step name
    """
    if not internal_step:
        return "Processing..."

    return STEP_DISPLAY_NAMES.get(internal_step, "Processing...")


@router.websocket("/ws/jobs/{job_id}")
async def job_progress_websocket(websocket: WebSocket, job_id: str, token: Optional[str] = None):
    """WebSocket endpoint for real-time job progress streaming.

    Polls Celery task state and database job record, streams updates to client
    with magical step names, handles completion/failure, and gracefully handles
    disconnection (job continues in background).

    Args:
        websocket: WebSocket connection
        job_id: Processing job ID
        token: JWT access token from query parameter (?token=...)

    Connection flow:
        1. Accept connection
        2. Validate JWT token
        3. Verify job exists and belongs to user
        4. Enter polling loop (500ms interval)
        5. Send progress updates until completion/failure/timeout
        6. Close connection

    Message types sent:
        - Progress: {job_id, status, progress, step, timestamp}
        - Completion: extends Progress with {result_url, processing_time_ms, dimensions}
        - Error: extends Progress with {error_type, message, suggestion}
    """
    await websocket.accept()

    # Validate token
    if not token:
        await websocket.send_json(
            {"error": "Authentication required", "detail": "Token missing from query parameters"}
        )
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        async with async_session_maker() as db:
            user = await validate_token_and_get_user(token, db)

            # Verify job exists and belongs to user
            job = await get_job_from_db(db, job_id)
            if not job:
                await websocket.send_json({"error": "Job not found", "detail": f"No job with ID {job_id}"})
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

            if job.user_id != user.id:
                await websocket.send_json(
                    {"error": "Unauthorized", "detail": "Job does not belong to authenticated user"}
                )
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

    except HTTPException as e:
        await websocket.send_json({"error": e.detail})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    logger.info(f"WebSocket connected for job {job_id}")

    # Start time for timeout tracking
    start_time = asyncio.get_event_loop().time()

    try:
        while True:
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > MAX_CONNECTION_TIME:
                logger.warning(f"WebSocket timeout for job {job_id} after {elapsed:.1f}s")
                await websocket.send_json(
                    {
                        "error": "Connection timeout",
                        "detail": "Maximum connection time exceeded. Job continues in background.",
                    }
                )
                break

            # Get Celery task state
            async_result = AsyncResult(job_id, app=celery_app)
            celery_state = async_result.state
            celery_info = async_result.info if isinstance(async_result.info, dict) else {}

            # Get job from database (for persistent state)
            async with async_session_maker() as db:
                job = await get_job_from_db(db, job_id)

                if not job:
                    await websocket.send_json({"error": "Job not found", "detail": "Job was deleted"})
                    break

                # Determine current state (prefer Celery state for in-progress, DB for completed/failed)
                if job.status == "completed":
                    # Job completed - send completion message
                    result_url = s3_client.generate_presigned_url(job.result_s3_key, expiry=3600)

                    await websocket.send_json(
                        {
                            "job_id": job_id,
                            "status": "completed",
                            "progress": 100,
                            "step": get_display_step_name("completed"),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "result_url": result_url,
                            "processing_time_ms": job.processing_time_ms,
                            "result_width": job.result_width,
                            "result_height": job.result_height,
                        }
                    )
                    logger.info(f"Job {job_id} completed, closing WebSocket")
                    break

                elif job.status == "failed":
                    # Job failed - send error message
                    await websocket.send_json(
                        {
                            "job_id": job_id,
                            "status": "failed",
                            "progress": job.progress,
                            "step": get_display_step_name(job.current_step),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "error_type": job.error_type or "server_error",
                            "message": job.error_message or "An unexpected error occurred",
                            "suggestion": job.suggestion,
                        }
                    )
                    logger.info(f"Job {job_id} failed with {job.error_type}, closing WebSocket")
                    break

                else:
                    # Job in progress - send progress update
                    # Use Celery meta if available, otherwise use DB state
                    if celery_state == "PROGRESS" and celery_info:
                        current_step = celery_info.get("step", job.current_step)
                        progress = celery_info.get("progress", job.progress)
                    else:
                        current_step = job.current_step
                        progress = job.progress

                    await websocket.send_json(
                        {
                            "job_id": job_id,
                            "status": job.status,
                            "progress": progress,
                            "step": get_display_step_name(current_step),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )

            # Wait before next poll
            await asyncio.sleep(POLL_INTERVAL)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job {job_id}. Job continues in background.")

    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}", exc_info=True)
        try:
            await websocket.send_json({"error": "Internal server error", "detail": str(e)})
        except:
            pass

    finally:
        try:
            await websocket.close()
        except:
            pass
