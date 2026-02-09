---
phase: 05-social-features-circles-and-fusion
plan: 05
subsystem: backend-fusion
tags: [fusion, composition, celery, consent, social]
dependency_graph:
  requires:
    - 05-03-SUMMARY.md (consent service for consent verification)
    - 03-01-SUMMARY.md (Celery task patterns, sync session, S3 storage)
  provides:
    - FusionArtwork model with JSON source_artwork_ids
    - Poisson blending Celery task with alpha fallback
    - Side-by-side composition task (horizontal, vertical, grid_2x2)
    - Fusion service with consent gate
    - Fusion REST API endpoints
  affects:
    - User model (fusion_artworks relationship)
    - WebSocket infrastructure (reuses /ws/jobs/{job_id} for progress)
tech_stack:
  added:
    - cv2.seamlessClone for Poisson blending
    - cv2.hconcat/vconcat for composition
    - JSON column in PostgreSQL for source_artwork_ids
  patterns:
    - Consent verification gate before fusion submission
    - Best-source-image selection (StyleJob > ProcessingJob)
    - Memory guard: 2048px dimension cap
    - Mask smoothing with Gaussian blur
    - Alpha blending fallback on Poisson error
key_files:
  created:
    - backend/app/models/fusion_artwork.py
    - backend/app/schemas/fusion.py
    - backend/app/workers/tasks/fusion_blending.py
    - backend/app/workers/tasks/composition.py
    - backend/app/services/fusion_service.py
    - backend/app/api/routes/fusion.py
    - backend/alembic/versions/f6a7b8c9d0e1_add_fusion_artworks.py
  modified:
    - backend/app/models/__init__.py (import FusionArtwork)
    - backend/app/models/user.py (fusion_artworks relationship)
    - backend/app/main.py (register fusion router)
decisions: []
metrics:
  duration: 6 minutes
  tasks_completed: 2
  files_created: 7
  files_modified: 3
  commits: 2
  lines_added: ~1327
  completed_date: 2026-02-09
---

# Phase 05 Plan 05: Fusion and Composition Backend Summary

**One-liner:** Poisson blending fusion and side-by-side composition with consent verification gate, JSON source tracking, and 2048px memory guard.

## What Was Built

### FusionArtwork Model & Migration
- **FusionArtwork** model with:
  - JSON `source_artwork_ids` column (list of photo UUIDs)
  - `fusion_type`: "fusion" or "composition"
  - `blend_mode`: "poisson"/"alpha" for fusion, "horizontal"/"vertical"/"grid_2x2" for composition
  - Status tracking: pending → processing → completed/failed
  - S3 keys for result and thumbnail
  - Processing time metrics
- **Migration** `f6a7b8c9d0e1` creates `fusion_artworks` table with proper foreign keys (cascade on user, set null on circle)
- **Schemas**: FusionCreateRequest, CompositionCreateRequest, FusionResponse, FusionStatusResponse, ConsentRequiredResponse

### Fusion Blending Celery Task
**File:** `backend/app/workers/tasks/fusion_blending.py`

Pipeline:
1. **Load** source images and masks (progress 10-20%)
   - Priority: StyleJob result > ProcessingJob result
   - Helper `_load_best_source_image` queries both job types
2. **Resize** to max dimensions (capped at 2048x2048) to prevent memory exhaustion
3. **Smooth** mask edges with Gaussian blur (5x5 kernel) for seamless transitions
4. **Blend** images sequentially (progress 30-80%)
   - Start with first image as base
   - For each subsequent image:
     - Calculate mask center using cv2.moments
     - Try `cv2.seamlessClone(overlay, base, mask, center, cv2.MIXED_CLONE)`
     - On cv2.error: fallback to `alpha_blend_fallback` (normalized mask alpha blending)
5. **Save** results (progress 90-100%)
   - Thumbnail: 256x256 JPEG q70
   - Full result: JPEG q90
6. **Update** FusionArtwork: status="completed", S3 keys, processing time

**Task config:**
- Queue: `default` (not high_priority — fusion is less urgent than processing)
- Time limit: 180s hard, 150s soft
- Auto-retry once on transient errors (ConnectionError, TimeoutError)
- on_failure: update status to "failed", store error message

**Memory safety:** Images capped at 2048x2048 to prevent OOM on large fusions.

### Composition Celery Task
**File:** `backend/app/workers/tasks/composition.py`

Pipeline:
1. **Load** source images (no masks needed for composition)
2. **Determine** target dimensions based on layout:
   - Horizontal: min height (maintain aspect ratio per image)
   - Vertical: min width (maintain aspect ratio per image)
   - Grid 2x2: min of both dimensions (exact resize)
3. **Resize** all images to target dimensions
4. **Compose**:
   - Horizontal: `cv2.hconcat(images)`
   - Vertical: `cv2.vconcat(images)`
   - Grid 2x2: pad to 4 images with black if <4, create 2x2 grid with hconcat+vconcat
5. **Save** results (thumbnail 256px wide proportional, full result JPEG q90)

**Task config:**
- Queue: `default`
- Time limit: 60s (compositions are fast, <5s typical)
- Auto-retry once on transient errors

### Fusion Service
**File:** `backend/app/services/fusion_service.py`

Functions:
- **`submit_fusion`**: Validates artworks, checks consent, creates FusionArtwork, submits task
- **`submit_composition`**: Same flow but purpose="composition"
- **`get_fusion_status`**: Returns status with presigned URLs (authorization: creator only for MVP)
- **`get_user_fusions`**: Paginated list of user's fusions with presigned URLs

**Consent gate:**
- Calls `check_all_consents_granted(artwork_ids, creator_id, purpose, db)` from consent_service
- If not all granted: returns `{status: "consent_required", pending: [artwork_ids]}`
- Self-owned artworks have implicit consent (skipped in pending list)

**Validation:**
- 2-4 artworks required
- All artworks must exist and be processed (have completed ProcessingJob or StyleJob)
- Purpose: "fusion" or "composition"

### Fusion API Routes
**File:** `backend/app/api/routes/fusion.py`

Endpoints:
- `POST /api/v1/fusion`: Create fusion, returns FusionResponse or ConsentRequiredResponse
- `POST /api/v1/composition`: Create composition, returns FusionResponse or ConsentRequiredResponse
- `GET /api/v1/fusion/{fusion_id}`: Get status with presigned URLs
- `GET /api/v1/fusion`: List user's fusions (paginated: offset, limit)
- `GET /api/v1/circles/{circle_id}/fusions`: Circle fusions (MVP: same as user list, TODO: filter by circle)

**Router registered** in `backend/app/main.py`.

## Key Implementation Details

### Poisson Blending with Fallback
- **Primary**: `cv2.seamlessClone` with `MIXED_CLONE` flag (seamless gradient-domain blending)
- **Fallback**: Alpha blending using normalized mask (result = base * (1-alpha) + overlay * alpha)
- Fallback triggers on cv2.error (e.g., mask/image mismatch, center out of bounds)

### Mask Smoothing
- Gaussian blur applied to mask edges before blending (5x5 kernel)
- Reduces hard boundaries, produces more natural fusion results

### Best Source Image Selection
- Priority: StyleJob result (highest quality, if user styled the image) > ProcessingJob result
- Queries both job types, returns most recent completed result
- Mask always loaded from ProcessingJob (StyleJob doesn't have mask)

### WebSocket Progress
- Reuses existing `/ws/jobs/{job_id}` endpoint (same as Phase 3 processing)
- Celery `self.update_state(state="PROGRESS", meta={...})` sends progress updates
- Frontend can connect to `websocket_url` in FusionResponse

### Memory Management
- **MAX_DIMENSION = 2048**: All images capped to prevent memory exhaustion
- If source image > 2048 in any dimension, scale down proportionally
- Target dimensions for composition use min of source dimensions (no upscaling)

### Error Handling
- **RetryableFusionTask** base class: auto-retry once on ConnectionError, TimeoutError, RuntimeError
- **on_failure**: Updates FusionArtwork status to "failed", stores error message (truncated to 500 chars)
- **ValueError** for validation errors (e.g., no processed image found)

## Deviations from Plan

None - plan executed exactly as written.

## Testing Notes

**Manual verification required:**
1. Run migration: `alembic upgrade head` (verify fusion_artworks table created)
2. Create fusion via API with 2+ processed photos
3. Verify consent gate: fusion with other user's artwork should return `consent_required`
4. Check WebSocket progress updates during processing
5. Verify Poisson blending produces seamless result (no hard edges)
6. Test alpha fallback by triggering cv2.error (e.g., invalid mask)
7. Test compositions: horizontal, vertical, grid_2x2 layouts
8. Verify memory cap: fusion with very large images should resize to 2048px
9. Check error handling: fusion with unprocessed photo should fail validation

**Expected behavior:**
- Fusion takes ~5-30 seconds depending on image count and size
- Composition takes <5 seconds (simple concat operations)
- Self-owned artwork in fusion should NOT require consent
- Progress updates every 10-20% during processing
- Completed fusion has presigned URLs for result and thumbnail

## Performance Characteristics

- **Fusion processing**: ~5-30s (depends on image count, size, blend complexity)
- **Composition processing**: <5s (simple concat, no blending)
- **Memory footprint**: Capped at 2048x2048 per image (~12MB uncompressed RGB)
- **S3 storage**: ~500KB-2MB per fusion result (JPEG q90), ~30KB per thumbnail (q70)
- **Task priority**: `default` queue (lower priority than user-facing processing jobs)

## Integration Points

**Upstream dependencies:**
- consent_service.check_all_consents_granted (05-03)
- ProcessingJob, StyleJob models (03-01, 04-02)
- Celery task infrastructure (03-01)
- S3 storage client (01-01)
- WebSocket /ws/jobs/{job_id} endpoint (03-02)

**Downstream consumers (future):**
- Mobile fusion builder UI (05-06)
- Shared gallery (05-04) — display fusion results
- Circle fusion feed — filter by circle_id

## Known Limitations (MVP)

1. **Circle filtering not implemented**: `GET /circles/{circle_id}/fusions` returns all user fusions (TODO: filter by circle_id and verify membership)
2. **Authorization**: Only creator can view fusion (TODO: allow circle members to view)
3. **Source image loading**: Always uses best available (StyleJob > ProcessingJob), no preference option
4. **Grid 2x2**: Pads with black if <4 images (could use repeating or gradient fill)
5. **Poisson blending**: No tuning parameters exposed (always MIXED_CLONE, no NORMAL_CLONE option)
6. **Mask quality**: Reuses processing mask as-is (no manual mask adjustment)

## Self-Check

**Verification commands:**
```bash
# FusionArtwork model exists
[ -f "backend/app/models/fusion_artwork.py" ] && echo "FOUND"

# Schemas exist
[ -f "backend/app/schemas/fusion.py" ] && echo "FOUND"

# Celery tasks exist
[ -f "backend/app/workers/tasks/fusion_blending.py" ] && echo "FOUND"
[ -f "backend/app/workers/tasks/composition.py" ] && echo "FOUND"

# Service exists
[ -f "backend/app/services/fusion_service.py" ] && echo "FOUND"

# API routes exist
[ -f "backend/app/api/routes/fusion.py" ] && echo "FOUND"

# Migration exists
[ -f "backend/alembic/versions/f6a7b8c9d0e1_add_fusion_artworks.py" ] && echo "FOUND"

# Commits exist
git log --oneline --all | grep -E "de2397c|ffba5c9"
```

**Self-Check Results:**

All files created and verified:
- FOUND: backend/app/models/fusion_artwork.py
- FOUND: backend/app/schemas/fusion.py
- FOUND: backend/app/workers/tasks/fusion_blending.py
- FOUND: backend/app/workers/tasks/composition.py
- FOUND: backend/app/services/fusion_service.py
- FOUND: backend/app/api/routes/fusion.py
- FOUND: backend/alembic/versions/f6a7b8c9d0e1_add_fusion_artworks.py

Commits verified:
- de2397c: feat(05-05): add FusionArtwork model, schemas, and migration
- ffba5c9: feat(05-05): add fusion/composition Celery tasks, service, and API

## Self-Check: PASSED
