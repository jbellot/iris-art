---
phase: 04-camera-guidance-and-artistic-styles
plan: 03
subsystem: ai-processing, ui, api
tags: [stable-diffusion, controlnet, watermark, hd-export, celery, websocket, react-native]

# Dependency graph
requires:
  - phase: 04-camera-guidance-and-artistic-styles
    plan: 02
    provides: Style transfer pipeline, WebSocket progress, StyleJob model
  - phase: 03-ai-processing-pipeline
    provides: Celery task patterns, ModelCache pattern, processing jobs
  - phase: 02-photo-capture-upload
    provides: Photo model, S3 storage, mobile screens

provides:
  - SDXL Turbo AI art generation from iris patterns with dev-mode OpenCV fallback
  - ControlNet preprocessing for iris edge and color extraction
  - HD export pipeline (2048x2048) with Real-ESRGAN/Lanczos upscaling
  - Server-side watermarking for free exports (tiled diagonal pattern)
  - AI generation Celery task reusing StyleJob model (style_preset_id=NULL)
  - ExportJob model tracking HD export requests with is_paid flag
  - Mobile AI generation screen with prompt input and style hint chips
  - Mobile HD export screen with payment gate placeholder
  - Export and AI generation REST API endpoints

affects: [05-stable-diffusion-premium-styles, 06-payments-and-premium]

# Tech tracking
tech-stack:
  added:
    - diffusers>=0.30.0
    - transformers>=4.40.0
    - accelerate>=0.30.0
  patterns:
    - SDXL Turbo with dev-mode OpenCV fallback (edge-preserving filter + color quantization)
    - ControlNet preprocessing using OpenCV (Canny edges + HoughCircles + k-means color clustering)
    - Tiled diagonal watermark pattern for free exports (semi-transparent, difficult to crop)
    - AI generation reuses StyleJob model with style_preset_id=NULL
    - HD export memory management: clear SD generator before loading Real-ESRGAN
    - Payment gate placeholder (is_paid flag set by Phase 6 payment webhook)

key-files:
  created:
    - backend/app/workers/models/sd_generator.py
    - backend/app/workers/models/controlnet_processor.py
    - backend/app/workers/tasks/ai_generation.py
    - backend/app/models/export_job.py
    - backend/app/schemas/exports.py
    - backend/app/services/exports.py
    - backend/app/services/watermark.py
    - backend/app/workers/tasks/hd_export.py
    - backend/app/api/routes/exports.py
    - backend/alembic/versions/c2d3e4f5a6b7_add_export_jobs_and_update_style_jobs_for_ai_generation.py
    - mobile/src/types/exports.ts
    - mobile/src/services/exports.ts
    - mobile/src/hooks/useAIGeneration.ts
    - mobile/src/hooks/useHDExport.ts
    - mobile/src/screens/Styles/AIGenerateScreen.tsx
    - mobile/src/screens/Exports/HDExportScreen.tsx
  modified:
    - backend/app/workers/models/model_cache.py
    - backend/app/api/routes/styles.py
    - backend/app/main.py
    - backend/app/models/user.py
    - backend/app/models/style_job.py
    - backend/requirements.txt
    - mobile/src/hooks/useJobProgress.ts
    - mobile/src/screens/Styles/StylePreviewScreen.tsx
    - mobile/src/navigation/types.ts
    - mobile/src/navigation/RootNavigator.tsx

key-decisions:
  - "SDXL Turbo for AI generation (4 inference steps, no guidance scale)"
  - "Dev-mode OpenCV fallback: edge-preserving filter + stylization + color quantization"
  - "ControlNet preprocessing uses OpenCV (no ML models): Canny edges + HoughCircles + k-means colors"
  - "AI generation reuses StyleJob model with style_preset_id=NULL (indicates AI generation vs preset)"
  - "Tiled diagonal watermark with 'IrisVue' repeated 3-4 times + 'Free Preview' in corner"
  - "HD export uses Real-ESRGAN 4x upscale (falls back to Lanczos resize in dev mode)"
  - "ExportJob.is_paid defaults to False, set True by Phase 6 payment verification"
  - "HD export routed to 'default' Celery queue (not high_priority) since non-urgent"
  - "Memory management: clear_sd_generator() and clear_style_models() before loading Real-ESRGAN"
  - "Magical step names for AI generation: 'Reading your iris patterns...', 'Extracting unique features...', 'Imagining your artwork...', 'Refining the details...', 'Almost done...'"
  - "HD export magical names: 'Preparing for HD export...', 'Upscaling to HD...', 'Applying finishing touches...', 'Saving your masterpiece...'"
  - "Mobile payment gate shows free (with watermark) and paid (coming soon) options"

patterns-established:
  - "AI generation auto-prompt from style hint: 'A stunning {style_hint} composition inspired by...'"
  - "Color overlays in dev-mode SD fallback based on prompt keywords (cosmic, sunset, ocean, fire, etc.)"
  - "Watermark service checks is_paid flag: paid = no watermark, free = tiled watermark"
  - "Export source types: styled (from StyleJob), ai_generated (from StyleJob with NULL preset), processed (from ProcessingJob)"

# Metrics
duration: 12min
completed: 2026-02-09
---

# Phase 04 Plan 03: AI Art Generation and HD Export Pipeline Summary

**Complete AI-unique art generation using Stable Diffusion XL Turbo with ControlNet iris guidance, plus full HD export pipeline with server-side watermarking for free/paid differentiation**

## Performance

- **Duration:** 12 minutes
- **Started:** 2026-02-09T18:01:19Z
- **Completed:** 2026-02-09T18:13:48Z
- **Tasks:** 2
- **Files modified:** 26 (16 backend, 10 mobile)

## Accomplishments

- SDXL Turbo generator with dev-mode OpenCV fallback (edge-preserving + stylization + color quantization)
- ControlNet processor extracts iris edges (Canny + HoughCircles) and dominant colors (k-means clustering)
- AI generation Celery task generates unique art from iris patterns (reuses StyleJob model with style_preset_id=NULL)
- ExportJob model tracks HD export requests with is_paid flag for watermark control
- Watermark service applies tiled diagonal "IrisVue" pattern for free exports (semi-transparent, repeated 3-4 times)
- HD export Celery task upscales to 2048x2048 (Real-ESRGAN or Lanczos fallback) and applies watermark
- Export REST API endpoints for HD export requests and job status
- AI generation endpoint added to styles API (POST /api/v1/styles/generate)
- Mobile AIGenerateScreen with prompt input and 6 style hint chips (Cosmic, Abstract, Watercolor, Oil, Geometric, Minimalist)
- Mobile HDExportScreen with payment gate placeholder (free with watermark / paid coming soon)
- StylePreviewScreen updated with "Export HD" and "Generate AI Art" buttons
- WebSocket progress tracking reused for both AI generation and HD export

## Task Commits

Each task was committed atomically:

1. **Task 1: Backend AI generation and HD export pipeline** - `eb0b2fc` (feat)
2. **Task 2: Mobile AI generation and HD export screens** - `811584a` (feat)

## Files Created/Modified

**Backend (16 files):**
- Created: `sd_generator.py`, `controlnet_processor.py`, `ai_generation.py`, `export_job.py`, `exports.py` (schemas), `exports.py` (service), `watermark.py`, `hd_export.py`, `exports.py` (routes), Alembic migration
- Modified: `model_cache.py`, `styles.py` (routes), `main.py`, `user.py`, `style_job.py`, `requirements.txt`

**Mobile (10 files):**
- Created: `exports.ts` (types), `exports.ts` (service), `useAIGeneration.ts`, `useHDExport.ts`, `AIGenerateScreen.tsx`, `HDExportScreen.tsx`
- Modified: `useJobProgress.ts`, `StylePreviewScreen.tsx`, `types.ts` (navigation), `RootNavigator.tsx`

## Decisions Made

- **SDXL Turbo for AI generation:** 4 inference steps with guidance_scale=0.0 (Turbo doesn't need guidance). Falls back to OpenCV dev-mode simulation when torch/CUDA unavailable.
- **Dev-mode OpenCV fallback:** Combines edge-preserving filter, stylization, color quantization (k=16), and prompt-based color overlays to produce visually distinct artistic images.
- **ControlNet preprocessing:** Uses OpenCV-only techniques (no ML models required): Canny edge detection + HoughCircles for iris patterns + k-means clustering (k=5) for dominant colors.
- **AI generation reuses StyleJob:** Setting style_preset_id=NULL indicates AI generation (vs preset-based styling). This allows reusing existing WebSocket infrastructure and mobile patterns.
- **Tiled diagonal watermark:** "IrisVue" text repeated 3-4 times across image at 45 degrees with semi-transparent white (alpha=80/255). Also adds "Free Preview" in bottom-right. Robust against simple cropping.
- **HD export pipeline:** Real-ESRGAN 4x upscale to 2048x2048 (falls back to Lanczos resize in dev mode). Saves as JPEG quality 95.
- **Memory management:** Call `ModelCache.clear_sd_generator()` and `clear_style_models()` before loading Real-ESRGAN to avoid VRAM conflicts (SD and Real-ESRGAN compete for GPU memory).
- **Payment gate placeholder:** ExportJob.is_paid defaults to False. Phase 6 will wire RevenueCat payment to call `mark_as_paid()` before export task checks the flag.
- **HD export queue:** Routed to 'default' queue (not high_priority) since export is non-urgent background work.
- **Magical step names:** AI generation uses iris-specific names ("Reading your iris patterns...", "Extracting unique features..."). HD export uses artisan language ("Saving your masterpiece...").
- **Mobile payment gate:** Shows free option (with watermark) as functional button, paid option (without watermark) grayed out with "Coming Soon" alert.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. All dependencies were in place (ModelCache, StyleJob, WebSocket infrastructure). Dev-mode fallbacks ensure full pipeline works without GPU/models.

## User Setup Required

None - no external service configuration required.

**Dev-mode behavior:**
- SDXL Turbo falls back to OpenCV artistic filters when torch/CUDA unavailable
- ControlNet preprocessing uses OpenCV-only techniques (works everywhere)
- Real-ESRGAN falls back to Lanczos resize for HD export
- All watermark functionality works (PIL-based, no dependencies)

**Production setup (optional):**
- SDXL Turbo model auto-downloads from HuggingFace on first run (requires CUDA GPU)
- Real-ESRGAN weights would be placed in `backend/app/workers/models/weights/` (not required for MVP)

## Next Phase Readiness

- AI art generation pipeline complete and ready for premium enhancements in Phase 5
- HD export infrastructure ready for Phase 6 payment integration (RevenueCat → mark_as_paid)
- Mobile payment gate placeholder clearly shows monetization path
- Watermark service provides free/paid differentiation for art exports

**Blockers:** None

**Note:** All exports currently get watermarks (is_paid=False). Phase 6 will wire payment verification to set is_paid=True before export task runs.

## Self-Check: PASSED

**Created files verified:**
- ✓ backend/app/workers/models/sd_generator.py
- ✓ backend/app/workers/models/controlnet_processor.py
- ✓ backend/app/workers/tasks/ai_generation.py
- ✓ backend/app/models/export_job.py
- ✓ backend/app/services/watermark.py
- ✓ backend/app/workers/tasks/hd_export.py
- ✓ backend/app/api/routes/exports.py
- ✓ mobile/src/screens/Styles/AIGenerateScreen.tsx
- ✓ mobile/src/screens/Exports/HDExportScreen.tsx
- ✓ mobile/src/hooks/useAIGeneration.ts
- ✓ mobile/src/hooks/useHDExport.ts

**Commits verified:**
- ✓ eb0b2fc (feat: backend AI generation and HD export pipeline)
- ✓ 811584a (feat: mobile AI generation and HD export screens)

All claims validated.

---
*Phase: 04-camera-guidance-and-artistic-styles*
*Completed: 2026-02-09*
