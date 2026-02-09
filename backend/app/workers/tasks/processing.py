"""Celery tasks for AI iris processing pipeline."""

import io
import logging
import time
from typing import Optional

import cv2
import numpy as np
from celery import Task
from PIL import Image

from app.core.db import get_sync_session_maker
from app.models.processing_job import ProcessingJob
from app.storage.s3 import s3_client
from app.workers.celery_app import celery_app
from app.workers.models.enhancement_model import enhance_iris
from app.workers.models.reflection_model import remove_reflections
from app.workers.models.segmentation_model import segment_iris

logger = logging.getLogger(__name__)


class RetryableProcessingTask(Task):
    """Base task class with retry configuration for processing tasks."""

    autoretry_for = (ConnectionError, TimeoutError, RuntimeError)
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes max backoff
    retry_jitter = True
    max_retries = 1  # Auto-retry ONCE on transient failures


@celery_app.task(bind=True, base=RetryableProcessingTask, name="app.workers.tasks.processing.process_iris_pipeline")
def process_iris_pipeline(self, job_id: str, photo_id: str, user_id: str):
    """Process iris image through complete AI pipeline.

    Pipeline steps:
    1. Load original image from S3
    2. Segment iris
    3. Remove reflections
    4. Enhance with super-resolution
    5. Save results to S3

    Args:
        job_id: ProcessingJob ID
        photo_id: Photo ID to process
        user_id: User ID
    """
    start_time = time.time()
    SessionMaker = get_sync_session_maker()

    logger.info(f"Starting processing pipeline for job {job_id}")

    try:
        # Step 1: Load image from S3 (0-10%)
        _update_job_sync(SessionMaker, job_id, "processing", current_step="loading", progress=5)
        self.update_state(state="PROGRESS", meta={"step": "loading", "progress": 5})

        with SessionMaker() as db:
            from app.models.photo import Photo
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if not photo:
                raise ValueError("Photo not found")

            # Download from S3
            image_bytes = s3_client.download_file(photo.s3_key)

        # Convert to OpenCV format
        image_array = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Failed to decode image")

        _update_job_sync(SessionMaker, job_id, "processing", current_step="loading", progress=10)

        # Step 2: Segment iris (10-40%)
        logger.info(f"Job {job_id}: Running segmentation")
        _update_job_sync(SessionMaker, job_id, "processing", current_step="segmenting", progress=20)
        self.update_state(state="PROGRESS", meta={"step": "segmenting", "progress": 20})

        segmented_image, mask = segment_iris(image)

        _update_job_sync(SessionMaker, job_id, "processing", current_step="segmenting", progress=40)

        # Step 3: Remove reflections (40-60%)
        logger.info(f"Job {job_id}: Removing reflections")
        _update_job_sync(SessionMaker, job_id, "processing", current_step="removing_reflections", progress=50)
        self.update_state(state="PROGRESS", meta={"step": "removing_reflections", "progress": 50})

        reflection_removed = remove_reflections(segmented_image, mask)

        _update_job_sync(SessionMaker, job_id, "processing", current_step="removing_reflections", progress=60)

        # Step 4: Enhance (60-90%)
        logger.info(f"Job {job_id}: Enhancing image")
        _update_job_sync(SessionMaker, job_id, "processing", current_step="enhancing", progress=70)
        self.update_state(state="PROGRESS", meta={"step": "enhancing", "progress": 70})

        enhanced_image = enhance_iris(reflection_removed, scale=4)

        _update_job_sync(SessionMaker, job_id, "processing", current_step="enhancing", progress=90)

        # Step 5: Save results to S3 (90-100%)
        logger.info(f"Job {job_id}: Saving results")
        _update_job_sync(SessionMaker, job_id, "processing", current_step="saving", progress=95)
        self.update_state(state="PROGRESS", meta={"step": "saving", "progress": 95})

        # Save processed image
        result_s3_key = f"processed/{user_id}/{job_id}.jpg"
        _, buffer = cv2.imencode(".jpg", enhanced_image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        s3_client.upload_file(result_s3_key, buffer.tobytes(), content_type="image/jpeg", server_side_encryption=False)

        # Save mask
        mask_s3_key = f"processed/{user_id}/{job_id}_mask.png"
        _, mask_buffer = cv2.imencode(".png", mask)
        s3_client.upload_file(mask_s3_key, mask_buffer.tobytes(), content_type="image/png", server_side_encryption=False)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Update job as completed
        result_height, result_width = enhanced_image.shape[:2]
        _update_job_sync(
            SessionMaker,
            job_id,
            "completed",
            current_step="completed",
            progress=100,
            result_s3_key=result_s3_key,
            mask_s3_key=mask_s3_key,
            result_width=result_width,
            result_height=result_height,
            processing_time_ms=processing_time_ms,
        )

        logger.info(f"Job {job_id} completed in {processing_time_ms}ms")
        return {"status": "completed", "job_id": job_id, "processing_time_ms": processing_time_ms}

    except ValueError as e:
        # Quality issues - user-facing error
        logger.warning(f"Job {job_id} failed with quality issue: {e}")
        _update_job_sync(
            SessionMaker,
            job_id,
            "failed",
            error_type="quality_issue",
            error_message=str(e),
            suggestion="Try capturing a new photo in better lighting with your eye centered.",
        )
        raise

    except (ConnectionError, TimeoutError) as e:
        # Transient errors - let autoretry handle it
        logger.warning(f"Job {job_id} transient error (attempt {self.request.retries}): {e}")
        # On final retry failure, update job
        if self.request.retries >= self.max_retries:
            _update_job_sync(
                SessionMaker,
                job_id,
                "failed",
                error_type="transient_error",
                error_message="Processing timed out. Please try again.",
                suggestion="Check your internet connection and try again.",
            )
        raise

    except Exception as e:
        # Server errors
        logger.error(f"Job {job_id} failed with server error: {e}", exc_info=True)
        _update_job_sync(
            SessionMaker,
            job_id,
            "failed",
            error_type="server_error",
            error_message="Something went wrong. Please try again later.",
            suggestion="If the problem persists, contact support.",
        )
        raise


def _update_job_sync(SessionMaker, job_id: str, status: str, **kwargs):
    """Update job status using sync session.

    Args:
        SessionMaker: Sync session maker
        job_id: Job ID
        status: New status
        **kwargs: Additional fields to update
    """
    with SessionMaker() as db:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.status = status
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            db.commit()
