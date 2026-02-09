---
phase: 05-social-features-circles-and-fusion
plan: 03
subsystem: api
tags: [consent, permissions, shared-gallery, fastapi, sqlalchemy]

# Dependency graph
requires:
  - phase: 05-01
    provides: Circle and CircleMembership models for social groups
provides:
  - ArtworkConsent model for per-artwork, per-grantee, per-purpose permission tracking
  - Consent API for requesting, granting, denying, and revoking artwork usage permissions
  - Shared gallery endpoint showing all active circle members' artwork
  - Consent service with full lifecycle management
affects: [05-04, 05-05, 05-06, fusion, composition]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Self-owned artwork has implicit consent (no explicit grant needed)"
    - "Consent requests skip already-granted artworks"
    - "Unique constraint per artwork+grantee+purpose combination"

key-files:
  created:
    - backend/app/models/artwork_consent.py
    - backend/app/schemas/consent.py
    - backend/app/services/consent_service.py
    - backend/app/api/routes/consent.py
    - backend/alembic/versions/e5f6a7b8c9d0_add_artwork_consents.py
  modified:
    - backend/app/models/__init__.py
    - backend/app/models/user.py
    - backend/app/services/circle_service.py
    - backend/app/api/routes/circles.py
    - backend/app/schemas/circles.py
    - backend/app/main.py
    - backend/app/models/style_job.py

key-decisions:
  - "Self-owned artwork skips consent (implicit approval for own content)"
  - "Consent requests check for existing granted/pending status to avoid duplicates"
  - "Shared gallery only shows artwork from active circle members (excludes left_at != NULL)"

patterns-established:
  - "Consent lifecycle: pending → granted/denied, granted → revoked"
  - "Presigned URLs for shared gallery thumbnails (1-hour expiry)"
  - "Consent status check returns: self, granted, pending, denied, revoked, none"

# Metrics
duration: 5min
completed: 2026-02-09
---

# Phase 05 Plan 03: Shared Gallery and Consent Backend Summary

**ArtworkConsent model with per-artwork permissions, shared gallery API showing active members' art, and full consent lifecycle (request, grant, deny, revoke)**

## Performance

- **Duration:** 5 minutes
- **Started:** 2026-02-09T19:30:13Z
- **Completed:** 2026-02-09T19:35:49Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments
- ArtworkConsent model tracks per-artwork, per-grantee, per-purpose consent with full lifecycle
- Shared gallery endpoint returns paginated artwork from all active circle members with presigned URLs
- Consent API provides request, grant, deny, revoke, and status check operations
- Self-owned artwork has implicit consent (no explicit grant needed)

## Task Commits

Each task was committed atomically:

1. **Task 1: ArtworkConsent model, schemas, and migration** - `b86a000` (feat)
2. **Task 2: Consent service, shared gallery API, and consent routes** - `7cfad44` (feat)

## Files Created/Modified

### Created
- `backend/app/models/artwork_consent.py` - ArtworkConsent model with unique constraint per artwork+grantee+purpose
- `backend/app/schemas/consent.py` - Request/response schemas for consent operations
- `backend/app/services/consent_service.py` - Full consent lifecycle service (request, grant, deny, revoke, check)
- `backend/app/api/routes/consent.py` - REST API endpoints for consent management
- `backend/alembic/versions/e5f6a7b8c9d0_add_artwork_consents.py` - Database migration for artwork_consents table

### Modified
- `backend/app/models/__init__.py` - Import ArtworkConsent
- `backend/app/models/user.py` - Add consent_grants and consent_requests relationships
- `backend/app/services/circle_service.py` - Add get_shared_gallery function
- `backend/app/api/routes/circles.py` - Add GET /circles/{id}/gallery endpoint
- `backend/app/schemas/circles.py` - Add SharedGalleryItemResponse schema
- `backend/app/main.py` - Register consent router
- `backend/app/models/style_job.py` - Fix Python 3.12 compatibility (Mapped type annotation)

## Decisions Made

1. **Self-owned artwork has implicit consent** - Users don't need to request consent for their own artwork (automatic approval)
2. **Consent requests skip duplicates** - Check for existing granted/pending consent before creating new request
3. **Shared gallery shows only active members** - Filter by left_at IS NULL to exclude members who left the circle
4. **Presigned URLs for thumbnails** - 1-hour expiry for shared gallery artwork previews

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Python 3.12 compatibility in StyleJob model**
- **Found during:** Task 1 (generating Alembic migration)
- **Issue:** `Mapped["StylePreset" | None]` syntax error in Python 3.12 - string literal cannot be OR'd with None
- **Fix:** Changed to `Mapped["StylePreset | None"]` (union inside string literal)
- **Files modified:** backend/app/models/style_job.py
- **Verification:** Model imports successfully, no syntax errors
- **Committed in:** b86a000 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Auto-fix necessary for Python 3.12 compatibility. No scope creep.

## Issues Encountered

- **Database not running for migration generation** - Manually created migration file based on model specification, following existing migration patterns from alembic/versions/

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Consent backend ready for mobile UI integration (Plan 04)
- Shared gallery API ready for mobile gallery screen (Plan 04)
- Fusion gate can use check_all_consents_granted for permission validation (Plan 05)

## Self-Check: PASSED

All files created and commits verified:
- ✓ artwork_consent.py model exists
- ✓ consent schemas exist
- ✓ consent service exists
- ✓ consent routes exist
- ✓ migration file exists
- ✓ Commit b86a000 exists (Task 1)
- ✓ Commit 7cfad44 exists (Task 2)

---
*Phase: 05-social-features-circles-and-fusion*
*Completed: 2026-02-09*
