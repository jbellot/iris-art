# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-01)

**Core value:** Any user can capture a beautiful iris photo with their phone and turn it into personalized art
**Current focus:** Phase 5 complete — ready for Phase 6

## Current Position

Phase: 6 of 7 (Payments and Freemium)
Plan: 1 of 2 in current phase
Status: Active - Phase 6 In Progress
Last activity: 2026-02-10 -- Completed 06-01-PLAN.md (RevenueCat Payment Infrastructure)

Progress: [█████████░] 80%

## Performance Metrics

**Velocity:**
- Total plans completed: 19
- Average duration: 7 min
- Total execution time: 4.2 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 3/3 | 102 min | 34 min |
| 2 | 3/3 | 61 min | 20 min |
| 3 | 3/3 | 18 min | 6 min |
| 4 | 3/3 | 29 min | 10 min |
| 5 | 6/6 | 23 min | 3.8 min |
| 6 | 1/2 | 8 min | 8 min |

**Recent Trend:**
- Last 5 plans: 4 min, 4 min, 4 min, 6 min, 8 min
- Trend: Consistent execution speed

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: React Native + Vision Camera for mobile (research HIGH confidence)
- [Roadmap]: Privacy/biometric compliance is Phase 1 -- cannot be deferred
- [Roadmap]: Vertical build order: full-stack per feature, not horizontal layers
- [01-01]: SQLAlchemy 2.0 async with expire_on_commit=False prevents lazy load errors
- [01-01]: MinIO for S3-compatible local storage with server-side encryption
- [01-01]: Celery with Redis broker for background task processing
- [01-02]: JWT HS256 (symmetric) for single backend service
- [01-02]: Refresh token hashing in Redis for security
- [01-02]: Log emails instead of sending (ESP selection pending)
- [01-02]: Generic error messages prevent email enumeration
- [01-03]: IP geolocation with device locale fallback for jurisdiction detection
- [01-03]: Preserve consent records on withdrawal (audit trail required)
- [01-03]: Celery async data export with Redis result storage
- [01-03]: Optional S3 SSE for MinIO compatibility (disabled in dev)
- [02-01]: Presigned URLs for direct S3 upload (avoids streaming through backend)
- [02-01]: Biometric consent shown informational during onboarding, actual grant on first camera access
- [02-01]: JWT refresh interceptor with request queuing during token refresh
- [02-01]: Encrypted token storage using react-native-encrypted-storage
- [02-02]: Reanimated shared values for zoom (UI thread animation, 60fps)
- [02-02]: Separate axios instance for S3 PUT (presigned URL has auth in query)
- [02-02]: Exponential backoff retry only on network/5xx errors (not 4xx)
- [02-02]: Navigate to Gallery immediately after Accept (upload runs in background)
- [02-02]: Timestamp-based local ID generator (no uuid dependency)
- [02-03]: FlashList 2-column layout with variable-height items for masonry effect
- [02-03]: Active uploads prepended to API photos with local file:// URIs
- [02-03]: FastImage immutable caching for uploaded photos
- [03-01]: Sync SQLAlchemy session for Celery workers (psycopg2 with lazy loading)
- [03-01]: Dev-mode fallbacks: simulated segmentation mask, OpenCV Lanczos enhancement
- [03-01]: MVP reflection removal uses OpenCV inpainting (upgradeable to LapCAT)
- [03-01]: Singleton ModelCache with lazy loading prevents repeated model loads
- [03-01]: Priority queues for Celery (high_priority for user jobs, default for background)
- [03-01]: Auto-retry once on transient errors with exponential backoff
- [03-01]: Error classification: quality_issue, transient_error, server_error
- [03-01]: Celery prefetch-multiplier=1 prevents AI task queue buildup
- [Phase 03-02]: WebSocket authentication via JWT query parameter (WebSocket doesn't support Authorization header)
- [Phase 03-02]: Magical step names (Finding your iris...) over technical names per user decision
- [Phase 03-02]: Dual state updates: Celery state for real-time, database for persistent state
- [Phase 03-02]: on_failure handler cleans up partial S3 objects automatically
- [03-03]: WebSocket hook with auto-reconnect (max 3 retries, 2s delay)
- [03-03]: Zustand store for processing job tracking (same pattern as upload store)
- [03-03]: Before/after slider with PanResponder as hero interaction
- [03-03]: Process button in PhotoDetail header (natural UX flow)
- [03-03]: Quality errors suggest recapturing, transient errors suggest retry
- [Phase 04-01]: Frame skipping (every 3rd frame) for 33ms budget compliance
- [Phase 04-01]: 500ms debounce on readyToCapture prevents button flickering
- [Phase 04-01]: Burst capture selects middle frame (MVP approach for stability)
- [Phase 04-02]: OpenCV stylization fallback when ONNX models not found (dev mode support)
- [Phase 04-02]: 15 style presets seeded: 5 free, 10 premium with lock icon UI
- [Phase 04-02]: Progressive image loading: 256px preview with 3px blur, cross-fade to 1024px full-res
- [Phase 04-02]: Reuse Phase 3 WebSocket /ws/jobs/{job_id} endpoint for style job progress
- [Phase 04-02]: Premium styles show 'coming soon' alert (payment is Phase 6)
- [Phase 04-02]: Style model caching by name in ModelCache singleton
- [Phase 04-03]: SDXL Turbo for AI generation (4 steps, no guidance) with dev-mode OpenCV fallback
- [Phase 04-03]: AI generation reuses StyleJob model with style_preset_id=NULL
- [Phase 04-03]: Tiled diagonal watermark for free exports (semi-transparent "IrisVue" repeated 3-4 times)
- [Phase 04-03]: HD export to 2048x2048 with Real-ESRGAN or Lanczos fallback
- [Phase 04-03]: ExportJob.is_paid defaults to False, set True by Phase 6 payment verification
- [Phase 04-03]: Memory management: clear SD generator before loading Real-ESRGAN to avoid VRAM conflicts
- [Phase 05-01]: Soft delete for memberships with ownership transfer on owner departure
- [Phase 05-01]: Redis for invite token single-use tracking (30-day TTL)
- [Phase 05-01]: Rate limiting via Redis counters (5 invites per circle per hour)
- [Phase 05-01]: 10-member circle limit and 20-circle-per-user limit enforced
- [Phase 05-02]: React Native built-in Clipboard API instead of @react-native-clipboard/clipboard
- [Phase 05-02]: Circles navigation integrated via header button (not tab bar) for MVP
- [Phase 05-02]: Placeholder screens for SharedGallery and Fusion screens (forward-compatibility)
- [Phase 05-02]: Deep link configuration for invite URLs (irisvue://invite/:token)
- [Phase 05-03]: Self-owned artwork skips consent (implicit approval for own content)
- [Phase 05-03]: Consent requests check for existing granted/pending status to avoid duplicates
- [Phase 05-03]: Shared gallery only shows artwork from active circle members (excludes left_at != NULL)
- [Phase 05-06]: WebSocket + REST polling fallback for fusion progress (reuses Phase 3 pattern)
- [Phase 05-06]: Magical step names for fusion (5 steps) and composition (3 steps)
- [Phase 05-06]: Consent-required inline handling with pending consent owner list
- [Phase 05-06]: 2-4 artwork validation enforced at selection and submission
- [Phase 06-01]: Database-backed monthly rate limiting (no Redis) for low-frequency AI generation counts
- [Phase 06-01]: Empty string defaults for RevenueCat API keys (dev-safe, graceful degradation)
- [Phase 06-01]: Webhook 200 responses for all cases (prevents infinite retry loops on permanent failures)
- [Phase 06-01]: --legacy-peer-deps for react-native-purchases install (React 19 peer dep conflict)

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-02-10
Stopped at: Completed 06-01-PLAN.md (RevenueCat Payment Infrastructure)
Resume file: None
