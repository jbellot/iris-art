# Phase 2: Camera Capture and Image Upload - Context

**Gathered:** 2026-02-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can open the mobile app, capture an iris photo with basic camera controls, upload it to the cloud, and browse their photo gallery. This is the first visual interaction with the app. AI-guided capture overlay, artistic styles, and social sharing are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Capture experience
- Camera controls: shutter button, flash toggle, front/back camera switch, and zoom (pinch-to-zoom or slider)
- After capture: show a review screen with retake/accept buttons before proceeding (like iPhone camera flow)
- Static text tip shown before capture starts (e.g., "Hold phone 10-15cm from eye, ensure good lighting") — no real-time AI guidance yet (that's Phase 4)

### Upload flow
- Upload original full-resolution photos — no compression — AI processing pipeline downstream needs maximum quality
- Auto-retry a few times on failure silently; if retries exhausted, show error state with a manual retry button
- Progress shown as a progress bar overlay on the photo thumbnail during upload

### Gallery presentation
- Masonry / Pinterest-style layout with variable-height tiles
- Photos only — no date labels or status badges on gallery thumbnails (clean, minimal)
- Ordered newest first (reverse chronological)

### Onboarding and permissions
- Single welcome screen with brief intro and "Start capturing" button — no multi-slide onboarding
- Pre-permission screen before the system camera permission dialog, explaining why camera access is needed for iris photography
- Biometric consent (from Phase 1 infrastructure) integrated into the first-launch onboarding flow — before the user ever reaches the camera

### Claude's Discretion
- Viewfinder design (full-screen camera with circular guide overlay vs. minimal UI — pick what works best for iris capture)
- Upload timing strategy (immediate vs. background queue after accept)
- Photo detail view on tap (full-screen with zoom vs. detail card with metadata and actions)
- Camera permission denied experience (blocked screen with settings link vs. gallery-only fallback mode)

</decisions>

<specifics>
## Specific Ideas

No specific references — open to standard approaches for a modern mobile camera app.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-camera-capture-and-image-upload*
*Context gathered: 2026-02-01*
