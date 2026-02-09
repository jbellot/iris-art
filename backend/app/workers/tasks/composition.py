"""Celery tasks for composition artwork creation using side-by-side layouts."""

import io
import logging
import time
from typing import List

import cv2
import numpy as np
from celery import Task

from app.core.db import get_sync_session_maker
from app.models.fusion_artwork import FusionArtwork
from app.storage.s3 import s3_client
from app.workers.celery_app import celery_app
from app.workers.tasks.fusion_blending import _load_best_source_image

logger = logging.getLogger(__name__)

# Maximum image dimension to prevent memory exhaustion
MAX_DIMENSION = 2048


class RetryableCompositionTask(Task):
    """Base task class with retry configuration for composition tasks."""

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
        logger.error(f"Composition {fusion_id} permanently failed: {type(exc).__name__}: {exc}")

        # Update fusion artwork status to failed
        with SessionMaker() as db:
            fusion = db.query(FusionArtwork).filter(FusionArtwork.id == fusion_id).first()
            if fusion:
                fusion.status = "failed"
                fusion.error_message = str(exc)[:500]  # Limit error message length
                db.commit()


@celery_app.task(
    bind=True,
    base=RetryableCompositionTask,
    name="app.workers.tasks.composition.create_composition",
    queue="default",
    time_limit=60,  # 1 minute hard limit (compositions are fast)
    soft_time_limit=50,  # 50 seconds soft limit
)
def create_composition(
    self, fusion_id: str, artwork_ids: List[str], layout: str = "horizontal"
):
    """Create composition artwork using side-by-side layouts.

    Args:
        fusion_id: FusionArtwork ID
        artwork_ids: List of photo IDs to compose
        layout: "horizontal", "vertical", or "grid_2x2"
    """
    start_time = time.time()
    SessionMaker = get_sync_session_maker()

    logger.info(f"Starting composition {fusion_id} with {len(artwork_ids)} artworks, layout={layout}")

    try:
        # Update status to processing
        with SessionMaker() as db:
            fusion = db.query(FusionArtwork).filter(FusionArtwork.id == fusion_id).first()
            if not fusion:
                raise ValueError(f"Fusion {fusion_id} not found")

            fusion.status = "processing"
            db.commit()

        self.update_state(state="PROGRESS", meta={"step": "loading", "progress": 10, "job_id": fusion_id})

        # Load source images (we don't need masks for composition)
        images = []

        with SessionMaker() as db:
            for i, artwork_id in enumerate(artwork_ids):
                logger.info(f"Loading image {i+1}/{len(artwork_ids)}: {artwork_id}")
                image, _ = _load_best_source_image(artwork_id, db)
                images.append(image)

                progress = 10 + int((i + 1) / len(artwork_ids) * 20)  # 10-30%
                self.update_state(state="PROGRESS", meta={"step": "loading", "progress": progress, "job_id": fusion_id})

        self.update_state(state="PROGRESS", meta={"step": "composing", "progress": 40, "job_id": fusion_id})

        # Determine target dimensions based on layout
        if layout == "horizontal":
            # Use minimum height to avoid quality loss
            target_height = min(img.shape[0] for img in images)
            target_height = min(target_height, MAX_DIMENSION)
            target_width = None  # Will be proportional

        elif layout == "vertical":
            # Use minimum width to avoid quality loss
            target_width = min(img.shape[1] for img in images)
            target_width = min(target_width, MAX_DIMENSION)
            target_height = None  # Will be proportional

        else:  # grid_2x2
            # Use minimum dimensions
            min_height = min(img.shape[0] for img in images)
            min_width = min(img.shape[1] for img in images)
            # Cap at MAX_DIMENSION
            scale = MAX_DIMENSION / max(min_height, min_width)
            if scale < 1:
                target_height = int(min_height * scale)
                target_width = int(min_width * scale)
            else:
                target_height = min_height
                target_width = min_width

        # Resize images
        resized_images = []

        for i, img in enumerate(images):
            if layout == "horizontal":
                # Resize to target height, maintain aspect ratio
                aspect = img.shape[1] / img.shape[0]
                new_width = int(target_height * aspect)
                img_resized = cv2.resize(img, (new_width, target_height), interpolation=cv2.INTER_LANCZOS4)

            elif layout == "vertical":
                # Resize to target width, maintain aspect ratio
                aspect = img.shape[0] / img.shape[1]
                new_height = int(target_width * aspect)
                img_resized = cv2.resize(img, (target_width, new_height), interpolation=cv2.INTER_LANCZOS4)

            else:  # grid_2x2
                # Resize to exact target dimensions
                img_resized = cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)

            resized_images.append(img_resized)

            progress = 40 + int((i + 1) / len(images) * 20)  # 40-60%
            self.update_state(state="PROGRESS", meta={"step": "composing", "progress": progress, "job_id": fusion_id})

        # Create composition based on layout
        if layout == "horizontal":
            # Concatenate horizontally
            result = cv2.hconcat(resized_images)

        elif layout == "vertical":
            # Concatenate vertically
            result = cv2.vconcat(resized_images)

        else:  # grid_2x2
            # Pad to 4 images if needed with black images
            while len(resized_images) < 4:
                black = np.zeros_like(resized_images[0])
                resized_images.append(black)

            # Create 2x2 grid
            top_row = cv2.hconcat([resized_images[0], resized_images[1]])
            bottom_row = cv2.hconcat([resized_images[2], resized_images[3]])
            result = cv2.vconcat([top_row, bottom_row])

        logger.info(f"Composition result dimensions: {result.shape[1]}x{result.shape[0]}")

        self.update_state(state="PROGRESS", meta={"step": "saving", "progress": 80, "job_id": fusion_id})

        # Generate thumbnail (256px wide, proportional height)
        thumb_width = 256
        aspect = result.shape[0] / result.shape[1]
        thumb_height = int(thumb_width * aspect)
        thumbnail = cv2.resize(result, (thumb_width, thumb_height), interpolation=cv2.INTER_AREA)
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

        logger.info(f"Composition {fusion_id} completed in {processing_time_ms}ms")
        return {"status": "completed", "fusion_id": fusion_id, "processing_time_ms": processing_time_ms}

    except Exception as e:
        logger.error(f"Composition {fusion_id} failed: {type(e).__name__}: {e}")
        # Update status to failed
        with SessionMaker() as db:
            fusion = db.query(FusionArtwork).filter(FusionArtwork.id == fusion_id).first()
            if fusion:
                fusion.status = "failed"
                fusion.error_message = str(e)[:500]
                db.commit()
        raise
