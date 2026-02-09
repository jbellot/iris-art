# Phase 3: AI Processing Pipeline - Research

**Researched:** 2026-02-09
**Domain:** Asynchronous AI image processing with real-time progress tracking
**Confidence:** HIGH

## Summary

Phase 3 implements the core AI processing pipeline for iris segmentation, reflection removal, and quality enhancement. The pipeline runs asynchronously via Celery workers with real-time progress updates over WebSocket, delivering visible results back to the user with named processing steps ("Finding your iris...", "Removing reflections...", "Enhancing quality..."). Processing is user-initiated, supports batch queueing, and handles failures gracefully with friendly, actionable error messages.

The research confirms that the existing stack (FastAPI + Celery + Redis + WebSocket) is well-suited for this phase. The critical technical decisions are: (1) using ONNX Runtime for 2-3x inference speedup over native PyTorch, (2) loading AI models once at worker startup and reusing across tasks to avoid 3-10 second overhead per task, (3) implementing priority queues to ensure user-initiated processing completes faster than batch jobs, and (4) using exponential backoff with jitter for automatic retry on transient failures.

The primary challenges are: (1) selecting and fine-tuning iris segmentation models (U-Net and DeepLabV3+ are proven architectures with 95%+ accuracy), (2) implementing reflection removal (recent transformer models like LapCAT show promise but may require custom training), (3) integrating Real-ESRGAN for upscaling (battle-tested, production-ready), and (4) ensuring graceful degradation when AI models fail on poor-quality inputs.

**Primary recommendation:** Build vertically (segmentation → WebSocket progress → mobile result display) before horizontally (all three AI stages at once). Start with U-Net for segmentation (proven, fast), defer reflection removal to later iteration if quality is acceptable without it, and use Real-ESRGAN for enhancement (pre-trained models available). Implement WebSocket progress tracking from day 1—it's architecturally simpler to build it in initially than to retrofit later.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Processing feedback:**
- Show named processing steps to the user: "Segmenting iris...", "Removing reflections...", "Enhancing quality..."
- User can navigate freely while processing runs in background — not locked to a processing screen
- Push notification when processing completes (system notification even if app is backgrounded), plus in-app indicator
- Claude's discretion on gallery thumbnail treatment during processing (progress ring, spinner, or other)

**Result presentation:**
- Before/after slider comparison of original capture vs processed iris result
- Show final result only — no intermediate processing steps exposed to user
- Minimal metadata below the image: resolution and processing time
- Actions available on result: Save to device, Share externally, Reprocess

**Failure and retry:**
- Friendly, helpful error tone: suggest what the user can do next ("Try capturing with better lighting")
- Auto-retry once on transient failures (server errors), then show error if still failing
- On quality-related failures, suggest recapturing with guidance and direct link to camera
- Claude's discretion on job attempt visibility (latest status only vs attempt count)

**Processing expectations:**
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

### Deferred Ideas (OUT OF SCOPE)

- Multi-iris combination (couple irises art, family art) — Phase 5: Social Features (Circles and Fusion)
- Artistic style application on processed iris — Phase 4: Camera Guidance and Artistic Styles

</user_constraints>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **PyTorch** | 2.x | Deep learning framework | Industry standard for computer vision, better ecosystem for iris segmentation models, superior research-to-production workflow |
| **ONNX Runtime** | 1.20.x | Model inference optimization | 2-3x faster inference than native PyTorch, supports CPU/GPU/NPU acceleration, production-proven for scaling |
| **opencv-python-headless** | 4.10.x | Image preprocessing | Headless version (no GUI dependencies), used for color space conversion, geometric transforms, pre/post-processing |
| **Pillow** | 11.x | Image I/O | Reading/writing image formats, EXIF handling, basic manipulations |
| **Celery** | 5.6.x | Distributed task queue | Already in stack (Phase 1), proven for ML workloads, supports priority queues and retry logic |
| **Redis** | 7.x | Message broker + result backend | Already in stack (Phase 1), Celery broker and job state storage |
| **FastAPI WebSocket** | (built-in) | Real-time progress updates | Native FastAPI WebSocket support for streaming job progress to mobile clients |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **torchvision** | 0.19.x | Pre-trained models and transforms | Image transformations, data augmentation utilities |
| **numpy** | 2.x | Numerical operations | Array operations, matrix math for image processing pipelines |
| **scikit-image** | 0.24.x | Traditional CV algorithms | Morphology operations, filters for preprocessing, quality metrics (SSIM, PSNR) |
| **boto3** | latest | S3 operations | Already in stack (Phase 1), load original images from S3, save processed results |

### AI Models by Pipeline Stage

| Stage | Model | Why Chosen | Confidence |
|-------|-------|-----------|------------|
| **Iris Segmentation** | U-Net or DeepLabV3+ with MobileNetV2 | U-Net achieves 98.9%+ IoU on iris datasets. DeepLabV3+ achieves 95.54% mIoU with faster inference. Both proven in research. | HIGH |
| **Reflection Removal** | Traditional inpainting OR LapCAT transformer | Traditional approach faster but lower quality. LapCAT (2025) handles high-res reflection removal. May need custom training. | MEDIUM |
| **Quality Enhancement** | Real-ESRGAN (4x upscaling) | Industry standard, battle-tested, free/open-source, pre-trained models available, 4x/8x upscaling with detail preservation | HIGH |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ONNX Runtime | Native PyTorch | Native PyTorch 2-3x slower inference, ONNX Runtime optimizes graph and integrates hardware accelerators (CUDA, TensorRT) |
| U-Net | SAM (Segment Anything Model) | SAM is general-purpose, not iris-specific; U-Net variants trained on iris datasets perform better and faster |
| Real-ESRGAN | Stable Diffusion upscaling | Stable Diffusion more resource-intensive (10-30s), Real-ESRGAN optimized for upscaling (2-5s), simpler integration |
| WebSocket | HTTP polling | Polling wastes bandwidth (hundreds of requests), slower updates (1-2s delay), WebSocket instant push updates |
| Celery | RQ (Redis Queue) | RQ simpler but lacks priority queues, task routing, Celery Beat scheduling — needed for Phase 3+ complexity |

**Installation:**
```bash
# AI/ML core
pip install torch>=2.0.0 torchvision>=0.19.0
pip install onnxruntime>=1.20.0
pip install opencv-python-headless>=4.10.0
pip install Pillow>=11.0
pip install numpy>=2.0
pip install scikit-image>=0.24.0

# Already installed from Phase 1
# celery>=5.2.7
# redis>=4.5.4
# fastapi[standard]>=0.115.0
# boto3
```

## Architecture Patterns

### Recommended Project Structure

```
backend/
├── app/
│   ├── workers/
│   │   ├── celery_app.py           # Already exists (Phase 1)
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   ├── iris_segmentation.py    # NEW: Segmentation task
│   │   │   ├── reflection_removal.py   # NEW: Reflection removal task
│   │   │   └── enhancement.py          # NEW: Enhancement task
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── model_cache.py          # NEW: Load models once, reuse
│   │       ├── segmentation_model.py   # NEW: U-Net/DeepLabV3+ wrapper
│   │       ├── reflection_model.py     # NEW: Reflection removal wrapper
│   │       └── enhancement_model.py    # NEW: Real-ESRGAN wrapper
│   ├── api/
│   │   └── routes/
│   │       ├── processing.py           # NEW: Job submission endpoints
│   │       └── websocket.py            # NEW: WebSocket progress streaming
│   ├── models/                         # SQLAlchemy models
│   │   ├── processing_job.py           # NEW: Job tracking table
│   │   └── processed_image.py          # NEW: Results table
│   ├── schemas/
│   │   ├── processing.py               # NEW: Pydantic schemas for jobs
│   │   └── websocket.py                # NEW: WebSocket message schemas
│   └── services/
│       └── processing_service.py       # NEW: Business logic for job management
```

### Pattern 1: Model Loading at Worker Startup

**What:** Load AI models once when Celery worker starts, store in memory, reuse across all tasks

**When to use:** All production deployments — loading models per-task adds 3-10 second overhead per job

**Why critical:** PyTorch model loading involves reading weights from disk (100MB-500MB), initializing layers, and moving to GPU memory. Doing this for every task is catastrophically slow. Loading once at startup amortizes cost across thousands of tasks.

**Example:**
```python
# app/workers/models/model_cache.py
import torch
import onnxruntime as ort
from pathlib import Path

class ModelCache:
    """Singleton cache for AI models. Load once at worker startup, reuse forever."""

    _segmentation_session = None
    _enhancement_model = None

    @classmethod
    def get_segmentation_model(cls):
        """Get ONNX Runtime session for iris segmentation."""
        if cls._segmentation_session is None:
            model_path = Path(__file__).parent / "weights" / "unet_iris_segmentation.onnx"

            # Configure ONNX Runtime for GPU if available
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
            cls._segmentation_session = ort.InferenceSession(
                str(model_path),
                providers=providers
            )
            print(f"Loaded segmentation model on {cls._segmentation_session.get_providers()[0]}")

        return cls._segmentation_session

    @classmethod
    def get_enhancement_model(cls):
        """Get Real-ESRGAN model for quality enhancement."""
        if cls._enhancement_model is None:
            from basicsr.archs.rrdbnet_arch import RRDBNet
            from realesrgan import RealESRGANer

            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
            model_path = Path(__file__).parent / "weights" / "RealESRGAN_x4plus.pth"

            cls._enhancement_model = RealESRGANer(
                scale=4,
                model_path=str(model_path),
                model=model,
                tile=400,  # Process in tiles to avoid OOM on large images
                tile_pad=10,
                pre_pad=0,
                half=True,  # FP16 for faster GPU inference
                device='cuda' if torch.cuda.is_available() else 'cpu'
            )
            print(f"Loaded enhancement model on {cls._enhancement_model.device}")

        return cls._enhancement_model

# app/workers/tasks/iris_segmentation.py
from app.workers.celery_app import celery_app
from app.workers.models.model_cache import ModelCache

@celery_app.task(bind=True)
def segment_iris_task(self, image_id: str):
    """
    Segment iris from captured photo.
    Model is loaded once at worker startup, not per-task.
    """
    # Get model from cache — instant, already loaded
    model = ModelCache.get_segmentation_model()

    # Load image from S3
    self.update_state(state='PROGRESS', meta={'step': 'loading', 'progress': 10})
    image = load_image_from_s3(image_id)

    # Preprocess
    self.update_state(state='PROGRESS', meta={'step': 'preparing', 'progress': 30})
    input_tensor = preprocess_for_segmentation(image)

    # Run inference (fast — model already loaded)
    self.update_state(state='PROGRESS', meta={'step': 'finding_iris', 'progress': 50})
    output = model.run(None, {'input': input_tensor})[0]

    # Post-process and save
    self.update_state(state='PROGRESS', meta={'step': 'finalizing', 'progress': 80})
    segmented_image = postprocess_segmentation(output, image)
    result_url = save_result_to_s3(segmented_image, image_id)

    return {'result_url': result_url, 'progress': 100}
```

**Critical:** Models must be loaded in worker process, not in FastAPI process. Celery workers are separate processes, so model loading happens once per worker, not once globally.

### Pattern 2: WebSocket Progress Streaming

**What:** FastAPI WebSocket endpoint that polls Celery task state and streams updates to mobile client in real-time

**When to use:** All long-running tasks (>2 seconds) — iris processing takes 5-15 seconds, users need progress feedback

**Why better than polling:** HTTP polling generates hundreds of wasteful requests, delays updates by 1-2 seconds, drains mobile battery. WebSocket is single persistent connection with instant server-push updates.

**Example:**
```python
# app/api/routes/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from celery.result import AsyncResult
from app.workers.celery_app import celery_app
import asyncio

@app.websocket("/ws/jobs/{job_id}")
async def job_progress_websocket(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time job progress updates.
    Mobile client connects, receives progress updates until job completes.
    """
    await websocket.accept()

    try:
        result = AsyncResult(job_id, app=celery_app)

        # Poll task state every 500ms, push updates to client
        while not result.ready():
            state = result.state
            info = result.info if isinstance(result.info, dict) else {}

            # Map internal task state to user-friendly step names
            step_name = map_step_to_display_name(info.get('step', ''))

            await websocket.send_json({
                'status': state,
                'progress': info.get('progress', 0),
                'step': step_name,  # "Finding your iris..." not "segmentation"
                'timestamp': datetime.utcnow().isoformat()
            })

            await asyncio.sleep(0.5)  # Poll every 500ms

        # Send final completion message
        await websocket.send_json({
            'status': 'completed',
            'progress': 100,
            'result': result.result,
            'timestamp': datetime.utcnow().isoformat()
        })

    except WebSocketDisconnect:
        # Client disconnected — job continues in background
        pass
    except Exception as e:
        # Send error to client
        await websocket.send_json({
            'status': 'failed',
            'error': str(e)
        })
    finally:
        await websocket.close()

def map_step_to_display_name(internal_step: str) -> str:
    """Map internal task steps to user-friendly, magical names."""
    mapping = {
        'loading': 'Preparing your image...',
        'preparing': 'Preparing your image...',
        'finding_iris': 'Finding your iris...',
        'segmentation': 'Finding your iris...',
        'removing_reflections': 'Removing reflections...',
        'enhancing': 'Enhancing quality...',
        'upscaling': 'Enhancing quality...',
        'finalizing': 'Almost done...',
        'saving': 'Almost done...'
    }
    return mapping.get(internal_step, 'Processing...')
```

**Mobile client example:**
```typescript
// mobile/src/hooks/useJobProgress.ts
export const useJobProgress = (jobId: string) => {
  const [progress, setProgress] = useState(0);
  const [step, setStep] = useState('');
  const [result, setResult] = useState<ProcessingResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ws = new WebSocket(`wss://api.irisvue.com/ws/jobs/${jobId}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      setProgress(data.progress);
      setStep(data.step);

      if (data.status === 'completed') {
        setResult(data.result);
        ws.close();

        // Show push notification if app is backgrounded
        showNotification({
          title: 'Processing Complete',
          body: 'Your iris art is ready to view!'
        });
      } else if (data.status === 'failed') {
        setError(data.error);
        ws.close();
      }
    };

    ws.onerror = () => {
      setError('Connection lost. Please check your network.');
    };

    return () => ws.close();
  }, [jobId]);

  return { progress, step, result, error };
};
```

### Pattern 3: Priority Queue for User-Initiated vs Batch Processing

**What:** Separate Celery queues with different priorities — high priority for user-initiated processing, normal priority for batch jobs

**When to use:** When you have both interactive (user waiting) and background (system-initiated) processing

**Why important:** User-initiated processing must feel instant. If batch analytics jobs clog the queue, users wait minutes for their photos. Priority queues ensure user jobs jump the line.

**Example:**
```python
# app/workers/celery_app.py (updated from Phase 1)
from celery import Celery
from kombu import Queue

celery_app = Celery("iris_art", ...)

# Configure priority queues
celery_app.conf.update(
    task_queues=(
        Queue('high_priority', routing_key='high', priority=9),
        Queue('normal_priority', routing_key='normal', priority=5),
        Queue('low_priority', routing_key='low', priority=1),
    ),

    # Route tasks to appropriate queues
    task_routes={
        'app.workers.tasks.iris_segmentation.*': {
            'queue': 'high_priority',
            'priority': 9
        },
        'app.workers.tasks.enhancement.*': {
            'queue': 'high_priority',
            'priority': 9
        },
        'app.workers.tasks.batch_analytics.*': {
            'queue': 'low_priority',
            'priority': 1
        }
    }
)

# Worker command:
# celery -A app.workers.celery_app worker -Q high_priority,normal_priority,low_priority -c 4
```

**Deployment:**
```yaml
# docker-compose.yml (updated from Phase 1)
services:
  worker-high-priority:
    build: .
    command: celery -A app.workers.celery_app worker -Q high_priority -c 4 --prefetch-multiplier=1
    deploy:
      replicas: 3  # More workers for user-facing tasks

  worker-normal-priority:
    build: .
    command: celery -A app.workers.celery_app worker -Q normal_priority -c 2
    deploy:
      replicas: 1
```

### Pattern 4: Automatic Retry with Exponential Backoff

**What:** Celery tasks automatically retry on failure with exponentially increasing delays and random jitter

**When to use:** All AI processing tasks — models can fail due to transient errors (OOM, GPU timeout, S3 network issues)

**Why exponential backoff:** Immediate retry often fails again (resource still unavailable). Exponential backoff gives system time to recover. Jitter prevents "thundering herd" where all retries happen simultaneously.

**Example:**
```python
# app/workers/tasks/iris_segmentation.py
from celery import Task
from app.workers.celery_app import celery_app

class RetryableTask(Task):
    """Base task class with retry configuration."""
    autoretry_for = (
        ConnectionError,  # S3 connection issues
        TimeoutError,     # Model inference timeout
        RuntimeError,     # CUDA OOM or model errors
    )
    retry_backoff = True        # Enable exponential backoff
    retry_backoff_max = 600     # Max 10 minutes between retries
    retry_jitter = True         # Add random jitter to prevent thundering herd
    max_retries = 3             # Try up to 3 times before giving up

@celery_app.task(bind=True, base=RetryableTask)
def segment_iris_task(self, image_id: str, attempt: int = 1):
    """
    Segment iris with automatic retry on transient failures.

    User constraint: Auto-retry once on transient failures, then show error.
    """
    try:
        # ... processing logic ...
        return {'result_url': result_url, 'progress': 100}

    except ValueError as e:
        # Quality-related failure (iris not detected) — don't retry, show helpful error
        raise self.retry(exc=e, countdown=0, max_retries=0)  # Fail immediately

    except Exception as e:
        # Transient failure — let autoretry_for handle it
        # Backoff calculation: retry_backoff * 2^retry_count
        # First retry: ~2s, second retry: ~4s, third retry: ~8s (with jitter)
        raise
```

**Error handling in API:**
```python
# app/api/routes/processing.py
from celery.exceptions import MaxRetriesExceededError

@router.post("/process/segment")
async def submit_segmentation_job(image_id: str, db: AsyncSession = Depends(get_db)):
    """Submit iris segmentation job."""

    # Create job record
    job = ProcessingJob(
        id=str(uuid4()),
        user_id=current_user.id,
        image_id=image_id,
        task_type="segmentation",
        status="pending",
        attempt_count=0
    )
    db.add(job)
    await db.commit()

    # Submit to Celery
    try:
        task = segment_iris_task.apply_async(
            args=[image_id],
            task_id=job.id,
            priority=9
        )
        return {"job_id": job.id, "status": "pending"}

    except MaxRetriesExceededError:
        # All retries exhausted — update job status
        job.status = "failed"
        job.error_message = "Processing failed after multiple attempts. Please try capturing a new photo in better lighting."
        await db.commit()
        raise HTTPException(status_code=500, detail=job.error_message)
```

### Pattern 5: Quality Gating (Optional)

**What:** AI evaluates output quality before showing to user; re-process or show warning if quality below threshold

**When to use:** When you want to ensure users only see high-quality results, not AI failures

**Why controversial:** Adds processing time, and "what is good quality?" is subjective. User constraint gives Claude discretion on this.

**Example:**
```python
# app/workers/tasks/quality_gating.py
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import peak_signal_noise_ratio as psnr

def evaluate_iris_segmentation_quality(segmented_image, original_image) -> dict:
    """
    Evaluate segmentation quality using image metrics.
    Returns quality score and decision (accept/reject/warning).
    """
    # Calculate SSIM (structural similarity) — higher is better (0-1)
    # Not comparing to original, but checking for artifacts
    gray_seg = cv2.cvtColor(segmented_image, cv2.COLOR_RGB2GRAY)

    # Check for common failure modes
    checks = {
        'has_iris': check_iris_detected(segmented_image),  # Did we find anything?
        'sharpness': calculate_sharpness(gray_seg),         # Is it blurry?
        'contrast': calculate_contrast(gray_seg),           # Is it washed out?
        'coverage': calculate_iris_coverage(segmented_image),  # How much of image is iris?
    }

    # Simple scoring heuristic
    if not checks['has_iris']:
        return {'quality_score': 0, 'decision': 'reject', 'reason': 'iris_not_found'}

    if checks['sharpness'] < 100:  # Laplacian variance threshold
        return {'quality_score': 0.3, 'decision': 'warning', 'reason': 'image_blurry'}

    if checks['coverage'] < 0.1:  # Iris covers less than 10% of image
        return {'quality_score': 0.4, 'decision': 'warning', 'reason': 'iris_too_small'}

    # All checks passed
    quality_score = (checks['sharpness'] / 300) * 0.5 + checks['contrast'] * 0.3 + checks['coverage'] * 0.2
    return {'quality_score': quality_score, 'decision': 'accept', 'reason': None}

@celery_app.task(bind=True, base=RetryableTask)
def segment_iris_task_with_quality_gate(self, image_id: str):
    """Segment iris with quality gating."""

    # ... segmentation logic ...

    # Evaluate quality
    quality = evaluate_iris_segmentation_quality(segmented_image, original_image)

    if quality['decision'] == 'reject':
        # Fail task with helpful error
        raise ValueError(f"Iris not detected clearly. {quality['reason']}")

    # Return result with quality metadata
    return {
        'result_url': result_url,
        'progress': 100,
        'quality_score': quality['quality_score'],
        'quality_warning': quality['reason'] if quality['decision'] == 'warning' else None
    }
```

**Recommendation:** Start without quality gating (ship faster, see real user data). Add in Phase 3 iteration if failure rate is high (>10%). Quality gating adds 100-500ms per task and complicates error handling.

### Anti-Patterns to Avoid

- **Loading models per-task**: Adds 3-10 seconds per task, kills performance
- **Synchronous processing in API endpoint**: Blocks FastAPI event loop, poor scalability
- **HTTP polling for progress**: Hundreds of wasteful requests, slower than WebSocket, drains battery
- **No priority queues**: Batch jobs block user-initiated processing, poor UX
- **Storing processed images in database**: Database bloat, slow queries, expensive backups — use S3
- **No retry logic**: Transient failures (GPU timeout, S3 network hiccup) permanently fail jobs
- **Trusting AI output without validation**: Models fail silently, users see garbage, poor experience
- **Using full-resolution images for all steps**: Wastes GPU memory, slows processing — downscale when possible
- **Ignoring mobile backgrounding**: User navigates away, loses connection, job completes but no notification
- **Technical error messages**: "CUDA out of memory" means nothing to users — map to friendly suggestions

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Image upscaling | Custom super-resolution model | Real-ESRGAN pre-trained models | Real-ESRGAN is battle-tested, 4x/8x upscaling with pre-trained weights, open-source, widely used in production |
| Model inference optimization | Manual quantization, graph optimization | ONNX Runtime with pre-built optimizations | ONNX Runtime applies graph optimizations, constant folding, hardware accelerator integration automatically |
| Task queue with retries | Custom retry logic with time.sleep | Celery autoretry_for with exponential backoff | Celery handles retry scheduling, backoff calculation, jitter, max retries — robust and proven |
| Real-time progress updates | Custom polling with setTimeout | WebSocket for push updates | WebSocket is standard, lower latency, less bandwidth, better mobile battery life |
| Job state management | In-memory dictionaries or Redis keys | Celery result backend with PostgreSQL job tracking | Celery result backend handles state persistence, task cleanup, result expiration automatically |
| Image preprocessing pipeline | Custom resize, normalize, tensor conversion | torchvision.transforms or albumentations | These libraries handle edge cases, GPU acceleration, batch processing correctly |
| Quality metrics (SSIM, PSNR) | Manual pixel comparison | scikit-image metrics | These metrics have optimized implementations, handle edge cases, widely validated |
| Notification on job completion | Custom in-app polling + state management | Push notifications via Firebase Cloud Messaging | FCM handles background notifications, delivery guarantees, cross-platform compatibility |

**Key insight:** AI model inference is the easy part. Production challenges are: loading models efficiently, handling failures gracefully, tracking job state reliably, and delivering results with great UX. Use battle-tested libraries for these "unsexy" problems so you can focus on model quality and user experience.

## Common Pitfalls

### Pitfall 1: Model Loading Overhead Kills Performance

**What goes wrong:** Loading PyTorch/ONNX model from disk for every Celery task adds 3-10 seconds of overhead per job. Users see "Processing..." for 10 seconds before actual inference even starts.

**Why it happens:** Models are 100MB-500MB weights files that must be read from disk, deserialized, and moved to GPU memory. Developers test with single tasks and don't notice overhead, but in production with queued tasks, loading time dominates total time.

**How to avoid:** Load models once at Celery worker startup, store in class variable or module-level variable, reuse across all tasks in that worker process. Use `ModelCache` pattern (see Pattern 1 above).

**Warning signs:** Task logs show "Loading model..." before every task execution. Task duration is 10-15 seconds but actual inference is only 2-3 seconds. GPU utilization spikes briefly then drops to zero (loading from CPU to GPU repeatedly).

### Pitfall 2: Synchronous Processing in FastAPI Endpoint

**What goes wrong:** Running AI inference directly in FastAPI endpoint blocks the event loop, preventing FastAPI from handling other requests. User waits 10-30 seconds for HTTP response. Server becomes unresponsive under load.

**Why it happens:** Developers see "async def" in FastAPI and assume it's non-blocking, but CPU-bound operations (model inference) still block the event loop. Python's GIL prevents true parallelism.

**How to avoid:** Offload all AI processing to Celery workers. FastAPI endpoint should only: create job record, submit to Celery queue, return job_id immediately (<100ms). User tracks progress via WebSocket, gets result when Celery task completes.

**Warning signs:** API endpoint response times >5 seconds. FastAPI handles only 1-2 requests per second. CPU usage 100% on API server. Users complain about slow response.

### Pitfall 3: HTTP Polling Instead of WebSocket

**What goes wrong:** Mobile client polls GET /jobs/{id}/status every 1-2 seconds. Generates hundreds of API requests per job. Adds 1-2 second delay to progress updates. Drains mobile battery. Wastes bandwidth.

**Why it happens:** WebSocket seems more complex than HTTP polling. Developers build polling first, then never upgrade to WebSocket.

**How to avoid:** Implement WebSocket progress streaming from day 1. It's architecturally simpler to build it in initially than to retrofit later. FastAPI has native WebSocket support, no external dependencies needed.

**Warning signs:** API logs show GET /jobs/{id}/status requests every second. Mobile battery drain complaints. Users see progress bar updates with noticeable delay (jumps from 30% to 50% instead of smooth increment).

### Pitfall 4: No Priority Queues (FIFO Only)

**What goes wrong:** User-initiated processing (high priority) waits behind batch analytics jobs (low priority). User taps "Process" and waits 5 minutes because system is running 100 batch jobs. Poor UX, user abandons app.

**Why it happens:** Default Celery configuration uses single FIFO queue. All tasks are equal priority. Developers don't anticipate mixed workload (interactive + batch).

**How to avoid:** Configure priority queues from day 1. Route user-initiated tasks to high-priority queue, batch jobs to low-priority queue. Deploy more workers for high-priority queue.

**Warning signs:** User complaints about slow processing during batch job runs. Queue depth grows to 100+ tasks. High-priority tasks sit in queue for minutes.

### Pitfall 5: No Retry Logic for Transient Failures

**What goes wrong:** GPU runs out of memory during inference, task fails permanently. S3 connection times out during image load, task fails permanently. User sees "Processing failed" even though retry would have succeeded.

**Why it happens:** Developers test in clean environment without resource contention. Don't anticipate transient failures (network hiccups, GPU OOM, concurrent task conflicts).

**How to avoid:** Use Celery's `autoretry_for` with exponential backoff and jitter. Retry on ConnectionError, TimeoutError, RuntimeError. Don't retry on ValueError (quality issues — those won't improve with retry).

**Warning signs:** High task failure rate (>10%) during peak load. Users report intermittent "Processing failed" errors that go away when retrying manually. Logs show "CUDA out of memory" or "Connection timed out" followed by permanent failure.

### Pitfall 6: Ignoring Mobile App Backgrounding

**What goes wrong:** User submits job, backgrounds app (switches to another app or locks phone), processing completes, but user never sees result. No notification, no indication job finished. User returns to app hours later wondering why nothing happened.

**Why it happens:** Developers test with app foregrounded throughout entire processing flow. Don't test backgrounding, don't implement push notifications.

**How to avoid:** Implement push notifications for job completion. Use Firebase Cloud Messaging (FCM) to send notification when task state changes to 'completed'. Show notification even if app is backgrounded. When user taps notification, deep-link to result screen.

**Warning signs:** Users report "I processed a photo but never saw the result." Analytics show high drop-off between job submission and result viewing. No notification infrastructure in place.

### Pitfall 7: Trusting AI Output Without Validation

**What goes wrong:** Segmentation model fails to find iris (returns blank mask), but task completes successfully and shows user a blank image. Reflection removal introduces artifacts, but user sees corrupted output. Enhancement model crashes on certain image sizes, but error is swallowed.

**Why it happens:** Developers assume AI models work perfectly. Don't validate output before showing to user. Don't handle edge cases (no iris detected, low quality input, unsupported image size).

**How to avoid:** Validate model output before marking task as successful. Check: (1) segmentation mask is not empty, (2) mask covers reasonable portion of image (10%+), (3) output image has reasonable dimensions, (4) no NaN or inf values in output. Raise ValueError with helpful message if validation fails.

**Warning signs:** Users report seeing blank images or corrupted results. High proportion of "meaningless" results. No quality checks in task code.

### Pitfall 8: Using Full-Resolution Images Unnecessarily

**What goes wrong:** Segmentation model runs on 4000x3000px original image, taking 15 seconds and consuming 8GB GPU memory. Multiple concurrent tasks cause out-of-memory errors.

**Why it happens:** Developers don't realize segmentation models work equally well at lower resolution. Modern phone cameras produce 12MP-48MP images, but segmentation only needs 512x512px-1024x1024px.

**How to avoid:** Downscale images to model's expected input size before inference. For segmentation, 512x512px is sufficient. For enhancement, run on original resolution since that's the whole point. For reflection removal, depends on model architecture.

**Warning signs:** GPU memory errors (CUDA out of memory). Long inference times (>10s for segmentation). GPU utilization below 50% (memory-bound, not compute-bound).

### Pitfall 9: No Error Classification (All Errors Look the Same)

**What goes wrong:** User sees "Processing failed" for all errors, whether it's (1) iris not detected (quality issue, user should recapture), (2) GPU out of memory (server issue, retry will help), or (3) S3 connection failed (transient network issue, retry will help). User doesn't know what to do.

**Why it happens:** Developers catch all exceptions as Exception and return generic error message. Don't classify errors by type or actionability.

**How to avoid:** Classify errors into categories: (1) Quality errors (ValueError) → show actionable message ("Iris not detected. Try better lighting"), don't retry, link to camera. (2) Transient errors (ConnectionError, TimeoutError) → auto-retry, show "Processing..." again. (3) Server errors (RuntimeError, OOM) → auto-retry once, then show "Server busy, please try again later".

**Warning signs:** All error messages say "Processing failed" or "An error occurred". Users don't know whether to retry, recapture, or wait. Support tickets say "I got an error but don't know what it means."

### Pitfall 10: Forgetting to Clean Up Failed Jobs

**What goes wrong:** Failed tasks leave partial results in S3 (segmented image but no enhancement). Database fills with "pending" jobs that will never complete. Redis fills with expired task results.

**Why it happens:** Developers implement happy path (success case) but don't implement cleanup on failure. No scheduled task to purge old jobs.

**How to avoid:** Implement cleanup logic: (1) On task failure, delete any partial S3 objects created during task. (2) Add Celery Beat periodic task to purge jobs older than 7 days with status 'pending' or 'failed'. (3) Configure Celery result expiration (result_expires=86400 for 24 hours).

**Warning signs:** S3 bucket grows with orphaned files. Database queries slow down due to millions of old job records. Redis memory usage grows indefinitely.

## Code Examples

Verified patterns from research:

### Complete Segmentation Task with Progress Updates

```python
# app/workers/tasks/iris_segmentation.py
from celery import Task
from app.workers.celery_app import celery_app
from app.workers.models.model_cache import ModelCache
from app.storage.s3 import load_image_from_s3, save_result_to_s3
import cv2
import numpy as np

class SegmentationTask(Task):
    """Base task for iris segmentation with retry configuration."""
    autoretry_for = (ConnectionError, TimeoutError, RuntimeError)
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True
    max_retries = 3

@celery_app.task(bind=True, base=SegmentationTask, name='segment_iris')
def segment_iris_task(self, image_id: str, user_id: str):
    """
    Segment iris from captured photo.

    Progress updates:
    - 10%: Loading image from S3
    - 30%: Preprocessing (resize, normalize)
    - 50-70%: Running segmentation model
    - 80%: Postprocessing (smooth mask, extract iris)
    - 90%: Saving result to S3
    - 100%: Complete
    """

    try:
        # Step 1: Load image
        self.update_state(state='PROGRESS', meta={
            'step': 'loading',
            'progress': 10,
            'message': 'Loading your image...'
        })
        original_image = load_image_from_s3(image_id)

        # Step 2: Preprocess
        self.update_state(state='PROGRESS', meta={
            'step': 'preparing',
            'progress': 30,
            'message': 'Preparing your image...'
        })

        # Resize to model input size (512x512)
        h, w = original_image.shape[:2]
        target_size = 512
        scale = target_size / max(h, w)
        resized = cv2.resize(original_image, None, fx=scale, fy=scale)

        # Pad to square
        padded = np.zeros((target_size, target_size, 3), dtype=np.uint8)
        y_offset = (target_size - resized.shape[0]) // 2
        x_offset = (target_size - resized.shape[1]) // 2
        padded[y_offset:y_offset+resized.shape[0], x_offset:x_offset+resized.shape[1]] = resized

        # Normalize to [0, 1]
        input_tensor = padded.astype(np.float32) / 255.0
        input_tensor = np.transpose(input_tensor, (2, 0, 1))  # HWC -> CHW
        input_tensor = np.expand_dims(input_tensor, axis=0)  # Add batch dimension

        # Step 3: Run segmentation
        self.update_state(state='PROGRESS', meta={
            'step': 'finding_iris',
            'progress': 50,
            'message': 'Finding your iris...'
        })

        model = ModelCache.get_segmentation_model()
        output = model.run(None, {'input': input_tensor})[0]

        self.update_state(state='PROGRESS', meta={
            'step': 'finding_iris',
            'progress': 70,
            'message': 'Finding your iris...'
        })

        # Step 4: Postprocess
        self.update_state(state='PROGRESS', meta={
            'step': 'finalizing',
            'progress': 80,
            'message': 'Almost done...'
        })

        # Extract mask (assuming model outputs [B, 1, H, W])
        mask = output[0, 0]  # Remove batch and channel dims
        mask = (mask > 0.5).astype(np.uint8) * 255  # Threshold and convert to binary

        # Unpad and resize back to original size
        mask = mask[y_offset:y_offset+resized.shape[0], x_offset:x_offset+resized.shape[1]]
        mask = cv2.resize(mask, (w, h))

        # Validate mask (check if iris was actually detected)
        if mask.sum() < (h * w * 0.05):  # Iris should cover at least 5% of image
            raise ValueError("Iris not detected clearly. Make sure your eye is centered and well-lit.")

        # Apply mask to original image
        segmented = cv2.bitwise_and(original_image, original_image, mask=mask)

        # Step 5: Save result
        self.update_state(state='PROGRESS', meta={
            'step': 'saving',
            'progress': 90,
            'message': 'Almost done...'
        })

        result_url = save_result_to_s3(segmented, image_id, stage='segmented')
        mask_url = save_result_to_s3(mask, image_id, stage='mask')

        return {
            'progress': 100,
            'result_url': result_url,
            'mask_url': mask_url,
            'iris_coverage': mask.sum() / (h * w * 255),  # Proportion of image that is iris
            'original_size': {'width': w, 'height': h}
        }

    except ValueError as e:
        # Quality issue — don't retry, show helpful error
        return {
            'error': 'quality_issue',
            'message': str(e),
            'suggestion': 'Try capturing a new photo in better lighting with your eye centered.'
        }

    except Exception as e:
        # Transient error — will be auto-retried by autoretry_for
        raise
```

### Real-ESRGAN Enhancement Task

```python
# app/workers/tasks/enhancement.py
from app.workers.celery_app import celery_app
from app.workers.models.model_cache import ModelCache
from app.storage.s3 import load_image_from_s3, save_result_to_s3
import cv2
import numpy as np

@celery_app.task(bind=True, name='enhance_iris')
def enhance_iris_task(self, segmented_image_id: str, user_id: str):
    """
    Enhance iris quality using Real-ESRGAN 4x upscaling.
    """

    try:
        # Load segmented image
        self.update_state(state='PROGRESS', meta={
            'step': 'loading',
            'progress': 10,
            'message': 'Preparing to enhance...'
        })
        segmented_image = load_image_from_s3(segmented_image_id)

        # Get Real-ESRGAN model
        self.update_state(state='PROGRESS', meta={
            'step': 'enhancing',
            'progress': 30,
            'message': 'Enhancing quality...'
        })
        enhancer = ModelCache.get_enhancement_model()

        # Run enhancement (this is the slow part, 3-8 seconds on GPU)
        enhanced_image, _ = enhancer.enhance(segmented_image, outscale=4)

        self.update_state(state='PROGRESS', meta={
            'step': 'enhancing',
            'progress': 80,
            'message': 'Enhancing quality...'
        })

        # Save enhanced image
        self.update_state(state='PROGRESS', meta={
            'step': 'saving',
            'progress': 90,
            'message': 'Almost done...'
        })
        result_url = save_result_to_s3(enhanced_image, segmented_image_id, stage='enhanced')

        return {
            'progress': 100,
            'result_url': result_url,
            'upscale_factor': 4,
            'output_size': {
                'width': enhanced_image.shape[1],
                'height': enhanced_image.shape[0]
            }
        }

    except Exception as e:
        raise
```

### WebSocket Progress Endpoint

```python
# app/api/routes/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from celery.result import AsyncResult
from app.workers.celery_app import celery_app
from app.api.deps import get_current_user
import asyncio
from datetime import datetime

router = APIRouter()

@router.websocket("/ws/jobs/{job_id}")
async def job_progress_websocket(
    websocket: WebSocket,
    job_id: str,
    # Note: WebSocket doesn't support Authorization header the same way,
    # would need token in query param or initial message
):
    """Real-time progress updates for processing job."""
    await websocket.accept()

    try:
        result = AsyncResult(job_id, app=celery_app)

        while not result.ready():
            state = result.state
            info = result.info if isinstance(result.info, dict) else {}

            # Send progress update
            await websocket.send_json({
                'job_id': job_id,
                'status': state.lower(),
                'progress': info.get('progress', 0),
                'step': info.get('message', 'Processing...'),
                'timestamp': datetime.utcnow().isoformat()
            })

            await asyncio.sleep(0.5)

        # Job complete — send final result
        if result.successful():
            await websocket.send_json({
                'job_id': job_id,
                'status': 'completed',
                'progress': 100,
                'result': result.result,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            # Job failed
            error_info = result.info if isinstance(result.info, dict) else {'error': str(result.info)}
            await websocket.send_json({
                'job_id': job_id,
                'status': 'failed',
                'error': error_info.get('error', 'unknown'),
                'message': error_info.get('message', 'Processing failed'),
                'suggestion': error_info.get('suggestion'),
                'timestamp': datetime.utcnow().isoformat()
            })

    except WebSocketDisconnect:
        # Client disconnected — job continues in background
        pass
    except Exception as e:
        await websocket.send_json({
            'status': 'error',
            'message': str(e)
        })
    finally:
        await websocket.close()
```

### Job Submission API Endpoint

```python
# app/api/routes/processing.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.processing_job import ProcessingJob
from app.workers.tasks.iris_segmentation import segment_iris_task
from app.schemas.processing import JobResponse
from uuid import uuid4

router = APIRouter()

@router.post("/process/segment", response_model=JobResponse)
async def submit_segmentation_job(
    image_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Submit iris segmentation job.
    Returns job_id immediately, user tracks progress via WebSocket.
    """

    # Create job record
    job = ProcessingJob(
        id=str(uuid4()),
        user_id=current_user.id,
        image_id=image_id,
        task_type="segmentation",
        status="pending",
        attempt_count=0
    )
    db.add(job)
    await db.commit()

    # Submit to Celery high-priority queue
    task = segment_iris_task.apply_async(
        args=[image_id, current_user.id],
        task_id=job.id,
        priority=9,
        queue='high_priority'
    )

    return {
        'job_id': job.id,
        'status': 'pending',
        'websocket_url': f'/ws/jobs/{job.id}'
    }

@router.post("/process/batch", response_model=list[JobResponse])
async def submit_batch_processing(
    image_ids: list[str],
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Submit batch of images for processing.
    User constraint: Batch queue supported.
    """

    if len(image_ids) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 images per batch")

    jobs = []
    for image_id in image_ids:
        job = ProcessingJob(
            id=str(uuid4()),
            user_id=current_user.id,
            image_id=image_id,
            task_type="segmentation",
            status="pending"
        )
        db.add(job)

        # Submit with slight priority decrement so first job in batch has highest priority
        segment_iris_task.apply_async(
            args=[image_id, current_user.id],
            task_id=job.id,
            priority=9 - len(jobs),  # 9, 8, 7, ... descending
            queue='high_priority'
        )

        jobs.append(job)

    await db.commit()

    return [
        {
            'job_id': job.id,
            'status': 'pending',
            'websocket_url': f'/ws/jobs/{job.id}'
        }
        for job in jobs
    ]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Native PyTorch inference | ONNX Runtime with optimizations | 2023-2024 | 2-3x speedup, hardware accelerator support, smaller model size |
| HTTP long-polling for progress | WebSocket push updates | 2023+ | Instant updates, less bandwidth, better mobile battery, simpler server-side |
| Single FIFO task queue | Priority queues (high/normal/low) | 2024+ | User tasks complete faster, better resource allocation, separate SLAs |
| Manual retry logic | Celery autoretry_for with exponential backoff | 2024+ | Automatic retry, jitter prevents thundering herd, configurable max retries |
| U-Net (2015 architecture) | U-Net with attention mechanisms, DeepLabV3+ | 2023-2025 | Higher accuracy (95%+ mIoU), better handling of challenging cases |
| Traditional inpainting for reflection removal | Transformer-based reflection removal (LapCAT) | 2025 | Better high-res handling, fewer artifacts, but requires custom training |
| ESRGAN (2018) | Real-ESRGAN (2021, still current 2026) | 2021 | Better real-world degradation handling, pre-trained on diverse datasets |
| Manual progress tracking in Redis | Celery task state updates with custom metadata | 2023+ | Built-in state management, easier to implement, more reliable |

**Deprecated/outdated:**
- **Manual task result storage in Redis**: Use Celery result backend, handles expiration and cleanup automatically
- **Synchronous processing in API endpoints**: Use async task queue (Celery), mandatory for AI workloads
- **Polling for job status**: Use WebSocket, standard practice in 2026
- **Loading models per-task**: Load once at worker startup, cache in memory

## Open Questions

1. **Reflection Removal Model Selection**
   - What we know: LapCAT (2025) is state-of-art transformer for high-res reflection removal
   - What's unclear: Whether pre-trained models exist, or if we need to train on iris-specific dataset. Training requires paired data (with/without reflections).
   - Recommendation: Start with traditional inpainting (OpenCV) for MVP. If quality insufficient, evaluate LapCAT pre-trained models. Custom training is Phase 4+ work.

2. **U-Net vs DeepLabV3+ for Segmentation**
   - What we know: U-Net achieves 98.9%+ IoU, DeepLabV3+ achieves 95.54% mIoU with faster inference
   - What's unclear: Which performs better on mobile-captured iris photos (vs research datasets with controlled lighting)
   - Recommendation: Start with U-Net (higher accuracy, proven), A/B test DeepLabV3+ if inference time is bottleneck (>5s per image)

3. **Quality Gating Threshold**
   - What we know: Can use SSIM, PSNR, or custom metrics (sharpness, contrast, iris coverage) to evaluate output quality
   - What's unclear: What threshold distinguishes "acceptable" vs "reject and suggest recapture"? This is subjective.
   - Recommendation: Don't implement quality gating in MVP. Ship, collect real data (what do users keep vs delete?), set threshold based on actual user behavior.

4. **Push Notification Implementation**
   - What we know: Need to notify user when background processing completes
   - What's unclear: Firebase Cloud Messaging setup, notification permissions, deep-linking to result screen
   - Recommendation: Research FCM integration separately (may be Phase 4+ feature). For MVP, show in-app indicator when user returns to app.

5. **Batch Processing Priority**
   - What we know: User can submit batch of 10 images, each creates separate job
   - What's unclear: Should first image in batch have higher priority than last? Or all same priority?
   - Recommendation: Slight descending priority (first=9, last=0) so results arrive in order user selected. Prevents confusing UX where results appear randomly.

6. **Cleanup Strategy for Failed Jobs**
   - What we know: Need to delete partial S3 objects, purge old job records
   - What's unclear: How long to retain failed jobs? Immediate cleanup or keep for debugging?
   - Recommendation: Keep failed jobs for 7 days (for debugging), then purge. Delete partial S3 objects immediately on failure (within task's error handler).

## Sources

### Primary (HIGH confidence)

- [ONNX Runtime PyTorch Inference Tutorial](https://onnxruntime.ai/docs/tutorials/accelerate-pytorch/pytorch.html) - Official docs on PyTorch to ONNX conversion and optimization
- [ONNX Runtime Performance Analysis](https://medium.com/@deeplch/the-beginners-guide-cpu-inference-optimization-with-onnx-99-8-tf-20-5-pytorch-speedup-83fd5cd38615) - 20.5% PyTorch speedup, 99.8% TF speedup benchmarks
- [Real-ESRGAN GitHub Repository](https://github.com/xinntao/Real-ESRGAN) - Official implementation, pre-trained models, usage examples
- [Celery Task Routing and Retries](https://usmanasifbutt.github.io/blog/2025/03/13/celery-task-routing-and-retries.html) - Priority queues, exponential backoff, error handling patterns (2025)
- [Celery Automatic Retry Documentation](https://docs.celeryq.dev/en/stable/userguide/tasks.html) - Official Celery docs on autoretry_for, retry_backoff
- [FastAPI WebSocket with Celery Progress](https://celery.school/celery-progress-bars-with-fastapi-htmx) - WebSocket progress streaming pattern
- [Deep Learning for Iris Recognition Survey (ACM 2025)](https://dl.acm.org/doi/10.1145/3651306) - Comprehensive survey of iris segmentation models
- [Robust Iris Segmentation with U-Net (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7922029/) - U-Net achieving 98.9%+ IoU
- [LapCAT: High-Resolution Reflection Removal (Nature 2025)](https://www.nature.com/articles/s41598-025-94464-6) - Transformer-based reflection removal

### Secondary (MEDIUM confidence)

- [Using FastAPI with SocketIO for Real-Time Progress (Medium 2024)](https://medium.com/@eng.fadishaar/using-fastapi-with-socketio-to-display-real-time-progress-of-celery-tasks-87c16d538571) - Alternative to WebSocket using SocketIO
- [React Native Background Tasks 2026 (DEV Community)](https://dev.to/eira-wexford/run-react-native-background-tasks-2026-for-optimal-performance-d26) - Background processing best practices
- [React Native Push Notifications with FCM (React Native Firebase)](https://rnfirebase.io/messaging/usage) - Firebase Cloud Messaging integration
- [React Native Before/After Slider Libraries (Croct Blog 2026)](https://blog.croct.com/post/best-react-before-after-image-comparison-slider-libraries) - UI component research
- [Celery Priority Queues (Appliku)](https://appliku.com/post/celery-task-priority/) - Priority queue configuration
- [PyTorch Model Checkpointing Best Practices (PyTorch Docs)](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html) - Loading models with weights_only=True

### Tertiary (LOW confidence - marked for validation)

- [Iris Segmentation with DeepLabV3+ (GitHub)](https://github.com/naveen-purohit/Iris-Segmentation-through-deep-learning-UNet) - Community implementation, not peer-reviewed
- [RABRRN: Reflection Removal (MDPI 2023)](https://www.mdpi.com/2076-3417/13/3/1618) - Earlier reflection removal approach, pre-transformer era

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - ONNX Runtime, Real-ESRGAN, Celery patterns verified from official docs and production usage
- Architecture: HIGH - WebSocket progress, model caching, priority queues are industry-standard patterns
- Pitfalls: HIGH - Model loading overhead, synchronous processing, HTTP polling are well-documented anti-patterns
- AI models: HIGH (Real-ESRGAN), HIGH (U-Net/DeepLabV3+ for iris), MEDIUM (reflection removal — newer research)
- Mobile integration: MEDIUM - Push notifications and background processing need separate research/testing

**Research date:** 2026-02-09
**Valid until:** 2026-03-09 (30 days — AI model landscape evolving, but ONNX Runtime and Celery patterns stable)

**Notes for planner:**
- Celery + Redis already in stack from Phase 1, no new infrastructure needed
- FastAPI WebSocket is built-in, no additional dependencies
- AI models (U-Net, Real-ESRGAN) have pre-trained weights available, don't need training from scratch
- Mobile client already has React Query (Phase 2) for API calls, can extend for WebSocket
- Quality gating is discretionary — recommend deferring to Phase 3 iteration based on real failure data
- Push notifications (FCM) may be separate Phase 4+ feature — in-app indicator sufficient for MVP
