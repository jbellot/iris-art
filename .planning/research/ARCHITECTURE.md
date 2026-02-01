# Architecture Research

**Domain:** AI-powered mobile image processing (iris photography)
**Researched:** 2026-02-01
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          MOBILE CLIENT LAYER                             │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │ Camera Module  │  │  Gallery UI    │  │  Social UI     │            │
│  │ + ML Guidance  │  │  + Previews    │  │  + Circles     │            │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘            │
│          │                   │                   │                      │
│          └───────────────────┴───────────────────┘                      │
│                              │                                           │
│                        REST API / WebSocket                              │
│                              │                                           │
├──────────────────────────────┴───────────────────────────────────────────┤
│                         API GATEWAY LAYER                                │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  FastAPI Server (async/await)                                    │   │
│  │  - Auth endpoints (OAuth2 + Social Login)                        │   │
│  │  - Image upload/download endpoints                               │   │
│  │  - Job status/progress endpoints (WebSocket)                     │   │
│  │  - Social features endpoints (circles, galleries)                │   │
│  │  - Payment endpoints (Stripe integration)                        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────────────────────┤
│                     BACKGROUND PROCESSING LAYER                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │ Celery Workers │  │ Celery Workers │  │ Celery Workers │            │
│  │ (High Priority)│  │ (Normal Prio)  │  │ (Low Priority) │            │
│  │ - Segmentation │  │ - Enhancement  │  │ - Batch Jobs   │            │
│  │ - Real-time    │  │ - Style Trans  │  │ - Analytics    │            │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘            │
│          │                   │                   │                      │
│          └───────────────────┴───────────────────┘                      │
│                              │                                           │
│                        Redis (Message Broker)                            │
│                       + Result Backend                                   │
├──────────────────────────────────────────────────────────────────────────┤
│                          DATA LAYER                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ PostgreSQL   │  │ S3/Cloud     │  │ Redis Cache  │                  │
│  │ - Users      │  │ - Original   │  │ - Sessions   │                  │
│  │ - Metadata   │  │   images     │  │ - Task state │                  │
│  │ - Circles    │  │ - Processed  │  │ - API cache  │                  │
│  │ - Jobs       │  │   images     │  │              │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└──────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Mobile Client** | Camera capture, real-time guidance overlay, UI/UX, local caching | React Native (recommended) or Flutter with Vision Camera plugin |
| **FastAPI Server** | REST API endpoints, request validation, authentication, job orchestration | FastAPI with async/await, Pydantic models, OAuth2 middleware |
| **Celery Workers** | Async AI processing (segmentation, enhancement, style transfer), background tasks | Celery with Redis broker, multiple priority queues |
| **Redis** | Message broker for job queues, result backend, session storage, API caching | Redis 7.x with persistence enabled |
| **PostgreSQL** | User data, image metadata, social features (circles), job tracking | PostgreSQL 15+ with UUID primary keys |
| **S3/Cloud Storage** | Binary image storage (original + processed), CDN origin | AWS S3, Cloudflare R2, or similar with CloudFront CDN |
| **AI Models** | Iris segmentation (U-Net), enhancement, style transfer, generation | PyTorch/TensorFlow models served by workers |

## Recommended Project Structure

### Backend (Python/FastAPI)
```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py           # OAuth2, Apple/Google Sign In
│   │   │   │   ├── images.py         # Upload/download endpoints
│   │   │   │   ├── processing.py     # Job submission/status
│   │   │   │   ├── social.py         # Circles, galleries
│   │   │   │   └── payments.py       # Stripe integration
│   │   │   ├── deps.py               # Dependencies (DB session, auth)
│   │   │   └── router.py             # Main router
│   ├── core/
│   │   ├── config.py                 # Settings (Pydantic BaseSettings)
│   │   ├── security.py               # JWT, OAuth2 flows
│   │   └── storage.py                # S3/cloud storage client
│   ├── db/
│   │   ├── models.py                 # SQLAlchemy models
│   │   ├── session.py                # DB connection
│   │   └── migrations/               # Alembic migrations
│   ├── schemas/
│   │   ├── user.py                   # Pydantic schemas
│   │   ├── image.py
│   │   └── job.py
│   ├── services/
│   │   ├── auth_service.py           # Business logic
│   │   ├── image_service.py
│   │   └── social_service.py
│   ├── workers/
│   │   ├── celery_app.py             # Celery configuration
│   │   ├── tasks/
│   │   │   ├── iris_segmentation.py  # AI processing tasks
│   │   │   ├── enhancement.py
│   │   │   ├── style_transfer.py
│   │   │   └── fusion.py
│   │   └── models/
│   │       ├── segmentation_model.py # Model loading/inference
│   │       ├── enhancement_model.py
│   │       └── style_model.py
│   └── main.py                       # FastAPI app entry point
├── tests/
├── alembic.ini
├── requirements.txt
└── docker-compose.yml                # Local dev: API + Redis + Postgres
```

### Mobile (React Native - Recommended)
```
mobile/
├── src/
│   ├── screens/
│   │   ├── CameraScreen.tsx          # Real-time camera with guidance
│   │   ├── GalleryScreen.tsx         # User's iris collection
│   │   ├── ProcessingScreen.tsx      # Style selection + progress
│   │   ├── CirclesScreen.tsx         # Social features
│   │   └── ProfileScreen.tsx
│   ├── components/
│   │   ├── IrisGuidanceOverlay.tsx   # SVG overlay for alignment
│   │   ├── ImageCard.tsx
│   │   └── ProgressIndicator.tsx
│   ├── navigation/
│   │   └── AppNavigator.tsx          # React Navigation
│   ├── services/
│   │   ├── api.ts                    # Axios/fetch API client
│   │   ├── auth.ts                   # Apple/Google Sign In
│   │   ├── camera.ts                 # react-native-vision-camera
│   │   ├── websocket.ts              # WebSocket for progress
│   │   └── storage.ts                # AsyncStorage
│   ├── hooks/
│   │   ├── useCamera.ts              # Camera permissions/control
│   │   ├── useImageUpload.ts         # Upload with progress
│   │   └── useJobProgress.ts         # WebSocket job tracking
│   ├── store/
│   │   ├── slices/                   # Redux Toolkit or Zustand
│   │   │   ├── authSlice.ts
│   │   │   ├── imagesSlice.ts
│   │   │   └── jobsSlice.ts
│   │   └── store.ts
│   ├── types/
│   │   ├── api.ts                    # TypeScript types matching backend
│   │   └── models.ts
│   └── utils/
│       ├── imageUtils.ts             # Compression, validation
│       └── validators.ts
├── android/
├── ios/
├── package.json
└── tsconfig.json
```

### Structure Rationale

- **Backend separation by concern**: Clear boundaries between API routes, business logic (services), data access (models), and background processing (workers). This enables independent scaling and testing.
- **Celery workers in dedicated module**: AI processing is isolated from API server, allowing separate deployment and horizontal scaling based on queue depth rather than API traffic.
- **Mobile feature-based structure**: Screens, components, and services organized by feature for easier navigation and maintenance. Shared state management via Redux Toolkit or Zustand for predictable data flow.
- **Type safety across stack**: TypeScript in mobile matches Pydantic schemas in backend for consistent API contracts and reduced runtime errors.

## Architectural Patterns

### Pattern 1: Async Job Processing with Progress Tracking

**What:** Long-running AI tasks (segmentation, style transfer) are processed asynchronously with real-time progress updates via WebSocket.

**When to use:** Any operation taking >2 seconds (iris segmentation ~5-15s, style transfer ~10-30s)

**Trade-offs:**
- **Pros:** Non-blocking API, scalable worker pool, better user experience with progress feedback
- **Cons:** Additional complexity (job tracking, WebSocket management), requires Redis for state

**Example:**
```python
# Backend: API endpoint submits job
@router.post("/process/segment")
async def segment_iris(
    image_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Create job record
    job = Job(
        id=str(uuid4()),
        user_id=current_user.id,
        image_id=image_id,
        task_type="segmentation",
        status="pending"
    )
    db.add(job)
    db.commit()

    # Submit to Celery with high priority
    task = segment_iris_task.apply_async(
        args=[image_id],
        task_id=job.id,
        priority=9  # 0-9, where 9 is highest
    )

    return {"job_id": job.id, "status": "pending"}

# Backend: Celery task with progress updates
@celery_app.task(bind=True)
def segment_iris_task(self, image_id: str):
    # Load image from S3
    self.update_state(state='PROGRESS', meta={'step': 'loading', 'progress': 10})
    image = load_from_s3(image_id)

    # Preprocess
    self.update_state(state='PROGRESS', meta={'step': 'preprocessing', 'progress': 30})
    preprocessed = preprocess_for_segmentation(image)

    # Run model inference
    self.update_state(state='PROGRESS', meta={'step': 'segmentation', 'progress': 50})
    segmented = segmentation_model.predict(preprocessed)

    # Post-process and save
    self.update_state(state='PROGRESS', meta={'step': 'saving', 'progress': 80})
    result_url = save_to_s3(segmented)

    return {"result_url": result_url, "progress": 100}

# Backend: WebSocket endpoint for progress
@app.websocket("/ws/jobs/{job_id}")
async def job_progress_websocket(
    websocket: WebSocket,
    job_id: str
):
    await websocket.accept()
    result = AsyncResult(job_id, app=celery_app)

    while not result.ready():
        state = result.state
        info = result.info if isinstance(result.info, dict) else {}
        await websocket.send_json({
            "status": state,
            "progress": info.get('progress', 0),
            "step": info.get('step', '')
        })
        await asyncio.sleep(0.5)  # Poll every 500ms

    await websocket.send_json({
        "status": "completed",
        "result": result.result
    })
    await websocket.close()
```

```typescript
// Mobile: Job submission and progress tracking
const useJobProgress = (jobId: string) => {
  const [progress, setProgress] = useState(0);
  const [step, setStep] = useState('');
  const [result, setResult] = useState(null);

  useEffect(() => {
    const ws = new WebSocket(`wss://api.irisvue.com/ws/jobs/${jobId}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data.progress);
      setStep(data.step);

      if (data.status === 'completed') {
        setResult(data.result);
        ws.close();
      }
    };

    return () => ws.close();
  }, [jobId]);

  return { progress, step, result };
};
```

### Pattern 2: Hybrid On-Device/Server Processing

**What:** Lightweight ML models run on-device for real-time guidance (iris detection, alignment); heavy processing (segmentation, style transfer) runs server-side.

**When to use:** When user experience requires instant feedback (<100ms) but processing quality requires powerful models

**Trade-offs:**
- **Pros:** Best of both worlds—instant UI feedback + high-quality results; reduced server load for simple tasks; works offline for guidance
- **Cons:** Requires maintaining two model versions; on-device models need optimization (TFLite/CoreML); larger app bundle size

**Example:**
```typescript
// Mobile: On-device iris detection for camera guidance
import { useTensorflowModel } from 'react-native-fast-tflite';

const CameraScreen = () => {
  const model = useTensorflowModel(require('./models/iris_detector_lite.tflite'));
  const device = useCameraDevice('front');

  const frameProcessor = useFrameProcessor((frame) => {
    'worklet';

    // Run lightweight iris detection model on-device
    const detections = model.runSync([frame]); // ~20-50ms

    // Check alignment
    const isAligned = checkIrisAlignment(detections);
    const isCentered = checkIrisCentered(detections);

    // Update UI overlay in real-time
    runOnJS(updateGuidanceOverlay)({
      aligned: isAligned,
      centered: isCentered,
      confidence: detections.confidence
    });
  }, [model]);

  return (
    <Camera
      device={device}
      frameProcessor={frameProcessor}
      {...otherProps}
    />
  );
};

// When user captures photo, send to server for high-quality processing
const captureAndProcess = async () => {
  const photo = await camera.current.takePhoto();

  // Upload to server
  const { job_id } = await api.post('/process/segment', {
    image: photo.path
  });

  // Track progress via WebSocket
  navigation.navigate('Processing', { jobId: job_id });
};
```

### Pattern 3: Priority-Based Job Queue

**What:** Multiple Celery queues with different priorities for different task types (real-time vs batch processing).

**When to use:** When you have tasks with varying urgency and resource requirements

**Trade-offs:**
- **Pros:** High-priority tasks (user-initiated) complete faster; efficient resource allocation; prevents batch jobs from blocking interactive tasks
- **Cons:** More complex worker configuration; need to monitor queue depths separately; potential for low-priority starvation

**Example:**
```python
# Backend: Celery configuration with priority queues
from kombu import Queue

celery_app.conf.task_queues = (
    Queue('high_priority', routing_key='high', priority=9),
    Queue('normal_priority', routing_key='normal', priority=5),
    Queue('low_priority', routing_key='low', priority=1),
)

celery_app.conf.task_routes = {
    'app.workers.tasks.iris_segmentation.*': {
        'queue': 'high_priority',
        'priority': 9
    },
    'app.workers.tasks.style_transfer.*': {
        'queue': 'normal_priority',
        'priority': 5
    },
    'app.workers.tasks.analytics.*': {
        'queue': 'low_priority',
        'priority': 1
    }
}

# Configure workers to process queues in priority order
# Worker command: celery -A app.workers.celery_app worker -Q high_priority,normal_priority,low_priority -c 4
```

**Deployment:**
```yaml
# docker-compose.yml for different worker pools
services:
  worker-high-priority:
    build: .
    command: celery -A app.workers.celery_app worker -Q high_priority -c 4 --prefetch-multiplier=1
    deploy:
      replicas: 3  # More workers for high-priority tasks

  worker-normal-priority:
    build: .
    command: celery -A app.workers.celery_app worker -Q normal_priority -c 4
    deploy:
      replicas: 2

  worker-low-priority:
    build: .
    command: celery -A app.workers.celery_app worker -Q low_priority -c 2
    deploy:
      replicas: 1
```

### Pattern 4: Image Storage with CDN Optimization

**What:** Separate S3 buckets for original and processed images; CloudFront CDN for fast global delivery; on-demand transformation for different sizes.

**When to use:** All production deployments to minimize storage costs and maximize delivery speed

**Trade-offs:**
- **Pros:** Fast global delivery via edge caching; lower storage costs (store only originals + cached variants); scalable to millions of images
- **Cons:** Cold cache performance hit on first request; CDN costs scale with traffic; requires invalidation strategy for updates

**Example:**
```python
# Backend: Storage service with CDN integration
class ImageStorageService:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.original_bucket = 'irisvue-originals'
        self.processed_bucket = 'irisvue-processed'
        self.cdn_domain = 'cdn.irisvue.com'

    async def store_original(self, image_id: str, image_data: bytes) -> str:
        """Store original high-res image"""
        key = f"originals/{image_id}.jpg"
        self.s3_client.put_object(
            Bucket=self.original_bucket,
            Key=key,
            Body=image_data,
            ContentType='image/jpeg',
            StorageClass='STANDARD'  # Hot storage for originals
        )
        return f"s3://{self.original_bucket}/{key}"

    async def store_processed(
        self,
        image_id: str,
        variant: str,  # 'segmented', 'enhanced', 'styled'
        image_data: bytes
    ) -> str:
        """Store processed variant with CDN URL"""
        key = f"{variant}/{image_id}.jpg"
        self.s3_client.put_object(
            Bucket=self.processed_bucket,
            Key=key,
            Body=image_data,
            ContentType='image/jpeg',
            CacheControl='public, max-age=31536000',  # 1 year cache
            StorageClass='STANDARD_IA'  # Cheaper for infrequent access
        )

        # Return CDN URL, not direct S3 URL
        return f"https://{self.cdn_domain}/{key}"

    def get_thumbnail_url(self, image_id: str, size: str = 'medium') -> str:
        """Return CDN URL with size transformation"""
        # CloudFront can do on-the-fly resizing via Lambda@Edge
        return f"https://{self.cdn_domain}/thumbnails/{size}/{image_id}.jpg"
```

```typescript
// Mobile: Progressive image loading with CDN
const ImageCard = ({ imageId }: { imageId: string }) => {
  return (
    <FastImage
      source={{
        uri: `https://cdn.irisvue.com/thumbnails/small/${imageId}.jpg`,
        priority: FastImage.priority.normal,
        cache: FastImage.cacheControl.immutable
      }}
      onPress={() => {
        // Load full resolution on tap
        navigation.navigate('ImageDetail', {
          fullResUrl: `https://cdn.irisvue.com/processed/enhanced/${imageId}.jpg`
        });
      }}
    />
  );
};
```

## Data Flow

### Request Flow: Iris Photo Capture → Processing → Result

```
[User captures iris photo]
        ↓
[Mobile: Compress + validate (max 10MB)]
        ↓
[POST /api/v1/images/upload]
        ↓
[FastAPI: Validate auth + file type]
        ↓
[Store original → S3 (originals bucket)]
        ↓
[Create image record → PostgreSQL]
        ↓
[Return: {image_id, upload_url}]
        ↓
[Mobile: Navigate to processing screen]
        ↓
[User selects "Segment Iris"]
        ↓
[POST /api/v1/processing/segment]
        ↓
[FastAPI: Create job record → PostgreSQL]
        ↓
[Submit task → Redis queue (high priority)]
        ↓
[Return: {job_id, websocket_url}]
        ↓
[Mobile: Connect to WebSocket]
        ↓
[Celery Worker: Pull task from queue]
        ↓
[Load original from S3 → Apply segmentation model]
        ↓
[Update state: 'preprocessing' (30%)]  ───→ [WebSocket pushes to mobile]
        ↓
[Update state: 'segmentation' (50%)]   ───→ [WebSocket pushes to mobile]
        ↓
[Update state: 'saving' (80%)]         ───→ [WebSocket pushes to mobile]
        ↓
[Store result → S3 (processed bucket)]
        ↓
[Update job record → PostgreSQL (status: 'completed')]
        ↓
[Return result: {result_url, metadata}]
        ↓
[WebSocket: Send completion + result_url]
        ↓
[Mobile: Display processed image from CDN]
```

### State Management: Mobile App

```
[App Launch]
    ↓
[Check AsyncStorage for auth token]
    ↓ (if exists)
[POST /api/v1/auth/refresh] → [Update Redux: user, token]
    ↓
[Subscribe to Redux store changes]
    ↓
┌────────────────────────────────────────────────┐
│ Redux Store (Single Source of Truth)          │
│                                                 │
│  auth: { user, token, isAuthenticated }        │
│  images: { items[], selectedId, filters }      │
│  jobs: { active[], completed[], byId{} }       │
│  circles: { userCircles[], invitations[] }     │
│  ui: { loading, error, modal }                 │
└────────────────────────────────────────────────┘
    ↓ (state changes trigger re-renders)
[React Components consume via useSelector]
    ↓
[User actions dispatch Redux actions]
    ↓
[Redux Thunks for async operations]
    ↓
[API calls via services/api.ts]
    ↓
[Update Redux state on success/failure]
```

### Data Flow: Circle Invitation → Iris Fusion

```
[User A: Create circle "Wedding Party"]
        ↓
[POST /api/v1/circles] → [PostgreSQL: circles table]
        ↓
[User A: Invite User B via email]
        ↓
[POST /api/v1/circles/{id}/invite]
        ↓
[Create invitation → PostgreSQL (status: 'pending')]
        ↓
[Send email with magic link]
        ↓
[User B: Click link → Auto-login]
        ↓
[GET /api/v1/invitations/{token}]
        ↓
[Accept invitation → Update circle_members table]
        ↓
[User B: Capture iris → Process → Add to gallery]
        ↓
[Both users now see each other's irises in circle]
        ↓
[User A: Select two irises for fusion]
        ↓
[POST /api/v1/processing/fuse]
        ↓
[Celery task: Load both images → Apply fusion algorithm → Save result]
        ↓
[Result appears in both users' galleries]
```

### Key Data Flows

1. **Authentication Flow:** Mobile app stores JWT in secure storage → sends in Authorization header → FastAPI validates via middleware → user object available in endpoints

2. **Real-time Progress Flow:** WebSocket connection established → Celery task updates Redis state → FastAPI WebSocket endpoint polls Redis → pushes updates to mobile

3. **Payment Flow:** User selects premium style → Mobile shows Stripe payment sheet → Collect payment token → Send to backend → Backend charges via Stripe API → Update user subscription in PostgreSQL → Unlock premium features

4. **Social Sharing Flow:** User shares result to circle → Create share record with permissions → Other circle members can view but not download original → Analytics tracked in PostgreSQL

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| **0-1K users** | Single server for API + workers, single Redis instance, single Postgres instance. Shared S3 bucket with simple paths. Total: 1 API server + 2 workers + managed DB/Redis/S3. Estimated cost: $50-100/mo |
| **1K-10K users** | Separate API server from workers. Add load balancer for API. Add 2-3 worker instances per priority queue. Enable Redis persistence. Postgres read replicas. CDN for image delivery. Total: 2-3 API servers + 6-9 workers + managed services. Estimated cost: $300-500/mo |
| **10K-100K users** | API autoscaling group (3-10 instances). Worker autoscaling based on queue depth (10-30 instances). Redis cluster for high availability. Postgres with connection pooling (PgBouncer). Multi-region S3 with CloudFront. Database partitioning by user_id. Estimated cost: $2K-5K/mo |
| **100K+ users** | Microservices split: Auth service, Image service, Processing service, Social service. Kubernetes for orchestration. Separate databases per service (database per service pattern). Message queue for inter-service communication. Global CDN with edge computing for image transformations. Estimated cost: $10K+/mo |

### Scaling Priorities

1. **First bottleneck: Celery workers** (AI processing is CPU/GPU intensive)
   - **Symptom:** Job queue backlog growing, long wait times for results
   - **Fix:** Add more workers (horizontal scaling), optimize model inference (batching, quantization), consider GPU instances for workers
   - **When:** Average queue time >30 seconds or queue length >50 jobs

2. **Second bottleneck: PostgreSQL connections** (FastAPI is async, creates many connections)
   - **Symptom:** Connection pool exhausted errors, slow query performance
   - **Fix:** Add PgBouncer connection pooler, optimize queries with indexes, add read replicas for analytics
   - **When:** Connection pool saturation >80% or query p95 >500ms

3. **Third bottleneck: Redis memory** (job state, cache, sessions stored in RAM)
   - **Symptom:** Redis evictions, slow task enqueuing, connection timeouts
   - **Fix:** Increase Redis instance size, enable Redis persistence with separate cache/queue instances, implement TTL policies
   - **When:** Memory usage >70% or evictions >100/min

4. **Fourth bottleneck: S3 request rate** (many concurrent uploads/downloads)
   - **Symptom:** S3 503 errors, slow image loading
   - **Fix:** Use S3 Transfer Acceleration, implement aggressive CDN caching, prefix partitioning for high throughput
   - **When:** Request rate >3500 GET/s per prefix or 5000 PUT/s per prefix

5. **Fifth bottleneck: API server CPU** (JSON serialization, request validation)
   - **Symptom:** High CPU on API servers, increased response times
   - **Fix:** Horizontal scaling with load balancer, enable response compression, optimize Pydantic models, implement Redis caching
   - **When:** CPU usage >70% or API p95 latency >1s

## Anti-Patterns

### Anti-Pattern 1: Storing Binary Images in PostgreSQL

**What people do:** Store iris photos as BYTEA or Large Objects in PostgreSQL alongside metadata

**Why it's wrong:**
- Database backups become massive and slow (GBs of image data)
- Poor performance: Image retrieval requires database query + serialization
- Expensive: Database storage costs 10-20x more than S3
- Doesn't scale: Can't leverage CDN for fast global delivery

**Do this instead:**
- Store only metadata in PostgreSQL (id, user_id, s3_key, created_at, processing_status)
- Store binary images in S3 with pre-signed URLs for secure access
- Serve via CloudFront CDN for <100ms global delivery
- Keep PostgreSQL queries fast and backups small

```python
# ❌ Anti-pattern: Binary in database
class Image(Base):
    id = Column(UUID, primary_key=True)
    image_data = Column(LargeBinary)  # Stores full image! Bad!

# ✅ Correct pattern: Metadata in database, binary in S3
class Image(Base):
    id = Column(UUID, primary_key=True)
    s3_key = Column(String)  # Just the key: "originals/uuid.jpg"
    s3_bucket = Column(String)  # "irisvue-originals"
    file_size = Column(Integer)
    content_type = Column(String)

    def get_url(self) -> str:
        return storage_service.get_signed_url(self.s3_bucket, self.s3_key)
```

### Anti-Pattern 2: Synchronous AI Processing in API Endpoints

**What people do:** Load ML model and run inference directly in FastAPI endpoint, blocking the response

**Why it's wrong:**
- User waits 10-30 seconds for HTTP response (poor UX, likely timeout)
- API server becomes CPU-bound, can't handle other requests
- No way to scale processing independently from API
- Can't retry failed jobs or track progress
- Single point of failure (if request drops, work is lost)

**Do this instead:**
- Submit job to Celery queue, immediately return job_id
- Process in background workers (separate from API servers)
- Use WebSocket for real-time progress updates
- Store job state in database for durability
- Scale workers independently based on queue depth

```python
# ❌ Anti-pattern: Synchronous processing
@app.post("/process/segment")
async def segment_iris(image_id: str):
    image = load_from_s3(image_id)  # Blocks for 1-2s
    model = load_model()  # Blocks for 3-5s (!)
    result = model.predict(image)  # Blocks for 5-10s
    save_to_s3(result)  # Blocks for 1-2s
    return {"result_url": result_url}  # Total: 10-20s response time!

# ✅ Correct pattern: Async job submission
@app.post("/process/segment")
async def segment_iris(image_id: str):
    job = create_job(image_id, task_type="segmentation")  # Fast!
    segment_iris_task.apply_async(args=[image_id], task_id=job.id)
    return {"job_id": job.id, "websocket_url": f"/ws/jobs/{job.id}"}  # <100ms
```

### Anti-Pattern 3: No Priority Queues (All Tasks Equal)

**What people do:** Use single Celery queue for all tasks (real-time user requests + batch analytics)

**Why it's wrong:**
- User-initiated tasks wait behind batch jobs (terrible UX)
- Can't scale resources based on task urgency
- One slow task blocks all subsequent tasks
- No way to guarantee SLA for interactive tasks

**Do this instead:**
- Separate queues by priority: high (user-facing), normal (automated), low (batch)
- Dedicate more workers to high-priority queue
- Set queue-specific routing in Celery config
- Monitor queue depths separately

```python
# ❌ Anti-pattern: Single queue
celery_app.conf.task_default_queue = 'default'  # Everything mixed together

# ✅ Correct pattern: Priority-based routing
celery_app.conf.task_queues = (
    Queue('high_priority', routing_key='high', priority=9),
    Queue('normal_priority', routing_key='normal', priority=5),
    Queue('low_priority', routing_key='low', priority=1),
)

celery_app.conf.task_routes = {
    'tasks.segment_iris': {'queue': 'high_priority'},  # User waiting!
    'tasks.style_transfer': {'queue': 'normal_priority'},
    'tasks.batch_analytics': {'queue': 'low_priority'},  # Can wait
}
```

### Anti-Pattern 4: Loading ML Models on Every Task

**What people do:** Load PyTorch/TensorFlow model from disk for each Celery task invocation

**Why it's wrong:**
- Model loading takes 3-10 seconds per task (huge overhead!)
- Repeated disk I/O and memory allocation
- Can't utilize GPU efficiently (constant model swapping)
- Wastes memory (model loaded/unloaded repeatedly)

**Do this instead:**
- Load models once when Celery worker starts
- Store in worker process memory
- Reuse loaded models across tasks
- For GPU workers, keep models in GPU memory

```python
# ❌ Anti-pattern: Load model every time
@celery_app.task
def segment_iris_task(image_id: str):
    model = load_segmentation_model()  # 5-10s overhead per task!
    image = load_image(image_id)
    result = model.predict(image)
    return result

# ✅ Correct pattern: Load once, reuse many times
class ModelCache:
    _segmentation_model = None
    _style_model = None

    @classmethod
    def get_segmentation_model(cls):
        if cls._segmentation_model is None:
            cls._segmentation_model = load_segmentation_model()
        return cls._segmentation_model

@celery_app.task
def segment_iris_task(image_id: str):
    model = ModelCache.get_segmentation_model()  # Fast! Already loaded
    image = load_image(image_id)
    result = model.predict(image)
    return result
```

### Anti-Pattern 5: No Image Compression Before Upload

**What people do:** Upload full-resolution 12MP camera photos directly from mobile (10-20MB each)

**Why it's wrong:**
- Slow uploads on mobile networks (10-60 seconds)
- Burns user's mobile data (expensive in many regions)
- Increased S3 storage costs (storing huge originals)
- Slower processing (GPU needs to process huge images)
- Poor UX (user waits forever for upload)

**Do this instead:**
- Compress images on mobile before upload (use native compression APIs)
- Target 1-3MB for originals (more than sufficient for iris art)
- Use progressive upload with quality adjustment
- Show upload progress indicator
- Consider thumbnail generation on mobile for instant preview

```typescript
// ❌ Anti-pattern: Upload raw camera photo
const photo = await camera.takePhoto();
await uploadImage(photo.path);  // 15MB, takes 60s on 3G!

// ✅ Correct pattern: Compress before upload
const photo = await camera.takePhoto();

const compressed = await Image.compress(photo.path, {
  maxWidth: 2048,  // Sufficient for iris detail
  maxHeight: 2048,
  quality: 0.8,  // 80% JPEG quality
  format: 'JPEG'
});  // Now ~2MB

await uploadImageWithProgress(compressed, (progress) => {
  setUploadProgress(progress);  // Show user feedback
});  // Takes 5-10s on 3G
```

### Anti-Pattern 6: Using HTTP Polling Instead of WebSocket for Progress

**What people do:** Poll GET /api/jobs/{id}/status every 1-2 seconds to check task progress

**Why it's wrong:**
- Wasteful: Makes hundreds of unnecessary API requests
- Slow: Minimum 1-2 second delay to see updates (poor UX)
- Server load: Each poll hits database to check status
- Scalability: 1000 users = 1000 requests/sec to API
- Battery drain: Constant network requests on mobile

**Do this instead:**
- Use WebSocket connection for real-time updates
- Server pushes updates as they happen (no polling delay)
- Single persistent connection (not hundreds of requests)
- Mobile-friendly: Less battery drain
- Fallback to polling only if WebSocket fails

```typescript
// ❌ Anti-pattern: HTTP polling
useEffect(() => {
  const interval = setInterval(async () => {
    const status = await api.get(`/jobs/${jobId}/status`);  // Wasteful!
    setProgress(status.progress);
  }, 1000);  // 60 requests/minute per user
  return () => clearInterval(interval);
}, [jobId]);

// ✅ Correct pattern: WebSocket push
useEffect(() => {
  const ws = new WebSocket(`wss://api.irisvue.com/ws/jobs/${jobId}`);

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    setProgress(data.progress);  // Instant updates!
  };

  return () => ws.close();  // Single connection
}, [jobId]);
```

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **AWS S3 / Cloudflare R2** | boto3 SDK with pre-signed URLs | Use separate buckets for originals vs processed. Enable versioning for originals. Set lifecycle policies to archive old processed images to Glacier after 90 days. |
| **CloudFront CDN** | Origin: S3 bucket, Lambda@Edge for transforms | Cache-Control headers: 1 year for processed images, 1 day for thumbnails. Invalidate on user deletion. |
| **Stripe Payments** | Stripe Python SDK + webhook handlers | Use Payment Intents API for mobile (better for Apple/Google Pay). Webhook for subscription events at `/api/v1/webhooks/stripe`. Idempotency keys required. |
| **Apple Sign In** | OAuth2 with fastapi-sso or authlib | Requires Apple Developer account. Returns user email + unique ID. Handle email privacy relay. |
| **Google Sign In** | OAuth2 with Google Identity Services | Returns user email + profile. Validate ID token server-side. Refresh tokens for offline access. |
| **Sentry** | Sentry Python SDK + React Native SDK | Error tracking + performance monitoring. Set context: user_id, image_id, job_id. |
| **PostHog / Mixpanel** | Event tracking SDK | Track key events: image_captured, processing_started, style_selected, circle_created, payment_completed. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **Mobile ↔ API** | REST + WebSocket over HTTPS | JWT in Authorization header. WebSocket for job progress only. REST for everything else. API versioning: /api/v1/, /api/v2/ |
| **API ↔ Workers** | Redis queue (Celery) | Stateless workers. Job state in Redis + PostgreSQL. Workers pull tasks. No direct HTTP between API and workers. |
| **API ↔ PostgreSQL** | SQLAlchemy ORM with async driver | Connection pooling via PgBouncer. Read replicas for analytics. Use database migrations (Alembic) for schema changes. |
| **Workers ↔ S3** | Direct boto3 calls | Workers read/write S3 directly. No API proxy. Use S3 Transfer Acceleration for large files. |
| **Mobile ↔ S3** | Pre-signed URLs from API | API generates pre-signed POST for uploads (secure, no credentials in mobile). Pre-signed GET for downloads (time-limited). |

## Build Order & Dependencies

Based on architectural dependencies and user value delivery, here's the optimal build order:

### Phase 1: Core Infrastructure (Week 1-2)
**Why first:** Foundation for everything else

1. **Database schema** (PostgreSQL models: Users, Images, Jobs)
2. **S3 buckets** setup (originals + processed)
3. **FastAPI project structure** (app skeleton, config, basic routes)
4. **Authentication** (JWT + OAuth2, Apple/Google Sign In integration)
5. **Basic API endpoints** (health check, auth, user CRUD)

**Deliverable:** Working API with auth, deployable to staging

**Dependencies:** None (greenfield)

### Phase 2: Image Upload & Storage (Week 2-3)
**Why second:** Needed before any processing can happen

1. **Image upload endpoint** (multipart/form-data, validation)
2. **S3 integration** (upload to originals bucket, pre-signed URLs)
3. **Image metadata storage** (PostgreSQL records)
4. **Mobile app scaffold** (React Native project, navigation, auth screens)
5. **Camera integration** (react-native-vision-camera, capture photo)
6. **Upload flow** (compress, upload with progress, error handling)

**Deliverable:** Users can capture and upload iris photos

**Dependencies:** Phase 1 (auth + API foundation)

### Phase 3: Async Processing Pipeline (Week 3-4)
**Why third:** Enables all AI features (segmentation, enhancement, style transfer)

1. **Celery setup** (Redis broker, worker configuration, priority queues)
2. **Job tracking** (PostgreSQL jobs table, status updates)
3. **WebSocket endpoint** (progress streaming)
4. **First AI task: Iris segmentation** (U-Net model, task implementation)
5. **Mobile processing screen** (job submission, progress bar, result display)

**Deliverable:** End-to-end flow from photo capture → AI processing → result

**Dependencies:** Phase 2 (image upload working)

### Phase 4: Camera Guidance Overlay (Week 4-5)
**Why fourth:** UX improvement, not core functionality (can be added anytime)

1. **Lightweight iris detection model** (TFLite/CoreML for on-device)
2. **Frame processor** (real-time inference on camera frames)
3. **Guidance overlay UI** (SVG overlay, alignment indicators)
4. **Feedback logic** (is iris centered? aligned? good lighting?)

**Deliverable:** Real-time camera guidance for better photo quality

**Dependencies:** Phase 2 (camera working), Phase 3 (processing working)

### Phase 5: Additional AI Features (Week 5-7)
**Why fifth:** Builds on processing pipeline established in Phase 3

1. **Enhancement task** (reflection removal, quality improvement)
2. **Style transfer task** (multiple artistic styles)
3. **Image generation task** (AI-generated iris art variants)
4. **Style gallery** (browse styles, preview thumbnails)
5. **HD export** (high-resolution output for premium users)

**Deliverable:** Full suite of AI art features

**Dependencies:** Phase 3 (processing pipeline working)

### Phase 6: Social Features (Week 7-9)
**Why sixth:** Differentiator feature, but depends on core processing being solid

1. **Circles schema** (PostgreSQL: circles, circle_members, invitations)
2. **Circle CRUD endpoints** (create, invite, accept, leave)
3. **Invitation system** (magic links, email notifications)
4. **Gallery permissions** (view irises within circle)
5. **Fusion task** (combine two irises into art)
6. **Mobile social UI** (circles screen, gallery, fusion flow)

**Deliverable:** Users can create circles, invite friends, create fusion art

**Dependencies:** Phase 5 (AI features complete, need multiple processed images to fuse)

### Phase 7: Payments & Freemium (Week 9-10)
**Why seventh:** Monetization comes after core value is proven

1. **Stripe integration** (Stripe SDK, payment intents, webhooks)
2. **Subscription management** (free vs premium tiers, feature gates)
3. **Payment endpoints** (initiate payment, check status, manage subscription)
4. **Mobile payment UI** (Stripe payment sheet, premium style selection)
5. **Premium features** (unlock HD export, premium styles, unlimited processing)

**Deliverable:** Working freemium model with payment processing

**Dependencies:** Phase 5 (need premium features to sell)

### Phase 8: Polish & Production Readiness (Week 10-12)
**Why last:** Optimization and reliability improvements

1. **CDN setup** (CloudFront with S3 origins, edge caching)
2. **Performance optimization** (API caching, database indexes, query optimization)
3. **Monitoring** (Sentry error tracking, PostHog analytics, performance monitoring)
4. **Load testing** (API stress tests, worker scaling tests)
5. **Mobile polish** (animations, loading states, error handling, offline mode)
6. **Documentation** (API docs, deployment guide, runbooks)

**Deliverable:** Production-ready application ready for public launch

**Dependencies:** All phases (this is polish on top of complete features)

### Critical Path Summary

```
Phase 1 (Auth & API)
    ↓
Phase 2 (Upload)
    ↓
Phase 3 (AI Processing) ←─── CRITICAL PATH
    ↓
Phase 5 (More AI Features)
    ↓
Phase 6 (Social)
    ↓
Phase 7 (Payments)
    ↓
Phase 8 (Polish)

Phase 4 (Camera Guidance) ←─── Can be done in parallel with Phase 5-6
```

**Parallel work opportunities:**
- Phase 4 (Camera Guidance) can be built in parallel with Phase 5 (AI Features)
- Frontend and backend teams can work simultaneously after Phase 3
- Multiple AI tasks (Phase 5) can be built in parallel by different developers

**Key principle:** Build vertically (full stack for one feature) before horizontally (all features at once). This ensures you always have a working demo and can gather user feedback early.

## API Design Approach

### RESTful Resources

```
/api/v1/auth/
    POST   /register                  # Email/password signup
    POST   /login                     # Email/password login
    POST   /refresh                   # Refresh access token
    POST   /social/apple              # Apple Sign In
    POST   /social/google             # Google Sign In
    POST   /logout                    # Invalidate token

/api/v1/users/
    GET    /me                        # Current user profile
    PATCH  /me                        # Update profile
    DELETE /me                        # Delete account

/api/v1/images/
    GET    /                          # List user's images (paginated)
    POST   /                          # Create image record + get upload URL
    GET    /{image_id}                # Get image metadata
    DELETE /{image_id}                # Delete image
    GET    /{image_id}/download       # Get pre-signed download URL

/api/v1/processing/
    POST   /segment                   # Submit segmentation job
    POST   /enhance                   # Submit enhancement job
    POST   /style-transfer            # Submit style transfer job
    POST   /fuse                      # Submit fusion job (2 images)
    GET    /styles                    # List available styles (free + premium)

/api/v1/jobs/
    GET    /{job_id}                  # Get job status
    DELETE /{job_id}                  # Cancel job (if not completed)

/api/v1/circles/
    GET    /                          # List user's circles
    POST   /                          # Create new circle
    GET    /{circle_id}               # Get circle details + members
    PATCH  /{circle_id}               # Update circle (name, settings)
    DELETE /{circle_id}               # Delete circle (owner only)
    POST   /{circle_id}/invite        # Send invitation
    GET    /{circle_id}/gallery       # Get all images in circle
    DELETE /{circle_id}/members/{user_id}  # Remove member

/api/v1/invitations/
    GET    /                          # List user's invitations
    POST   /{invite_token}/accept     # Accept invitation
    DELETE /{invite_token}            # Decline invitation

/api/v1/payments/
    POST   /create-intent             # Create Stripe payment intent
    GET    /subscription              # Get user's subscription status
    POST   /webhook                   # Stripe webhook handler

/ws/jobs/{job_id}                     # WebSocket for job progress
```

### Design Principles

1. **Resource-oriented URLs:** `/api/v1/images/{id}` not `/api/v1/getImage?id=123`
2. **HTTP methods for actions:** GET (read), POST (create), PATCH (partial update), DELETE (delete)
3. **API versioning:** `/api/v1/` prefix for future-proofing (can add /api/v2/ later)
4. **Pagination:** Query params `?page=1&limit=20` for list endpoints
5. **Filtering:** Query params `?status=completed&created_after=2026-01-01`
6. **Consistent response format:**
   ```json
   {
     "data": { ... },          // Successful response data
     "meta": { "page": 1 },    // Pagination/metadata (optional)
     "error": null             // Null on success
   }

   {
     "data": null,
     "error": {
       "code": "IMAGE_NOT_FOUND",
       "message": "Image with id xyz not found",
       "details": { "image_id": "xyz" }
     }
   }
   ```

7. **JWT authentication:** `Authorization: Bearer <token>` header on protected routes
8. **Pre-signed URLs for large files:** API returns temporary URL, client uploads/downloads directly to S3
9. **Idempotency:** POST requests with `Idempotency-Key` header to prevent duplicate processing
10. **Rate limiting:** 100 req/min per user for API, 10 req/min for processing endpoints

## Sources

### Architecture & System Design
- [Building async processing pipelines with FastAPI and Celery](https://devcenter.upsun.com/posts/building-async-processing-pipelines-with-fastapi-and-celery-on-upsun/)
- [Managing Background Tasks in FastAPI](https://leapcell.io/blog/managing-background-tasks-and-long-running-operations-in-fastapi)
- [How I Handled 100K Daily Jobs in FastAPI Using Task Queues](https://medium.com/@connect.hashblock/how-i-handled-100k-daily-jobs-in-fastapi-using-task-queues-and-async-retries-62bbcdd8240d)
- [Async Architecture with FastAPI, Celery, and RabbitMQ](https://medium.com/cuddle-ai/async-architecture-with-fastapi-celery-and-rabbitmq-c7d029030377)

### Mobile AI & Camera Integration
- [AI-Based Image Signal Processors](https://petapixel.com/2026/01/18/a-look-at-the-worlds-first-full-ai-based-image-signal-processor/)
- [Smartphone Cameras 2026: AI and Advanced Features](https://www.ibtimes.com/smartphone-cameras-2026-how-ai-advanced-features-outperform-megapixels-3796226)
- [Deploy ML models for real-time frame processing with React Native Vision Camera](https://medium.com/technoid-community/deploy-any-machine-learning-model-for-real-time-frame-processing-with-react-native-vision-camera-571fbf2948d1)
- [Flutter vs React Native in 2026](https://medium.com/@mahtabhussain7/flutter-vs-react-native-in-2026-which-is-the-best-cross-platform-framework-354db88a6b7c)

### Image Storage & CDN
- [Building a Scalable Image Service with S3, CloudFront, and Lambda](https://yesaritonga.medium.com/building-a-scalable-image-service-with-amazon-s3-cloudfront-dynamodb-and-lambda-cbe3a648ef66)
- [Dynamic Image Transformation for CloudFront](https://aws.amazon.com/solutions/implementations/dynamic-image-transformation-for-amazon-cloudfront/)
- [Optimize Images with AWS S3 and CloudFront](https://culturedevops.com/en/blog/aws-s3-cloudfront-image-optimization)
- [Optimizing Image Storage in PostgreSQL](https://medium.com/@ajaymaurya73130/optimizing-image-storage-in-postgresql-tips-for-performance-scalability-fd4d575a6624)
- [Databases vs Blob Storage: What to Use and When](https://medium.com/@harshithgowdakt/databases-vs-blob-storage-what-to-use-and-when-d5b1ec0d11cd)

### Queue Management & Real-Time Updates
- [Bull vs Celery vs Sidekiq: Job Queue Comparison 2026](https://www.index.dev/skill-vs-skill/backend-sidekiq-vs-celery-vs-bull)
- [Modern Queueing Architectures: Celery, RabbitMQ, Redis, or Temporal](https://medium.com/@pranavprakash4777/modern-queueing-architectures-celery-rabbitmq-redis-or-temporal-f93ea7c526ec)
- [Prioritizing Tasks With Celery and Redis](https://olzhasar.com/posts/prioritizing-tasks-with-celery-and-redis/)
- [WebSocket vs Long Polling: Choosing Real-time in 2025](https://potapov.me/en/make/websocket-sse-longpolling-realtime)
- [Long Polling vs WebSockets](https://ably.com/blog/websockets-vs-long-polling)

### Authentication & Payments
- [FastAPI Google OAuth 2.0 Authentication](https://parlak-deniss.medium.com/fastapi-authentication-with-google-oauth-2-0-9bb93b784eee)
- [fastapi-sso: SSO plugin for FastAPI](https://github.com/tomasvotava/fastapi-sso)
- [Mobile App Payment Gateway Integration with Stripe](https://stripe.com/resources/more/how-do-you-add-payment-gateways-in-an-app)
- [Can You Use Stripe for In-App Purchases in 2026?](https://adapty.io/blog/can-you-use-stripe-for-in-app-purchases/)
- [Building for the next wave of app monetization](https://stripe.com/blog/building-for-the-next-wave-of-app-monetization)

### System Architecture Patterns
- [Monorepos vs Microservices in 2026](https://medium.com/jonathans-musings/all-hail-the-monorepo-long-live-microservices-4f96209c66e4)
- [Microservices vs Monoliths in 2026](https://www.javacodegeeks.com/2025/12/microservices-vs-monoliths-in-2026-when-each-architecture-wins.html)
- [Top Software Architecture Trends for 2026](https://medium.com/@xaylonlabs/top-software-architecture-trends-for-2026-ai-edge-computing-and-the-rise-of-the-autonomous-81a2554fe9fd)
- [Mobile App Architecture Trends 2026](https://backlinksindiit.wixstudio.com/app-development-expe/post/6-mobile-app-architecture-trends-coming-in-2026)

### Iris Segmentation & Computer Vision
- [Deep Learning for Iris Recognition: A Survey](https://dl.acm.org/doi/10.1145/3651306)
- [Iris-SAM: Iris Segmentation Using a Foundation Model](https://arxiv.org/html/2402.06497v2)
- [Robust Iris Segmentation Algorithm Using Interleaved Residual U-Net](https://pmc.ncbi.nlm.nih.gov/articles/PMC7922029/)
- [Top 30+ Computer Vision Models For 2026](https://www.analyticsvidhya.com/blog/2025/03/computer-vision-models/)

### MVP Development & Build Order
- [8-Step Mobile App Development Process Guide 2026](https://americanchase.com/mobile-app-development-process/)
- [How to Build an MVP: Benefits, Costs, Stages](https://www.appschopper.com/blog/mvp-development-guide/)
- [MVP Tech Stack Guide 2026](https://medium.com/@cabotsolutions/mvp-tech-stack-guide-2026-build-fast-stay-compliant-94e1bc34fee7)

---
*Architecture research for: IrisVue — AI-powered mobile iris art photography app*
*Researched: 2026-02-01*
*Confidence: HIGH (verified with official docs, recent 2025-2026 sources, cross-referenced patterns)*
