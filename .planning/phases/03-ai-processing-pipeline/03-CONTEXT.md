# Phase 3: AI Processing Pipeline - Context

**Gathered:** 2026-02-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Take a captured iris photo and run it through iris segmentation, reflection removal, and quality enhancement — delivering visible results back to the user with real-time progress. Processing is async and user-initiated. Multi-iris fusion and artistic styles are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Processing feedback
- Show named processing steps to the user: "Segmenting iris...", "Removing reflections...", "Enhancing quality..."
- User can navigate freely while processing runs in background — not locked to a processing screen
- Push notification when processing completes (system notification even if app is backgrounded), plus in-app indicator
- Claude's discretion on gallery thumbnail treatment during processing (progress ring, spinner, or other)

### Result presentation
- Before/after slider comparison of original capture vs processed iris result
- Show final result only — no intermediate processing steps exposed to user
- Minimal metadata below the image: resolution and processing time
- Actions available on result: Save to device, Share externally, Reprocess

### Failure and retry
- Friendly, helpful error tone: suggest what the user can do next ("Try capturing with better lighting")
- Auto-retry once on transient failures (server errors), then show error if still failing
- On quality-related failures, suggest recapturing with guidance and direct link to camera
- Claude's discretion on job attempt visibility (latest status only vs attempt count)

### Processing expectations
- "Magic feel" — minimal explanation of what AI is doing, user submits and gets beautiful results
- User-initiated processing — user taps a "Process" button on a captured photo, not automatic
- Batch queue supported — user can select multiple photos and queue them all, results arrive as they complete
- Claude's discretion on quality gating (show all results vs threshold-based filtering)

### Claude's Discretion
- Gallery thumbnail progress indicator design during processing
- Job attempt visibility level (latest status vs attempt count)
- Quality gating approach for mediocre results
- Step name wording (keep magical, not technical)
- Processing queue priority and concurrency limits

</decisions>

<specifics>
## Specific Ideas

- Named steps should feel magical, not clinical — "Finding your iris..." rather than "Running segmentation model"
- Before/after slider is the hero interaction on the result screen
- Push notifications are important — processing may take time and user will have left the app
- Batch processing should feel effortless — queue and forget, come back to results

</specifics>

<deferred>
## Deferred Ideas

- Multi-iris combination (couple irises art, family art) — Phase 5: Social Features (Circles and Fusion)
- Artistic style application on processed iris — Phase 4: Camera Guidance and Artistic Styles

</deferred>

---

*Phase: 03-ai-processing-pipeline*
*Context gathered: 2026-02-09*
