"""Celery tasks for artistic style transfer."""

import io
import logging
import time

import cv2
import numpy as np
from celery import Task

from app.core.db import get_sync_session_maker
from app.models.style_job import StyleJob
from app.storage.s3 import s3_client
from app.workers.celery_app import celery_app
from app.workers.models.model_cache import ModelCache

logger = logging.getLogger(__name__)


class RetryableStyleTask(Task):
    """Base task class with retry configuration for style transfer tasks."""

    autoretry_for = (ConnectionError, TimeoutError, RuntimeError)
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes max backoff
    retry_jitter = True
    max_retries = 1  # Auto-retry ONCE on transient failures

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task permanent failure - clean up and update status.

        Args:
            exc: Exception that caused failure
            task_id: Task ID
            args: Task positional arguments
            kwargs: Task keyword arguments
            einfo: Exception info
        """
        job_id = args[0] if args else kwargs.get("job_id")
        user_id = args[1] if len(args) > 1 else kwargs.get("user_id")

        if not job_id:
            return

        SessionMaker = get_sync_session_maker()
        logger.error(f"Style job {job_id} permanently failed: {type(exc).__name__}: {exc}")

        # Clean up partial S3 objects
        if user_id:
            try:
                preview_s3_key = f"styled/{user_id}/{job_id}_preview.jpg"
                result_s3_key = f"styled/{user_id}/{job_id}.jpg"

                try:
                    s3_client.delete_file(preview_s3_key)
                    logger.info(f"Cleaned up partial preview: {preview_s3_key}")
                except Exception as e:
                    logger.debug(f"No partial preview to clean: {preview_s3_key} - {e}")

                try:
                    s3_client.delete_file(result_s3_key)
                    logger.info(f"Cleaned up partial result: {result_s3_key}")
                except Exception as e:
                    logger.debug(f"No partial result to clean: {result_s3_key} - {e}")

            except Exception as e:
                logger.warning(f"Error during S3 cleanup for style job {job_id}: {e}")

        # Error classification
        if isinstance(exc, ValueError):
            # Quality issues - already handled in task body
            pass
        elif isinstance(exc, (ConnectionError, TimeoutError)):
            _update_style_job_sync(
                SessionMaker,
                job_id,
                "failed",
                error_type="transient_error",
                error_message="Style processing timed out. Please try again.",
            )
        elif isinstance(exc, RuntimeError):
            _update_style_job_sync(
                SessionMaker,
                job_id,
                "failed",
                error_type="server_error",
                error_message="Something went wrong during styling. Please try again later.",
            )
        else:
            _update_style_job_sync(
                SessionMaker,
                job_id,
                "failed",
                error_type="server_error",
                error_message="An unexpected error occurred.",
            )


@celery_app.task(bind=True, base=RetryableStyleTask, name="app.workers.tasks.style_transfer.apply_style_preset")
def apply_style_preset(
    self,
    job_id: str,
    user_id: str,
    photo_s3_key: str,
    style_preset_name: str,
    style_model_path: str,
):
    """Apply artistic style preset to an iris image.

    Generates both a low-res preview (256x256) and full-res result (1024x1024).

    Args:
        job_id: StyleJob ID
        user_id: User ID
        photo_s3_key: S3 key of source image (processed iris or original photo)
        style_preset_name: Style preset name (for model caching)
        style_model_path: Path to ONNX model weights

    Pipeline steps:
        1. Load source image from S3
        2. Apply style transfer (preview + full-res)
        3. Upload results to S3
        4. Update job in database
    """
    start_time = time.time()
    SessionMaker = get_sync_session_maker()

    logger.info(f"Starting style transfer for job {job_id} with style {style_preset_name}")

    try:
        # Step 1: Load source image (0-10%)
        _update_style_job_sync(
            SessionMaker, job_id, "processing", current_step="Preparing your canvas...", progress=5
        )
        self.update_state(
            state="PROGRESS",
            meta={"step": "Preparing your canvas...", "progress": 5, "job_id": job_id},
        )

        # Download image from S3
        image_bytes = s3_client.download_file(photo_s3_key)
        image_array = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Failed to decode source image")

        _update_style_job_sync(
            SessionMaker, job_id, "processing", current_step="Preparing your canvas...", progress=10
        )
        self.update_state(
            state="PROGRESS",
            meta={"step": "Preparing your canvas...", "progress": 10, "job_id": job_id},
        )

        # Step 2: Apply style transfer (10-70%)
        logger.info(f"Job {job_id}: Applying style {style_preset_name}")
        _update_style_job_sync(
            SessionMaker, job_id, "processing", current_step="Applying artistic style...", progress=20
        )
        self.update_state(
            state="PROGRESS",
            meta={"step": "Applying artistic style...", "progress": 20, "job_id": job_id},
        )

        # Load style model from cache
        style_model = ModelCache.get_style_model(style_preset_name, style_model_path)

        # Generate preview (low-res, 256x256)
        _update_style_job_sync(
            SessionMaker, job_id, "processing", current_step="Applying artistic style...", progress=40
        )
        self.update_state(
            state="PROGRESS",
            meta={"step": "Applying artistic style...", "progress": 40, "job_id": job_id},
        )

        preview = style_model.apply(image, output_size=(256, 256))

        # Generate full-res (1024x1024)
        _update_style_job_sync(
            SessionMaker, job_id, "processing", current_step="Applying artistic style...", progress=60
        )
        self.update_state(
            state="PROGRESS",
            meta={"step": "Applying artistic style...", "progress": 60, "job_id": job_id},
        )

        full_result = style_model.apply(image, output_size=(1024, 1024))

        _update_style_job_sync(
            SessionMaker, job_id, "processing", current_step="Applying artistic style...", progress=70
        )
        self.update_state(
            state="PROGRESS",
            meta={"step": "Applying artistic style...", "progress": 70, "job_id": job_id},
        )

        # Step 3: Upload results to S3 (70-90%)
        logger.info(f"Job {job_id}: Uploading styled results")
        _update_style_job_sync(
            SessionMaker, job_id, "processing", current_step="Adding final touches...", progress=75
        )
        self.update_state(
            state="PROGRESS",
            meta={"step": "Adding final touches...", "progress": 75, "job_id": job_id},
        )

        # Upload preview (JPEG quality 70 for smaller file size)
        preview_s3_key = f"styled/{user_id}/{job_id}_preview.jpg"
        _, preview_buffer = cv2.imencode(".jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 70])
        s3_client.upload_file(
            preview_s3_key,
            preview_buffer.tobytes(),
            content_type="image/jpeg",
            server_side_encryption=False,
        )

        _update_style_job_sync(
            SessionMaker, job_id, "processing", current_step="Adding final touches...", progress=85
        )
        self.update_state(
            state="PROGRESS",
            meta={"step": "Adding final touches...", "progress": 85, "job_id": job_id},
        )

        # Upload full result (JPEG quality 90)
        result_s3_key = f"styled/{user_id}/{job_id}.jpg"
        _, result_buffer = cv2.imencode(".jpg", full_result, [cv2.IMWRITE_JPEG_QUALITY, 90])
        s3_client.upload_file(
            result_s3_key,
            result_buffer.tobytes(),
            content_type="image/jpeg",
            server_side_encryption=False,
        )

        _update_style_job_sync(
            SessionMaker, job_id, "processing", current_step="Almost done...", progress=90
        )
        self.update_state(
            state="PROGRESS",
            meta={"step": "Almost done...", "progress": 90, "job_id": job_id},
        )

        # Step 4: Update job as completed (90-100%)
        processing_time_ms = int((time.time() - start_time) * 1000)
        result_height, result_width = full_result.shape[:2]

        _update_style_job_sync(
            SessionMaker,
            job_id,
            "completed",
            current_step="completed",
            progress=100,
            preview_s3_key=preview_s3_key,
            result_s3_key=result_s3_key,
            result_width=result_width,
            result_height=result_height,
            processing_time_ms=processing_time_ms,
        )

        logger.info(f"Style job {job_id} completed in {processing_time_ms}ms")
        return {
            "status": "completed",
            "job_id": job_id,
            "processing_time_ms": processing_time_ms,
        }

    except ValueError as e:
        # Quality/input issues
        logger.warning(f"Style job {job_id} failed with quality issue: {e}")
        _update_style_job_sync(
            SessionMaker,
            job_id,
            "failed",
            error_type="quality_issue",
            error_message=str(e),
        )
        raise

    except (ConnectionError, TimeoutError) as e:
        # Transient errors - let autoretry handle it
        logger.warning(f"Style job {job_id} transient error (attempt {self.request.retries}): {e}")
        if self.request.retries >= self.max_retries:
            _update_style_job_sync(
                SessionMaker,
                job_id,
                "failed",
                error_type="transient_error",
                error_message="Style processing timed out. Please try again.",
            )
        raise

    except RuntimeError as e:
        # Runtime errors (CUDA OOM, model crashes)
        logger.warning(f"Style job {job_id} runtime error (attempt {self.request.retries}): {e}")
        if self.request.retries >= self.max_retries:
            _update_style_job_sync(
                SessionMaker,
                job_id,
                "failed",
                error_type="server_error",
                error_message="Something went wrong during styling. Please try again later.",
            )
        raise

    except Exception as e:
        # Unexpected errors
        logger.error(f"Style job {job_id} failed with unexpected error: {e}", exc_info=True)
        _update_style_job_sync(
            SessionMaker,
            job_id,
            "failed",
            error_type="server_error",
            error_message="An unexpected error occurred.",
        )
        raise


def _update_style_job_sync(SessionMaker, job_id: str, status: str, **kwargs):
    """Update style job status using sync session.

    Args:
        SessionMaker: Sync session maker
        job_id: Job ID
        status: New status
        **kwargs: Additional fields to update
    """
    with SessionMaker() as db:
        job = db.query(StyleJob).filter(StyleJob.id == job_id).first()
        if job:
            job.status = status
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            db.commit()
