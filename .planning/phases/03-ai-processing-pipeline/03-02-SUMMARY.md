---
phase: 03-ai-processing-pipeline
plan: 02
subsystem: backend-websocket-streaming
tags: [websocket, realtime, celery, progress, error-handling]
dependency-graph:
  requires: [processing-api, celery-worker, ai-pipeline]
  provides: [websocket-progress, realtime-updates]
  affects: [main-app, celery-tasks]
tech-stack:
  added: [fastapi-websocket, celery-result-polling]
  patterns: [polling-loop, jwt-query-auth, magical-naming, dual-state-updates, failure-cleanup]
key-files:
  created:
    - backend/app/api/routes/websocket.py
    - backend/app/schemas/websocket.py
  modified:
    - backend/app/main.py
    - backend/app/workers/tasks/processing.py
decisions:
  - "WebSocket authentication via JWT query parameter (WebSocket doesn't support Authorization header)"
  - "500ms polling interval balances responsiveness with server load"
  - "Magical step names (Finding your iris..., Removing reflections...) over technical names per user decision"
  - "Dual state updates: Celery state for real-time, database for persistent state after completion/failure"
  - "10-minute WebSocket timeout prevents indefinite connections"
  - "on_failure handler cleans up partial S3 objects automatically"
  - "Immediate result delivery for already-completed jobs (no stuck connections)"
  - "Job continues in Celery if WebSocket disconnects (resilient design)"
metrics:
  duration: 4min
  tasks-completed: 2
  files-created: 2
  files-modified: 2
  commits: 2
  completed-date: 2026-02-09
---

# Phase 03 Plan 02: WebSocket Real-Time Progress Streaming Summary

**One-liner:** WebSocket real-time progress streaming with magical step names, JWT query param auth, dual state updates (Celery + DB), classified error messages, failure cleanup, and resilient disconnection handling.

## What Was Built

### Task 1: WebSocket Progress Endpoint with Step Name Mapping
**Commit:** fd8dc26

Built the complete WebSocket infrastructure for real-time progress streaming:

**WebSocket Message Schemas:**
- **ProgressMessage**: Base schema with job_id, status, progress (0-100), step (magical name), timestamp
- **CompletionMessage**: Extends ProgressMessage with result_url (presigned), processing_time_ms, dimensions
- **ErrorMessage**: Extends ProgressMessage with error_type, message (friendly), suggestion (actionable)

**Step Name Mapping:**
Mapped internal step names to magical, user-facing names per user decision:
- `loading` → "Preparing your image..."
- `segmenting` → "Finding your iris..."
- `removing_reflections` → "Removing reflections..."
- `enhancing` → "Enhancing quality..."
- `saving` → "Almost done..."
- `completed` → "Complete!"

**WebSocket Endpoint (`/ws/jobs/{job_id}`):**
- **Authentication**: JWT token from query parameter (`?token=...`) since WebSocket doesn't support Authorization header
- **Connection Flow**:
  1. Accept WebSocket connection
  2. Validate JWT token and user identity
  3. Verify job exists and belongs to user
  4. Enter 500ms polling loop
- **Polling Loop**:
  - Polls Celery AsyncResult for real-time task state
  - Reads database for persistent job state
  - Prefers Celery state for in-progress jobs, DB state for completed/failed
  - Sends progress updates with magical step names
- **Completion Handling**: Sends presigned result URL, processing time, dimensions, then closes
- **Failure Handling**: Sends classified error (quality_issue/transient_error/server_error) with friendly message and suggestion
- **Disconnection**: Graceful handling - job continues in Celery background
- **Already-Completed Jobs**: Immediate result delivery (no infinite polling)
- **Timeout**: 10-minute safety limit to prevent indefinite connections

**Router Registration:**
- Added websocket router to main.py FastAPI app

### Task 2: Enhanced Pipeline with Granular Progress and Error Classification
**Commit:** f0105aa

Enhanced the Celery pipeline task for better progress tracking and failure handling:

**on_retry Handler:**
- Tracks retry attempts by incrementing `attempt_count` in database
- Logs retry reason and exception type
- Provides visibility into transient failure patterns

**on_failure Handler:**
- Fires when task permanently fails (all retries exhausted)
- **S3 Cleanup**: Automatically deletes partial result files:
  - `processed/{user_id}/{job_id}.jpg`
  - `processed/{user_id}/{job_id}_mask.png`
- **Error Classification**: Sets appropriate error_type, message, and suggestion based on exception:
  - ValueError → quality_issue (already handled in task body)
  - ConnectionError/TimeoutError → transient_error ("Tap 'Reprocess' to try again")
  - RuntimeError → server_error ("Tap 'Reprocess' to try again, or try with a different photo")
  - Other exceptions → server_error ("Please try again later")

**Granular Progress Updates:**
- Enhanced all Celery `update_state` calls to include `job_id` in meta
- Progress checkpoints at: 5, 10, 20, 40, 50, 60, 70, 90, 95, 100
- Dual updates at each major step:
  1. Database update via `_update_job_sync` (persistent state)
  2. Celery state update via `self.update_state` (real-time polling)
- Smooth progression through all pipeline stages

**Error Classification Improvements:**
- Added separate RuntimeError handling (CUDA OOM, model crashes)
- Updated all error suggestions to be more actionable:
  - quality_issue: "Try capturing a new photo in better lighting with your eye centered"
  - transient_error: "Tap 'Reprocess' to try again"
  - server_error: "Tap 'Reprocess' to try again, or try with a different photo" / "Please try again later"

## Deviations from Plan

None - plan executed exactly as written.

All enhancements (dual state updates, failure cleanup, retry tracking) were specified in the plan.

## Technical Highlights

### Dual State Updates
Every progress update writes to both:
1. **Celery state** (AsyncResult meta): For real-time WebSocket polling during processing
2. **Database** (ProcessingJob record): For persistent state after task completes or fails

This ensures:
- WebSocket clients get real-time updates while task is running
- Clients can reconnect and get final state from database after completion
- No race conditions between task completion and WebSocket polling

### JWT Query Parameter Authentication
WebSocket connections don't support standard Authorization headers the same way HTTP does. Solution:
- Accept token as query parameter: `/ws/jobs/{job_id}?token=...`
- Reuse existing JWT validation logic from `get_current_user`
- Verify job ownership before streaming updates
- Close connection with policy violation if authentication fails

### Magical Step Names
User decision: "Magic feel" over technical explanations. Internal names like `segmenting` map to user-facing names like "Finding your iris..." to create a delightful, non-technical experience.

### Failure Cleanup
`on_failure` handler automatically cleans up partial S3 objects:
- Prevents orphaned files in storage
- Maintains clean bucket state
- Handles case where task fails mid-processing (e.g., after saving result but before saving mask)

### Resilient Disconnection
Job survives WebSocket disconnection:
- WebSocket catches `WebSocketDisconnect` exception
- Logs disconnect but doesn't affect Celery task
- Task continues running in background
- Client can reconnect with new WebSocket to get updated progress

### Already-Completed Job Handling
WebSocket checks job status immediately:
- If `status == "completed"`, sends result immediately and closes
- If `status == "failed"`, sends error immediately and closes
- Prevents infinite polling for jobs that finished while client was disconnected

## Verification Results

All verification checks passed:

```bash
✓ WebSocket endpoint importable
✓ WebSocket router registered in main.py
✓ Step name mapping contains all magical names
✓ Pipeline task updates both Celery state and database at each step
✓ Error classification covers quality_issue, transient_error, server_error
✓ on_failure handler cleans up partial S3 objects
✓ on_retry handler tracks attempt count
✓ WebSocket handles already-completed jobs
✓ WebSocket times out after 10 minutes
✓ 9 Celery state updates in pipeline (every major step)
✓ Dual updates ensure real-time + persistent state
```

## WebSocket Message Flow

```
1. Client connects: ws://api/ws/jobs/{job_id}?token=...
   ↓
2. Server validates JWT and job ownership
   ↓
3. Enter 500ms polling loop:
   - Poll Celery AsyncResult
   - Read database job record
   - Map internal step to magical name
   - Send progress message
   ↓
4a. Job completes:
    - Send completion message with presigned result URL
    - Close WebSocket

4b. Job fails:
    - Send error message with classification and suggestion
    - Close WebSocket

4c. Client disconnects:
    - Log disconnect
    - Job continues in Celery

4d. Timeout (10 min):
    - Send timeout message
    - Close WebSocket (job continues)
```

## Example WebSocket Messages

**Progress Update:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "progress": 50,
  "step": "Removing reflections...",
  "timestamp": "2026-02-09T16:15:30Z"
}
```

**Completion:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "progress": 100,
  "step": "Complete!",
  "timestamp": "2026-02-09T16:16:05Z",
  "result_url": "https://s3.../processed/user_id/job_id.jpg?signature=...",
  "processing_time_ms": 35420,
  "result_width": 2048,
  "result_height": 2048
}
```

**Error:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "failed",
  "progress": 20,
  "step": "Finding your iris...",
  "timestamp": "2026-02-09T16:15:45Z",
  "error_type": "quality_issue",
  "message": "Iris not detected in image",
  "suggestion": "Try capturing a new photo in better lighting with your eye centered."
}
```

## Next Steps

**Immediate (Phase 3 continuation):**
- Add mobile WebSocket client for real-time progress UI
- Implement progress indicator with magical step names
- Add error handling and retry flow in mobile app
- Test WebSocket disconnection/reconnection scenarios

**Future enhancements:**
- Add progress percentage estimation based on pipeline stage
- Implement WebSocket connection pooling for scalability
- Add support for batch job progress (multiple jobs in one WebSocket)
- Consider Redis pub/sub as alternative to polling for higher concurrency

## Self-Check: PASSED

**Created files verified:**
```bash
✓ backend/app/api/routes/websocket.py
✓ backend/app/schemas/websocket.py
```

**Modified files verified:**
```bash
✓ backend/app/main.py (websocket router registered)
✓ backend/app/workers/tasks/processing.py (enhanced with handlers and dual updates)
```

**Commits verified:**
```bash
✓ fd8dc26: feat(03-02): add WebSocket real-time progress streaming with magical step names
✓ f0105aa: feat(03-02): enhance pipeline with granular progress, error classification, and failure handlers
```

All claimed artifacts exist and are committed to version control.
