"""Celery tasks for fusion artwork creation using Poisson blending."""

import io
import logging
import time
from typing import List

import cv2
import numpy as np
from celery import Task
from PIL import Image

from app.core.db import get_sync_session_maker
from app.models.fusion_artwork import FusionArtwork
from app.models.photo import Photo
from app.models.processing_job import ProcessingJob
from app.models.style_job import StyleJob
from app.storage.s3 import s3_client
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# Maximum image dimension to prevent memory exhaustion
MAX_DIMENSION = 2048


class RetryableFusionTask(Task):
    """Base task class with retry configuration for fusion tasks."""

    autoretry_for = (ConnectionError, TimeoutError, RuntimeError)
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes max backoff
    retry_jitter = True
    max_retries = 1  # Auto-retry ONCE on transient failures

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task permanent failure - clean up and update status."""
        fusion_id = args[0] if args else kwargs.get("fusion_id")

        if not fusion_id:
            return

        SessionMaker = get_sync_session_maker()
        logger.error(f"Fusion {fusion_id} permanently failed: {type(exc).__name__}: {exc}")

        # Update fusion artwork status to failed
        with SessionMaker() as db:
            fusion = db.query(FusionArtwork).filter(FusionArtwork.id == fusion_id).first()
            if fusion:
                fusion.status = "failed"
                fusion.error_message = str(exc)[:500]  # Limit error message length
                db.commit()


def alpha_blend_fallback(base: np.ndarray, overlay: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Fallback alpha blending when Poisson blending fails.

    Args:
        base: Base image (numpy array)
        overlay: Overlay image (numpy array)
        mask: Binary mask (numpy array)

    Returns:
        Blended image
    """
    # Normalize mask to 0-1 float
    if mask.dtype != np.float32:
        mask = mask.astype(np.float32) / 255.0

    # Expand mask to 3 channels if needed
    if len(mask.shape) == 2:
        mask = np.stack([mask] * 3, axis=-1)

    # Ensure all images have same shape
    if base.shape != overlay.shape:
        overlay = cv2.resize(overlay, (base.shape[1], base.shape[0]))
    if mask.shape[:2] != base.shape[:2]:
        mask = cv2.resize(mask, (base.shape[1], base.shape[0]))
        if len(mask.shape) == 2:
            mask = np.stack([mask] * 3, axis=-1)

    # Alpha blend: result = base * (1 - alpha) + overlay * alpha
    result = (base * (1.0 - mask) + overlay * mask).astype(np.uint8)
    return result


def _load_best_source_image(photo_id: str, db) -> tuple[np.ndarray, np.ndarray]:
    """Load the best available processed image and mask for a photo.

    Priority: StyleJob result > ProcessingJob result
    Returns tuple of (image, mask) as numpy arrays.

    Args:
        photo_id: Photo ID
        db: Sync database session

    Returns:
        Tuple of (image array, mask array)

    Raises:
        ValueError: If no processed image found
    """
    # Try StyleJob first (highest quality)
    style_job = (
        db.query(StyleJob)
        .filter(StyleJob.photo_id == photo_id, StyleJob.status == "completed")
        .order_by(StyleJob.created_at.desc())
        .first()
    )

    if style_job and style_job.result_s3_key:
        image_bytes = s3_client.download_file(style_job.result_s3_key)
        image_array = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        # Get mask from processing job
        processing_job = (
            db.query(ProcessingJob)
            .filter(ProcessingJob.id == style_job.processing_job_id)
            .first()
        )
        if processing_job and processing_job.mask_s3_key:
            mask_bytes = s3_client.download_file(processing_job.mask_s3_key)
            mask_array = np.frombuffer(mask_bytes, np.uint8)
            mask = cv2.imdecode(mask_array, cv2.IMREAD_GRAYSCALE)
            return image, mask

    # Try ProcessingJob
    processing_job = (
        db.query(ProcessingJob)
        .filter(ProcessingJob.photo_id == photo_id, ProcessingJob.status == "completed")
        .order_by(ProcessingJob.created_at.desc())
        .first()
    )

    if processing_job and processing_job.result_s3_key:
        image_bytes = s3_client.download_file(processing_job.result_s3_key)
        image_array = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if processing_job.mask_s3_key:
            mask_bytes = s3_client.download_file(processing_job.mask_s3_key)
            mask_array = np.frombuffer(mask_bytes, np.uint8)
            mask = cv2.imdecode(mask_array, cv2.IMREAD_GRAYSCALE)
            return image, mask

    # No processed image found
    raise ValueError(f"No processed image found for photo {photo_id}")


@celery_app.task(
    bind=True,
    base=RetryableFusionTask,
    name="app.workers.tasks.fusion_blending.create_fusion_artwork",
    queue="default",
    time_limit=180,  # 3 minutes hard limit
    soft_time_limit=150,  # 2.5 minutes soft limit
)
def create_fusion_artwork(
    self, fusion_id: str, artwork_ids: List[str], blend_mode: str = "poisson"
):
    """Create fusion artwork using Poisson blending or alpha blending.

    Args:
        fusion_id: FusionArtwork ID
        artwork_ids: List of photo IDs to blend
        blend_mode: "poisson" or "alpha"
    """
    start_time = time.time()
    SessionMaker = get_sync_session_maker()

    logger.info(f"Starting fusion {fusion_id} with {len(artwork_ids)} artworks, mode={blend_mode}")

    try:
        # Update status to processing
        with SessionMaker() as db:
            fusion = db.query(FusionArtwork).filter(FusionArtwork.id == fusion_id).first()
            if not fusion:
                raise ValueError(f"Fusion {fusion_id} not found")

            fusion.status = "processing"
            db.commit()

        self.update_state(state="PROGRESS", meta={"step": "loading", "progress": 10, "job_id": fusion_id})

        # Load source images and masks
        images = []
        masks = []

        with SessionMaker() as db:
            for i, artwork_id in enumerate(artwork_ids):
                logger.info(f"Loading image {i+1}/{len(artwork_ids)}: {artwork_id}")
                image, mask = _load_best_source_image(artwork_id, db)
                images.append(image)
                masks.append(mask)

                progress = 10 + int((i + 1) / len(artwork_ids) * 10)  # 10-20%
                self.update_state(state="PROGRESS", meta={"step": "loading", "progress": progress, "job_id": fusion_id})

        # Determine target dimensions (use largest, capped at MAX_DIMENSION)
        max_height = max(img.shape[0] for img in images)
        max_width = max(img.shape[1] for img in images)

        # Cap at MAX_DIMENSION
        if max_height > MAX_DIMENSION or max_width > MAX_DIMENSION:
            scale = MAX_DIMENSION / max(max_height, max_width)
            target_height = int(max_height * scale)
            target_width = int(max_width * scale)
        else:
            target_height = max_height
            target_width = max_width

        logger.info(f"Target dimensions: {target_width}x{target_height}")

        # Resize all images and masks to target dimensions
        resized_images = []
        resized_masks = []

        for i, (img, mask) in enumerate(zip(images, masks)):
            if img.shape[:2] != (target_height, target_width):
                img_resized = cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
            else:
                img_resized = img

            if mask.shape[:2] != (target_height, target_width):
                mask_resized = cv2.resize(mask, (target_width, target_height), interpolation=cv2.INTER_LINEAR)
            else:
                mask_resized = mask

            resized_images.append(img_resized)
            resized_masks.append(mask_resized)

        self.update_state(state="PROGRESS", meta={"step": "blending", "progress": 30, "job_id": fusion_id})

        # Apply Gaussian blur to mask edges for smoother blending
        smoothed_masks = []
        for mask in resized_masks:
            # Apply Gaussian blur (kernel size 5x5)
            smoothed = cv2.GaussianBlur(mask, (5, 5), 0)
            smoothed_masks.append(smoothed)

        # Blend images
        result = resized_images[0].copy()

        for i in range(1, len(resized_images)):
            logger.info(f"Blending image {i+1}/{len(resized_images)}")

            overlay = resized_images[i]
            mask = smoothed_masks[i]

            # Calculate mask center for Poisson blending
            mask_moments = cv2.moments(mask)
            if mask_moments["m00"] > 0:
                center_x = int(mask_moments["m10"] / mask_moments["m00"])
                center_y = int(mask_moments["m01"] / mask_moments["m00"])
                center = (center_x, center_y)
            else:
                center = (target_width // 2, target_height // 2)

            if blend_mode == "poisson":
                try:
                    # Try Poisson blending
                    result = cv2.seamlessClone(
                        overlay, result, mask, center, cv2.MIXED_CLONE
                    )
                    logger.info(f"Poisson blend {i} successful")
                except cv2.error as e:
                    # Fallback to alpha blending
                    logger.warning(f"Poisson blend {i} failed: {e}. Falling back to alpha blend.")
                    result = alpha_blend_fallback(result, overlay, mask)
            else:
                # Direct alpha blending
                result = alpha_blend_fallback(result, overlay, mask)

            progress = 30 + int(i / (len(resized_images) - 1) * 50)  # 30-80%
            self.update_state(state="PROGRESS", meta={"step": "blending", "progress": progress, "job_id": fusion_id})

        self.update_state(state="PROGRESS", meta={"step": "saving", "progress": 90, "job_id": fusion_id})

        # Generate thumbnail (256x256)
        thumbnail = cv2.resize(result, (256, 256), interpolation=cv2.INTER_AREA)
        _, thumb_buffer = cv2.imencode(".jpg", thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 70])
        thumbnail_s3_key = f"fusion/{fusion_id}_thumb.jpg"
        s3_client.upload_file(
            thumbnail_s3_key,
            thumb_buffer.tobytes(),
            content_type="image/jpeg",
            server_side_encryption=False,
        )

        # Save full result as JPEG
        _, result_buffer = cv2.imencode(".jpg", result, [cv2.IMWRITE_JPEG_QUALITY, 90])
        result_s3_key = f"fusion/{fusion_id}.jpg"
        s3_client.upload_file(
            result_s3_key,
            result_buffer.tobytes(),
            content_type="image/jpeg",
            server_side_encryption=False,
        )

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Update fusion artwork as completed
        with SessionMaker() as db:
            fusion = db.query(FusionArtwork).filter(FusionArtwork.id == fusion_id).first()
            if fusion:
                fusion.status = "completed"
                fusion.result_s3_key = result_s3_key
                fusion.thumbnail_s3_key = thumbnail_s3_key
                fusion.processing_time_ms = processing_time_ms
                from datetime import datetime, timezone
                fusion.completed_at = datetime.now(timezone.utc)
                db.commit()

        logger.info(f"Fusion {fusion_id} completed in {processing_time_ms}ms")
        return {"status": "completed", "fusion_id": fusion_id, "processing_time_ms": processing_time_ms}

    except Exception as e:
        logger.error(f"Fusion {fusion_id} failed: {type(e).__name__}: {e}")
        # Update status to failed
        with SessionMaker() as db:
            fusion = db.query(FusionArtwork).filter(FusionArtwork.id == fusion_id).first()
            if fusion:
                fusion.status = "failed"
                fusion.error_message = str(e)[:500]
                db.commit()
        raise
