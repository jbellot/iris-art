"""Celery tasks for AI-unique art generation using Stable Diffusion."""

import io
import logging
import time

import cv2
import numpy as np
from celery import Task
from PIL import Image

from app.core.db import get_sync_session_maker
from app.models.style_job import StyleJob
from app.storage.s3 import s3_client
from app.workers.celery_app import celery_app
from app.workers.models.model_cache import ModelCache

logger = logging.getLogger(__name__)


class RetryableAIGenerationTask(Task):
    """Base task class with retry configuration for AI generation tasks."""

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
        logger.error(f"AI generation job {job_id} permanently failed: {type(exc).__name__}: {exc}")

        # Clean up partial S3 objects
        if user_id:
            try:
                preview_s3_key = f"ai_art/{user_id}/{job_id}_preview.jpg"
                result_s3_key = f"ai_art/{user_id}/{job_id}.jpg"

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
                logger.warning(f"Error during S3 cleanup for AI job {job_id}: {e}")

        # Error classification
        if isinstance(exc, ValueError):
            # Quality issues
            _update_style_job_sync(
                SessionMaker,
                job_id,
                "failed",
                error_type="quality_issue",
                error_message=str(exc),
            )
        elif isinstance(exc, (ConnectionError, TimeoutError)):
            _update_style_job_sync(
                SessionMaker,
                job_id,
                "failed",
                error_type="transient_error",
                error_message="AI generation timed out. Please try again.",
            )
        elif isinstance(exc, RuntimeError):
            _update_style_job_sync(
                SessionMaker,
                job_id,
                "failed",
                error_type="server_error",
                error_message="Something went wrong during generation. Please try again later.",
            )
        else:
            _update_style_job_sync(
                SessionMaker,
                job_id,
                "failed",
                error_type="server_error",
                error_message="An unexpected error occurred.",
            )


@celery_app.task(
    bind=True,
    base=RetryableAIGenerationTask,
    name="app.workers.tasks.ai_generation.generate_ai_art"
)
def generate_ai_art(
    self,
    job_id: str,
    user_id: str,
    photo_id: str,
    processing_job_id: str,
    prompt: str = None,
    style_hint: str = None,
):
    """Generate AI-unique artistic composition from iris patterns.

    Uses SDXL Turbo with ControlNet edge guidance from iris features.
    Reuses StyleJob model with style_preset_id=NULL to indicate AI generation.

    Args:
        job_id: StyleJob ID
        user_id: User ID
        photo_id: Photo ID
        processing_job_id: ProcessingJob ID (processed iris image)
        prompt: Optional user prompt (default: auto-generated from iris)
        style_hint: Optional style hint (cosmic, abstract, watercolor, etc.)

    Pipeline steps:
        1. Load processed iris from S3
        2. Extract iris edges and colors with ControlNet processor
        3. Generate art with SDXL Turbo
        4. Save preview (256px) and full-res (1024px) to S3
        5. Update StyleJob with results
    """
    start_time = time.time()
    SessionMaker = get_sync_session_maker()

    logger.info(f"Starting AI generation for job {job_id}")

    try:
        # Step 1: Load processed iris (0-10%)
        _update_style_job_sync(
            SessionMaker, job_id, "processing", current_step="Reading your iris patterns...", progress=5
        )
        self.update_state(
            state="PROGRESS",
            meta={"step": "Reading your iris patterns...", "progress": 5, "job_id": job_id},
        )

        # Get processing job to find processed iris S3 key
        from app.models.processing_job import ProcessingJob

        with SessionMaker() as db:
            processing_job = db.query(ProcessingJob).filter(ProcessingJob.id == processing_job_id).first()
            if not processing_job or not processing_job.result_s3_key:
                raise ValueError("Processed iris not found")

            iris_s3_key = processing_job.result_s3_key

        # Download processed iris from S3
        image_bytes = s3_client.download_file(iris_s3_key)
        image_array = np.frombuffer(image_bytes, np.uint8)
        iris_cv = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if iris_cv is None:
            raise ValueError("Failed to decode processed iris image")

        # Convert to PIL for diffusers
        iris_rgb = cv2.cvtColor(iris_cv, cv2.COLOR_BGR2RGB)
        iris_pil = Image.fromarray(iris_rgb)

        _update_style_job_sync(
            SessionMaker, job_id, "processing", current_step="Reading your iris patterns...", progress=10
        )
        self.update_state(
            state="PROGRESS",
            meta={"step": "Reading your iris patterns...", "progress": 10, "job_id": job_id},
        )

        # Step 2: Extract unique iris features (10-25%)
        logger.info(f"Job {job_id}: Extracting iris features")
        _update_style_job_sync(
            SessionMaker, job_id, "processing", current_step="Extracting unique features...", progress=15
        )
        self.update_state(
            state="PROGRESS",
            meta={"step": "Extracting unique features...", "progress": 15, "job_id": job_id},
        )

        # Load ControlNet processor
        controlnet = ModelCache.get_controlnet_processor()

        # Extract iris edges for ControlNet guidance
        edge_map = controlnet.extract_iris_edges(iris_pil)

        # Extract dominant colors for prompt enhancement
        color_map = controlnet.extract_color_map(iris_pil)

        _update_style_job_sync(
            SessionMaker, job_id, "processing", current_step="Extracting unique features...", progress=25
        )
        self.update_state(
            state="PROGRESS",
            meta={"step": "Extracting unique features...", "progress": 25, "job_id": job_id},
        )

        # Step 3: Generate AI art (25-75%)
        logger.info(f"Job {job_id}: Generating AI art")
        _update_style_job_sync(
            SessionMaker, job_id, "processing", current_step="Imagining your artwork...", progress=30
        )
        self.update_state(
            state="PROGRESS",
            meta={"step": "Imagining your artwork...", "progress": 30, "job_id": job_id},
        )

        # Build prompt
        if not prompt:
            # Auto-generate prompt from style hint
            style_descriptor = style_hint if style_hint else "artistic"
            prompt = (
                f"A stunning {style_descriptor} composition inspired by the intricate patterns "
                f"and colors of a human iris, highly detailed, masterpiece quality, "
                f"professional art, vibrant colors, unique abstract design"
            )

        logger.info(f"Job {job_id}: Using prompt: {prompt[:100]}...")

        # Load SDXL Turbo generator
        sd_generator = ModelCache.get_sd_generator()

        _update_style_job_sync(
            SessionMaker, job_id, "processing", current_step="Imagining your artwork...", progress=40
        )
        self.update_state(
            state="PROGRESS",
            meta={"step": "Imagining your artwork...", "progress": 40, "job_id": job_id},
        )

        # Generate full-res art (1024x1024)
        generated_art = sd_generator.generate(
            iris_image=iris_pil,
            prompt=prompt,
            control_image=edge_map,
            num_steps=4,
            strength=0.8,
        )

        _update_style_job_sync(
            SessionMaker, job_id, "processing", current_step="Imagining your artwork...", progress=75
        )
        self.update_state(
            state="PROGRESS",
            meta={"step": "Imagining your artwork...", "progress": 75, "job_id": job_id},
        )

        # Step 4: Save results (75-90%)
        logger.info(f"Job {job_id}: Saving generated art")
        _update_style_job_sync(
            SessionMaker, job_id, "processing", current_step="Refining the details...", progress=80
        )
        self.update_state(
            state="PROGRESS",
            meta={"step": "Refining the details...", "progress": 80, "job_id": job_id},
        )

        # Generate preview (256x256)
        preview_pil = generated_art.resize((256, 256), Image.LANCZOS)

        # Save preview to buffer
        preview_buffer = io.BytesIO()
        preview_pil.save(preview_buffer, format="JPEG", quality=70)
        preview_bytes = preview_buffer.getvalue()

        # Upload preview to S3
        preview_s3_key = f"ai_art/{user_id}/{job_id}_preview.jpg"
        s3_client.upload_file(
            preview_s3_key,
            preview_bytes,
            content_type="image/jpeg",
            server_side_encryption=False,
        )

        _update_style_job_sync(
            SessionMaker, job_id, "processing", current_step="Refining the details...", progress=85
        )
        self.update_state(
            state="PROGRESS",
            meta={"step": "Refining the details...", "progress": 85, "job_id": job_id},
        )

        # Save full-res result (1024x1024)
        result_buffer = io.BytesIO()
        generated_art.save(result_buffer, format="JPEG", quality=90)
        result_bytes = result_buffer.getvalue()

        result_s3_key = f"ai_art/{user_id}/{job_id}.jpg"
        s3_client.upload_file(
            result_s3_key,
            result_bytes,
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

        # Step 5: Update job as completed (90-100%)
        processing_time_ms = int((time.time() - start_time) * 1000)
        result_width, result_height = generated_art.size

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

        logger.info(f"AI generation job {job_id} completed in {processing_time_ms}ms")
        return {
            "status": "completed",
            "job_id": job_id,
            "processing_time_ms": processing_time_ms,
        }

    except ValueError as e:
        # Quality/input issues
        logger.warning(f"AI generation job {job_id} failed with quality issue: {e}")
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
        logger.warning(f"AI generation job {job_id} transient error (attempt {self.request.retries}): {e}")
        if self.request.retries >= self.max_retries:
            _update_style_job_sync(
                SessionMaker,
                job_id,
                "failed",
                error_type="transient_error",
                error_message="AI generation timed out. Please try again.",
            )
        raise

    except RuntimeError as e:
        # Runtime errors (CUDA OOM, model crashes)
        logger.warning(f"AI generation job {job_id} runtime error (attempt {self.request.retries}): {e}")
        if self.request.retries >= self.max_retries:
            _update_style_job_sync(
                SessionMaker,
                job_id,
                "failed",
                error_type="server_error",
                error_message="Something went wrong during generation. Please try again later.",
            )
        raise

    except Exception as e:
        # Unexpected errors
        logger.error(f"AI generation job {job_id} failed with unexpected error: {e}", exc_info=True)
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
