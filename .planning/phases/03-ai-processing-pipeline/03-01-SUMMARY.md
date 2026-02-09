---
phase: 03-ai-processing-pipeline
plan: 01
subsystem: backend-ai-processing
tags: [ai, celery, pipeline, onnx, image-processing]
dependency-graph:
  requires: [photos-api, celery-worker, s3-storage]
  provides: [processing-api, ai-pipeline, model-cache]
  affects: [celery-queues, db-schema]
tech-stack:
  added: [onnxruntime, opencv-python-headless, torch, numpy, pillow, scikit-image]
  patterns: [singleton-cache, lazy-loading, retry-pattern, priority-queues, dev-fallbacks]
key-files:
  created:
    - backend/app/models/processing_job.py
    - backend/app/schemas/processing.py
    - backend/app/services/processing.py
    - backend/app/workers/models/model_cache.py
    - backend/app/workers/models/segmentation_model.py
    - backend/app/workers/models/reflection_model.py
    - backend/app/workers/models/enhancement_model.py
    - backend/app/workers/tasks/processing.py
    - backend/app/api/routes/processing.py
  modified:
    - backend/app/models/user.py
    - backend/app/models/photo.py
    - backend/app/core/db.py
    - backend/app/workers/celery_app.py
    - backend/app/main.py
    - backend/docker-compose.yml
    - backend/requirements.txt
decisions:
  - "Use sync SQLAlchemy session for Celery workers (psycopg2 instead of asyncpg)"
  - "Implement dev-mode fallbacks: simulated circular mask for segmentation, OpenCV Lanczos for enhancement"
  - "MVP reflection removal uses OpenCV inpainting (can upgrade to LapCAT later)"
  - "Singleton ModelCache with lazy loading prevents repeated model loads"
  - "Priority queues: high_priority for user jobs, default for background tasks"
  - "Auto-retry once on transient errors (ConnectionError, TimeoutError)"
  - "Error classification: quality_issue, transient_error, server_error"
  - "Celery prefetch-multiplier=1 to prevent AI task queue buildup in worker memory"
metrics:
  duration: 8min
  tasks-completed: 2
  files-created: 9
  files-modified: 8
  commits: 2
  completed-date: 2026-02-09
---

# Phase 03 Plan 01: AI Processing Pipeline Infrastructure Summary

**One-liner:** Complete backend AI processing pipeline with ProcessingJob model, model cache singleton, segmentation/reflection/enhancement pipeline, Celery tasks with priority queues, and REST API endpoints.

## What Was Built

### Task 1: ProcessingJob Model, Schemas, Service, and Migration
**Commit:** 4fe2c65

Created the database and service layer for tracking AI processing jobs:

- **ProcessingJob Model**: SQLAlchemy model with status/step tracking, progress (0-100), error classification (quality_issue/transient_error/server_error), result S3 keys, processing metrics
- **Pydantic Schemas**: JobSubmitRequest, BatchJobSubmitRequest (max 10), JobResponse, JobStatusResponse with presigned URLs
- **Processing Service**: CRUD operations (create, get, list, update_status), presigned URL generation for results
- **Sync DB Support**: Added lazy-loading sync session maker for Celery workers (psycopg2)
- **Database Migration**: Alembic migration for processing_jobs table with user/photo foreign keys
- **Model Relationships**: Updated User and Photo models with processing_jobs back_populates
- **Dependencies**: Added AI/ML packages (torch, onnxruntime, opencv, numpy, pillow, scikit-image, psycopg2-binary)

### Task 2: AI Model Infrastructure, Celery Pipeline, and Processing API
**Commit:** 24ac831

Built the complete AI processing pipeline infrastructure:

**Model Infrastructure:**
- **ModelCache**: Singleton with lazy loading for ONNX segmentation, Real-ESRGAN enhancement, reflection models
- **Segmentation Model**: ONNX inference with 512x512 resize, or simulated circular mask for dev mode
- **Reflection Removal**: OpenCV inpainting on detected highlights (MVP approach, upgradeable to LapCAT)
- **Enhancement Model**: CLAHE contrast adjustment + Lanczos 4x upscaling fallback

**Celery Pipeline:**
- **RetryableProcessingTask**: Base task with auto-retry config (max_retries=1, exponential backoff)
- **process_iris_pipeline**: Single orchestrator task with 5 steps (load, segment, reflect, enhance, save)
- **Progress Tracking**: Updates job at each step with progress percentage and current_step
- **Error Handling**: Classifies errors (quality issues vs transient vs server), provides user-friendly messages and suggestions
- **S3 Results**: Saves processed image and mask to `processed/{user_id}/{job_id}.{jpg|png}`

**Priority Queues:**
- **Queue Configuration**: high_priority and default queues with routing
- **Worker Setup**: Celery worker consumes both queues with prefetch-multiplier=1
- **Task Routing**: process_iris_pipeline routed to high_priority automatically

**Processing API:**
- **POST /api/v1/processing/submit**: Single job submission
- **POST /api/v1/processing/batch**: Batch submission (up to 10 photos) with priority ordering
- **GET /api/v1/processing/jobs/{job_id}**: Full job status with presigned URLs
- **GET /api/v1/processing/jobs**: Paginated list of user's jobs
- **POST /api/v1/processing/jobs/{job_id}/reprocess**: Create new job for same photo

**Docker & Configuration:**
- Updated docker-compose.yml with model weights volume mount
- Added .gitignore patterns for model weights (*.onnx, *.pth, *.pt)
- Created weights directory with .gitkeep

## Deviations from Plan

None - plan executed exactly as written.

All dev-mode fallbacks (simulated segmentation, OpenCV enhancement) were specified in the plan as graceful degradation for environments without model weights.

## Technical Highlights

### Dev-Mode Fallbacks
All AI models gracefully degrade when weights are missing:
- Segmentation: Uses simulated circular mask (still validates 5% coverage)
- Enhancement: Uses CLAHE + Lanczos instead of Real-ESRGAN
- Reflection: Always uses OpenCV inpainting (MVP approach)

This allows full pipeline testing without downloading large model files.

### Error Classification Strategy
Three error types guide user action:
- **quality_issue**: "Try capturing a new photo in better lighting" (user action)
- **transient_error**: "Check your internet connection and try again" (retry)
- **server_error**: "If the problem persists, contact support" (escalate)

### Singleton Model Cache
Models loaded once at worker startup (or first use) via class-level variables:
- Prevents repeated model loads per task
- Logs which execution provider is used (CUDA vs CPU)
- Lazy loading only when needed

### Priority Queue Design
User-initiated jobs run on high_priority queue:
- Ensures responsive processing for interactive use
- Batch jobs ordered by submission (first photo = highest priority)
- Prefetch=1 prevents memory buildup from queued AI tasks

## Verification Results

All imports verified:
```bash
✓ ProcessingJob model imports
✓ Processing schemas import
✓ Processing service imports
✓ ModelCache imports
✓ Segmentation model imports
✓ Reflection model imports
✓ Enhancement model imports
✓ Pipeline task imports
✓ Processing router imports
```

Configuration verified:
```bash
✓ Processing router registered in main.py
✓ Priority queue configured in celery_app.py
✓ Worker command includes both queues in docker-compose.yml
```

Database migration applied:
```bash
✓ Alembic migration generated
✓ processing_jobs table created in PostgreSQL
```

## Pipeline Flow

```
1. POST /api/v1/processing/submit (photo_id)
   ↓
2. Create ProcessingJob record (status=pending)
   ↓
3. Submit process_iris_pipeline.apply_async(queue='high_priority')
   ↓
4. Celery worker executes pipeline:
   - Load image from S3 (progress 0-10%)
   - Segment iris (10-40%)
   - Remove reflections (40-60%)
   - Enhance 4x (60-90%)
   - Save to S3 (90-100%)
   ↓
5. Update job: status=completed, result_s3_key, mask_s3_key, processing_time_ms
   ↓
6. GET /api/v1/processing/jobs/{job_id} returns presigned URLs
```

## Next Steps

**Immediate (Phase 3 continuation):**
- Add WebSocket support for real-time progress updates
- Implement mobile UI for job submission and status polling
- Add result gallery view with before/after comparison

**Future enhancements:**
- Download and integrate real ONNX segmentation model
- Upgrade to Real-ESRGAN for production enhancement
- Consider LapCAT transformer for reflection removal
- Add quality scoring algorithm
- Implement result caching strategy

## Self-Check: PASSED

**Created files verified:**
```bash
✓ backend/app/models/processing_job.py
✓ backend/app/schemas/processing.py
✓ backend/app/services/processing.py
✓ backend/app/workers/models/__init__.py
✓ backend/app/workers/models/model_cache.py
✓ backend/app/workers/models/segmentation_model.py
✓ backend/app/workers/models/reflection_model.py
✓ backend/app/workers/models/enhancement_model.py
✓ backend/app/workers/tasks/processing.py
✓ backend/app/api/routes/processing.py
✓ backend/app/workers/models/weights/.gitkeep
```

**Commits verified:**
```bash
✓ 4fe2c65: feat(03-01): add ProcessingJob model, schemas, service, and migration
✓ 24ac831: feat(03-01): add AI model infrastructure, Celery pipeline, and processing API
```

All claimed artifacts exist and are committed to version control.
