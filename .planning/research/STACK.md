# Stack Research

**Domain:** Cross-platform mobile app with AI-powered iris photography and art generation
**Researched:** 2026-02-01
**Confidence:** HIGH

## Recommended Stack

### Mobile Frontend (Cross-Platform)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **React Native** | 0.76.x | Cross-platform mobile framework | Better ecosystem for camera/real-time processing, mature native module support, easier native bridge integration for custom camera features. Flutter struggles with advanced camera APIs and hardware access. |
| react-native-vision-camera | 4.7.x | High-performance camera library | Industry-standard camera library with Frame Processors for real-time AI guidance, GPU acceleration, 30-240 FPS support, QR/barcode scanning. 350K+ weekly downloads, actively maintained. Replaces deprecated react-native-camera. |
| React Native Reanimated | 3.x | Smooth UI animations | Required for smooth zoom, focus indicators, and camera guidance overlays. Runs on UI thread for 60+ FPS performance. |
| Expo (selective modules) | SDK 52.x | Development tooling + Auth | Use Expo modules for Apple Sign In, Google Sign In, secure storage. Don't use Expo Go - use bare React Native workflow for camera control. |
| @react-native-firebase/auth | 21.x | Authentication | Official Firebase Auth for Apple/Google sign-in with PKCE, token management. Integrates with backend via JWT validation. |
| React Query (TanStack Query) | 5.x | Server state management | Handles API calls, caching, optimistic updates for gallery sync, background data fetching. |
| Zustand | 4.x | Client state management | Lightweight state management for camera settings, capture flow, local UI state. |

**Alternative Framework Analysis:**

Flutter was evaluated but rejected for the following reasons:
- Camera APIs require more native bridge code compared to React Native's mature ecosystem
- Real-time frame processing is more complex due to Flutter's rendering architecture
- React Native Vision Camera's Frame Processors provide superior real-time guidance capabilities
- JavaScript/TypeScript ecosystem alignment with potential web version

**Sources:**
- [Flutter vs React Native 2026 comparison](https://limeup.io/blog/flutter-vs-react-native/)
- [React Native Vision Camera documentation](https://react-native-vision-camera.com/)
- [VisionCamera GitHub - 9K+ stars](https://github.com/mrousavy/react-native-vision-camera)

### Backend (API Layer)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Python** | 3.11.x | Backend language | Required (project constraint). Excellent AI/ML library ecosystem, async support, type hints for maintainability. |
| **FastAPI** | 0.115.x | API framework | Required (project constraint). Async-first, automatic OpenAPI docs, Pydantic validation, excellent DX. Current standard for Python APIs in 2026. |
| Pydantic | 2.x | Data validation | Core validation library for FastAPI. v2 has Rust-powered core for high performance. Handles request/response validation, settings management. |
| pydantic-settings | 2.x | Configuration management | Official Pydantic extension for .env file loading, environment variable validation. |
| Uvicorn | 0.32.x | ASGI server | Production ASGI server for FastAPI. Use with Gunicorn for multiple workers. |
| Gunicorn | 23.x | Process manager | Runs multiple Uvicorn workers for production (2-4 workers recommended). |
| python-jose[cryptography] | 3.3.x | JWT handling | Industry-standard JWT encoding/decoding for Firebase token validation and internal auth. |
| python-multipart | 0.0.x | File upload handling | Required for FastAPI file uploads (iris photo uploads). |

**Async Configuration:**
- Use `async def` for all I/O-bound endpoints (database, external APIs)
- Avoid sync dependencies in threadpool for small operations
- FastAPI's async-first design maximizes throughput for image processing queues

**Sources:**
- [FastAPI official documentation](https://fastapi.tiangolo.com/)
- [FastAPI best practices 2026](https://github.com/zhanymkanov/fastapi-best-practices)
- [FastAPI at Scale 2026](https://medium.com/@kaushalsinh73/fastapi-at-scale-in-2026-pydantic-v2-uvloop-http-3-which-knob-moves-latency-vs-throughput-cd0a601179de)

### Database Layer

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **PostgreSQL** | 16.x | Primary database | Required (project constraint). Best open-source relational DB, JSONB for metadata, excellent performance, strong ACID guarantees. |
| asyncpg | 0.30.x | PostgreSQL async driver | Designed from ground up for asyncio, superior performance vs psycopg2. Required for SQLAlchemy async. |
| SQLAlchemy | 2.0.x | ORM | Industry-standard Python ORM with full async support via asyncpg. Use modern `select()` style, not legacy `.query()`. |
| Alembic | 1.14.x | Database migrations | Official SQLAlchemy migration tool. Generate migrations from model changes, version control schema. |

**Critical Configuration:**
```python
# Database URL format
DATABASE_URL = "postgresql+asyncpg://user:pass@host:5432/iris_art"

# Session configuration
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False  # Critical for async
)
```

**Sources:**
- [SQLAlchemy 2.0 async best practices](https://leapcell.io/blog/building-high-performance-async-apis-with-fastapi-sqlalchemy-2-0-and-asyncpg)
- [Async SQLAlchemy guide](https://dev.to/amverum/asynchronous-sqlalchemy-2-a-simple-step-by-step-guide-to-configuration-models-relationships-and-3ob3)
- [FastAPI + SQLAlchemy 2.0 setup](https://berkkaraal.com/blog/2024/09/19/setup-fastapi-project-with-async-sqlalchemy-2-alembic-postgresql-and-docker/)

### Background Task Processing

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Celery** | 5.4.x | Distributed task queue | Industry standard for ML workloads. Handles long-running AI processing (segmentation, style transfer, upscaling). Built-in retry, monitoring, scheduling. |
| Celery Beat | (bundled) | Task scheduler | Periodic tasks (cleanup, cache warming). Included with Celery. |
| Redis | 7.x | Message broker + cache | Celery broker and result backend. Also serves as cache for API responses, session storage. Fast, reliable, simple. |
| Flower | 2.x | Celery monitoring | Web UI for monitoring Celery tasks, workers, throughput. Essential for production debugging. |

**Alternative Considered:**
- **RQ (Redis Queue)**: Simpler but lacks advanced features. Celery's scheduling, task routing, and monitoring capabilities are critical for complex AI pipelines.

**Task Architecture:**
```python
# Iris processing pipeline stages as separate tasks
- capture_preprocessing_task (quick: image validation, EXIF)
- iris_segmentation_task (medium: 2-5s, U-Net inference)
- reflection_removal_task (medium: 3-8s, transformer model)
- upscaling_task (long: 5-15s, Real-ESRGAN 4x)
- style_transfer_task (long: 10-30s, NST or diffusion)
- fusion_task (long: 15-40s, blending two processed irises)
```

**Sources:**
- [Celery vs RQ comparison](https://python.plainenglish.io/python-celery-vs-python-rq-for-distributed-tasks-processing-20041c346e6)
- [Why Frappe moved from Celery to RQ](https://frappe.io/blog/technology/why-we-moved-from-celery-to-rq) (and insights on when Celery is still better)
- [Async Task Patterns comparison](https://medium.com/@connect.hashblock/async-task-patterns-in-django-choosing-between-celery-dramatiq-and-rq-bb14339291fc)

### AI/ML Pipeline

| Library | Version | Purpose | Why Recommended |
|---------|---------|---------|-----------------|
| **PyTorch** | 2.x | Deep learning framework | Industry standard for computer vision, better for research-to-production, superior segmentation models ecosystem. TensorFlow has deployment edge but PyTorch's TorchServe closed the gap. |
| torchvision | 0.19.x | Vision models/transforms | Pre-trained models, image transformations, data augmentation utilities. |
| ONNX Runtime | 1.20.x | Model inference optimization | 2-3x faster inference than native PyTorch. Converts PyTorch models to ONNX for production. Supports CPU/GPU/NPU hardware acceleration. |
| opencv-python-headless | 4.10.x | Image processing | Headless version (no GUI) for server. Pre/post-processing, color space conversion, geometric transforms. |
| Pillow | 11.x | Image I/O | Reading/writing image formats, basic manipulations, EXIF handling. |
| numpy | 2.x | Numerical operations | Array operations, matrix math for image processing pipelines. |
| scikit-image | 0.24.x | Image algorithms | Traditional CV algorithms (morphology, filters) for preprocessing. |

**AI Model Recommendations by Pipeline Stage:**

#### 1. Iris Segmentation
**Model:** U-Net or DeepLabV3+ with MobileNetV2 backbone
- **Why:** U-Net variants achieve 98.9%+ IoU on iris datasets. DeepLabV3+ with MobileNetV2 achieves 95.54% mIoU with faster inference.
- **Implementation:** Fine-tune pre-trained model on iris dataset, convert to ONNX for 2-3x speedup
- **Research:** [Interleaved Residual U-Net](https://pmc.ncbi.nlm.nih.gov/articles/PMC7922029/), [DeepLabV3+ iris segmentation](https://arxiv.org/abs/2408.03448)
- **Confidence:** HIGH - proven architecture for iris segmentation

#### 2. Reflection Removal
**Model:** Laplacian Pyramid Component-Aware Transformer (LapCAT) or RABRRN
- **Why:** Recent transformers solve high-res reflection removal. LapCAT handles full-resolution images without downsampling loss.
- **Alternative:** Traditional CV approach using polarization filters detection + inpainting (faster, lower quality)
- **Implementation:** Start with traditional approach, upgrade to transformer if quality insufficient
- **Research:** [LapCAT transformer](https://www.nature.com/articles/s41598-025-94464-6), [RABRRN attention network](https://www.mdpi.com/2076-3417/13/3/1618)
- **Confidence:** MEDIUM - newer research, may need custom training

#### 3. Image Upscaling
**Model:** Real-ESRGAN (4x upscaling)
- **Why:** Industry standard for real-world image restoration. 4x/8x upscaling with detail preservation. Free, open-source, proven.
- **Implementation:** Use pre-trained models, runs well on CPU or GPU
- **Hosting:** Run via ONNX Runtime or use Hugging Face Inference API
- **Research:** [Real-ESRGAN GitHub](https://github.com/xinntao/Real-ESRGAN), [2026 AI upscalers comparison](https://letsenhance.io/blog/all/best-ai-image-upscalers/)
- **Confidence:** HIGH - proven, production-ready

#### 4. Artistic Style Transfer
**Model:** Fast Neural Style Transfer (preset styles) + Stable Diffusion 3.5 (custom generation)
- **Why:** Fast NST for instant preset filters (<1s). Stable Diffusion 3.5 for unique AI-generated compositions (10-30s).
- **Preset Styles:** Train Fast NST models on artistic styles (Van Gogh, watercolor, etc.). Single forward pass inference.
- **AI Generation:** Use Stable Diffusion 3.5 (open-source) or FLUX.1.1 (faster, 4.5s, but proprietary)
- **Research:** [NST review 2025](https://www.nature.com/articles/s41598-025-95819-9), [FLUX vs Stable Diffusion 2026](https://www.gradually.ai/en/ai-image-models/)
- **Confidence:** HIGH (NST), MEDIUM (Stable Diffusion integration complexity)

#### 5. Iris Fusion
**Model:** Custom blending algorithm + Stable Diffusion ControlNet (optional)
- **Why:** Start with algorithmic approach (alpha blending, gradient domain fusion). Add AI enhancement via ControlNet for artistic fusion.
- **Implementation:**
  - Phase 1: Traditional Poisson blending (fast, predictable)
  - Phase 2: ControlNet-guided fusion (artistic, slower)
- **Confidence:** MEDIUM - hybrid approach, needs experimentation

**Model Hosting Options:**
1. **Self-hosted:** ONNX Runtime inference on own servers (full control, requires GPU)
2. **Hugging Face Inference API:** Serverless model hosting ($0.03-$80/hr Inference Endpoints)
3. **Hybrid:** Fast models (segmentation, upscaling) self-hosted; slow models (Stable Diffusion) via API

**Sources:**
- [PyTorch vs TensorFlow 2026](https://www.hyperstack.cloud/blog/case-study/pytorch-vs-tensorflow)
- [ONNX Runtime PyTorch optimization](https://onnxruntime.ai/docs/tutorials/accelerate-pytorch/pytorch.html)
- [Deep Learning iris segmentation survey](https://dl.acm.org/doi/10.1145/3651306)
- [Neural Style Transfer recent research](https://www.nature.com/articles/s41598-025-95819-9)
- [Stable Diffusion 3.5 comparison](https://www.gradually.ai/en/ai-image-models/)
- [Reflection removal survey](https://www.nature.com/articles/s41598-025-94464-6)
- [Real-ESRGAN documentation](https://realesrgan.com/)

### Real-Time Camera Guidance (Mobile)

| Technology | Purpose | Why Recommended |
|------------|---------|-----------------|
| MediaPipe (via React Native bridge) | Face/iris detection | Google's framework for real-time ML. Tracks 468 facial landmarks + iris at 30+ FPS. Run on-device for instant feedback. |
| TensorFlow Lite (optional) | Custom on-device models | If MediaPipe insufficient, deploy custom models via TFLite. Lighter than full TensorFlow. |
| React Native Vision Camera Frame Processors | Real-time processing | Run JS/native code on camera frames at capture time. Perfect for overlay guides, quality checks. |

**Guidance Pipeline:**
1. **MediaPipe Face Mesh** → detect eye regions (on-device, <30ms)
2. **Distance estimation** → use face mesh depth to guide distance (algorithm-based, <5ms)
3. **Lighting check** → analyze histogram for over/underexposure (OpenCV-based, <10ms)
4. **Focus indicator** → overlay guide on screen (React Native overlay, <16ms for 60fps)

**Sources:**
- [MediaPipe real-time body tracking](https://medium.com/@creativeainspiration/real-time-body-tracking-in-your-browser-what-mediapipe-actually-does-and-how-to-use-it-b31aa96a5071)
- [MediaPipe with OpenCV demos](https://github.com/Naveenp7/MediaPipe-Real-Time-Computer-Vision-Demos)

### Cloud Storage & CDN

| Technology | Purpose | Why Recommended |
|------------|---------|-----------------|
| **AWS S3** | Raw image storage | Cost-effective ($0.023/GB/month), reliable, scalable. Store original uploads, intermediate processing stages. |
| **Cloudinary** | Processed image CDN | API-first media management. On-the-fly transformations, CDN delivery, mobile SDKs. Better than self-managing CloudFront + Lambda. |
| Cloudinary Free Tier | Development/MVP | 25 GB storage, 25 GB bandwidth/month. Sufficient for early testing. |

**Storage Architecture:**
- **S3:** Raw uploads, processing artifacts, backups (private buckets)
- **Cloudinary:** Final artworks, thumbnails, gallery images (CDN-delivered, public)
- **Hybrid approach:** Upload to S3 → process → deliver via Cloudinary

**Why not S3 alone?**
Cloudinary provides built-in image optimization, responsive delivery, format conversion (WebP, AVIF), and transformation APIs that would require custom Lambda + CloudFront setup.

**Sources:**
- [Cloudinary vs S3 comparison](https://cloudinary.com/guides/ecosystems/cloudinary-vs-s3)
- [AWS S3 vs Cloudinary vs imgix cost breakdown](https://knackforge.com/blog/aws-s3)

### Authentication & Payment

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Firebase Auth | 10.x | OAuth provider | Handles Apple Sign In + Google Sign In with PKCE. Mobile SDKs handle token refresh, secure storage. Backend validates JWT. |
| RevenueCat | 4.x | In-app purchase management | Cross-platform subscription SDK. Handles iOS/Android IAP complexities, instant entitlement sync, analytics. |
| Stripe (via RevenueCat Web Billing) | Latest | Web payments (US market) | Epic v. Apple ruling (2025) allows external checkout. RevenueCat integrates Stripe for web flows as IAP alternative. |

**Authentication Flow:**
1. User signs in with Apple/Google via Firebase Auth
2. Mobile app gets Firebase ID token
3. Backend validates token with Firebase Admin SDK
4. Backend issues internal JWT (short-lived, custom claims)
5. Mobile stores JWT in secure storage (Keychain/Keystore)

**Payment Architecture:**
- **Primary:** Native IAP via RevenueCat (iOS App Store, Google Play)
- **Secondary:** Web checkout via Stripe (US only, Epic ruling compliance)
- **RevenueCat cost:** 1% of Monthly Tracked Revenue over $2,500 + Stripe fees (2.9% + $0.30)

**Critical Apple Requirement:**
If offering Google Sign-In, MUST also offer Apple Sign In (App Store requirement 2.1). Apple Sign In provides email privacy relay (privaterelay.appleid.com).

**Sources:**
- [Apple Sign In requirement](https://workos.com/blog/apple-app-store-authentication-sign-in-with-apple-2025)
- [Firebase Auth documentation](https://firebase.google.com/docs/auth/ios/google-signin)
- [RevenueCat Stripe integration](https://www.revenuecat.com/blog/engineering/can-you-use-stripe-for-in-app-purchases/)
- [RevenueCat pricing 2026](https://www.metacto.com/blogs/the-real-cost-of-revenuecat-what-app-publishers-need-to-know)

### Deployment & Infrastructure

| Technology | Purpose | Why Recommended |
|------------|---------|-----------------|
| **Docker** | Containerization | Package FastAPI app, Celery workers, Redis, PostgreSQL. Consistent dev/prod environments. |
| Docker Compose | Local orchestration | Dev environment with hot reload, health checks, networking. Production uses cloud orchestration. |
| **Google Cloud Run** | API hosting | Serverless FastAPI hosting. Auto-scaling, built-in HTTPS, pay-per-use. Official FastAPI deployment guide (Jan 2026). |
| Google Cloud SQL | Managed PostgreSQL | Fully managed PostgreSQL 16. Automatic backups, HA, connection pooling. Better than self-managed RDS. |
| Google Compute Engine (GPU) | AI inference workers | GPU instances for heavy model inference (Stable Diffusion). Preemptible instances for cost savings. |
| GitHub Actions | CI/CD | Build Docker images, run tests, deploy to Cloud Run. Free for public repos, $0.008/minute for private. |
| Sentry | Error tracking | Real-time error reporting, performance monitoring, release tracking. Free tier: 5K errors/month. |

**Deployment Architecture:**
```
┌─────────────────┐
│  Mobile App     │
│  (React Native) │
└────────┬────────┘
         │
    ┌────▼─────────────────────────────┐
    │  Cloud Load Balancer (HTTPS)     │
    └────┬─────────────────────────────┘
         │
    ┌────▼─────────────────┐
    │  FastAPI (Cloud Run) │──┐
    │  Auto-scaling 0-100  │  │
    └────┬─────────────────┘  │
         │                     │
    ┌────▼─────────┐     ┌────▼────────┐
    │  Cloud SQL   │     │  Redis      │
    │  PostgreSQL  │     │  (Memstore) │
    └──────────────┘     └─────┬───────┘
                               │
                         ┌─────▼────────┐
                         │ Celery       │
                         │ Workers      │
                         │ (GCE + GPU)  │
                         └──────────────┘
```

**Why Google Cloud over AWS?**
- Cloud Run is simpler than ECS/EKS for FastAPI (official guide updated Jan 2026)
- Better ML/AI integration (Vertex AI, TPUs if needed later)
- Simpler pricing for serverless workloads
- **Alternative:** AWS is valid if team prefers it (EC2 + ECS + RDS)

**CI/CD Pipeline:**
1. Push to `main` → GitHub Actions trigger
2. Run tests (pytest + coverage)
3. Build Docker image
4. Push to Google Artifact Registry
5. Deploy to Cloud Run (blue-green deployment)
6. Run smoke tests
7. Slack notification

**Sources:**
- [FastAPI Cloud Run quickstart (Jan 2026)](https://docs.cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-fastapi-service)
- [FastAPI Docker deployment guide](https://fastapi.tiangolo.com/deployment/docker/)
- [Docker Compose FastAPI PostgreSQL Redis guide](https://www.khueapps.com/blog/article/setup-docker-compose-for-fastapi-postgres-redis-and-nginx-caddy)
- [GitHub Actions FastAPI CI/CD tutorial](https://pyimagesearch.com/2024/11/11/fastapi-with-github-actions-and-ghcr-continuous-delivery-made-simple/)

### Development Tools

| Tool | Purpose | Configuration |
|------|---------|---------------|
| Poetry | Python dependency management | Lock file for reproducible builds, better than pip + requirements.txt |
| pytest | Testing framework | Async test support, fixtures, parametrization |
| pytest-asyncio | Async test support | Test async FastAPI endpoints |
| pytest-cov | Code coverage | Aim for 80%+ coverage |
| Black | Code formatting | PEP 8 compliant, opinionated formatter |
| Ruff | Linting | Rust-powered linter, replaces Flake8 + isort, 10-100x faster |
| mypy | Type checking | Gradual typing, catch errors before runtime |
| pre-commit | Git hooks | Auto-format, lint, type-check before commit |
| httpx | HTTP client | Async HTTP client for testing, better than requests for async |

**Python Development Setup:**
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run tests with coverage
pytest --cov=app --cov-report=html

# Format code
black app/
ruff check app/ --fix

# Type check
mypy app/
```

**React Native Development Tools:**
| Tool | Purpose |
|------|---------|
| TypeScript | Type safety, IDE autocomplete |
| ESLint | Linting for JavaScript/TypeScript |
| Prettier | Code formatting |
| React Native Debugger | Debugging React Native apps |
| Reactotron | State inspection, API monitoring |
| Metro Bundler | React Native bundler (built-in) |

## Installation

### Backend (Python)

```bash
# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Clone repo and install dependencies
cd backend/
poetry install

# Install pre-commit hooks
poetry run pre-commit install

# Copy environment template
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
poetry run alembic upgrade head

# Start development server
poetry run uvicorn app.main:app --reload

# Start Celery worker (separate terminal)
poetry run celery -A app.celery.worker worker --loglevel=info

# Start Celery Beat scheduler (separate terminal)
poetry run celery -A app.celery.worker beat --loglevel=info

# Start Flower monitoring (separate terminal)
poetry run celery -A app.celery.worker flower
```

### Frontend (React Native)

```bash
# Install Node dependencies
cd mobile/
npm install

# iOS setup
cd ios/
pod install
cd ..

# Start Metro bundler
npm start

# Run on iOS simulator (separate terminal)
npm run ios

# Run on Android emulator (separate terminal)
npm run android

# Type check
npm run type-check

# Lint
npm run lint

# Format
npm run format
```

### Local Development (Docker Compose)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down

# Rebuild after dependency changes
docker-compose up --build
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| React Native | Flutter | If team has Dart expertise and doesn't need advanced camera features. Flutter has better out-of-box UI consistency but weaker camera ecosystem. |
| PyTorch | TensorFlow | If prioritizing production deployment tools (TF Serving, TF Lite). PyTorch has better research ecosystem and is catching up on deployment. |
| Celery | RQ (Redis Queue) | If task requirements are simple (no scheduling, routing, complex workflows). RQ is simpler but less feature-rich. |
| PostgreSQL | MongoDB | If data is truly document-oriented with no relationships. Iris metadata, circles, fusions are highly relational - PostgreSQL is better fit. |
| Google Cloud | AWS | If team has AWS expertise or enterprise requirements. AWS has broader service catalog but GCP has simpler serverless and better ML tooling. |
| Cloudinary | CloudFront + Lambda@Edge | If minimizing vendor lock-in or need custom transformation logic. Requires more DevOps effort. |
| SQLAlchemy | SQLModel | If want Pydantic integration without learning SQLAlchemy. SQLModel is thinner abstraction but less mature. |
| Uvicorn + Gunicorn | Hypercorn | If need HTTP/2 or WebSocket support beyond FastAPI defaults. Uvicorn is more mature and battle-tested. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| react-native-camera | Deprecated, no longer maintained | react-native-vision-camera (official replacement) |
| Expo Go workflow | Can't use native modules for advanced camera control | Bare React Native workflow with selective Expo modules |
| TensorFlow 1.x | Deprecated, no support | PyTorch 2.x or TensorFlow 2.x |
| Flask | Lacks async support, slower than FastAPI | FastAPI (modern, async, auto-docs) |
| Django | Too heavy for API-only backend, slower than FastAPI | FastAPI (lighter, faster, API-focused) |
| MySQL | Weaker JSONB support, less robust than PostgreSQL | PostgreSQL (better for metadata, complex queries) |
| Heroku | Expensive at scale, limited GPU options | Google Cloud Run + Compute Engine (cheaper, more flexible) |
| JWT without expiry | Security risk | Short-lived JWTs (15min) + refresh tokens |
| Synchronous SQLAlchemy with FastAPI | Blocks event loop, poor performance | Async SQLAlchemy 2.0 + asyncpg |
| pip + requirements.txt | No lock file, dependency conflicts | Poetry (lock file, better resolution) |
| Nose | Unmaintained test framework | pytest (modern, async support, rich ecosystem) |

## Stack Patterns by Variant

### If prioritizing speed-to-market (MVP)
- Use Expo managed workflow initially (sacrifice some camera features for faster auth/storage setup)
- Use Hugging Face Inference API for all AI models (avoid GPU server management)
- Use Cloudinary for all image storage (skip S3hybrid setup)
- Use Firebase Firestore instead of PostgreSQL (faster setup, less schema work)
- **Trade-off:** Higher operational costs, less control, may need migration later

### If prioritizing performance
- Use bare React Native from start with full Vision Camera integration
- Self-host all AI models with ONNX optimization on GPU instances
- Use PostgreSQL with hand-tuned indexes and connection pooling
- Use Redis Cluster for distributed caching
- **Trade-off:** More DevOps complexity, longer initial setup

### If prioritizing cost optimization
- Use Google Cloud Run auto-scaling (scale to zero when idle)
- Use Google Compute Engine Spot/Preemptible instances for Celery workers (70% cheaper)
- Use S3 Standard-IA storage class for processed images (40% cheaper after 30 days)
- Self-host models to avoid per-request AI API costs
- **Trade-off:** More infrastructure management, potential worker interruptions

### If team is small (1-3 developers)
- Minimize moving parts: Use Hugging Face Inference API (no GPU management)
- Use managed services: Cloud SQL, Redis Memorystore (no ops)
- Use GitHub Actions for CI/CD (no Jenkins/CircleCI setup)
- Use Sentry free tier for monitoring (no self-hosted Prometheus)
- **Trade-off:** Higher per-request costs, less customization

## Version Compatibility Matrix

| Package | Version | Compatible With | Notes |
|---------|---------|-----------------|-------|
| FastAPI | 0.115.x | Pydantic 2.x | Pydantic v1 no longer supported in FastAPI 0.100+ |
| SQLAlchemy | 2.0.x | asyncpg 0.29+, Alembic 1.13+ | SQLAlchemy 1.4 not compatible with async best practices |
| Pydantic | 2.x | FastAPI 0.100+, pydantic-settings 2.x | Major breaking changes from v1 |
| React Native | 0.76.x | react-native-vision-camera 4.x | Vision Camera 3.x only supports RN 0.72+ |
| Python | 3.11.x | All recommended packages | Python 3.12 supported but 3.11 more stable for ML libs |
| PostgreSQL | 16.x | asyncpg 0.30.x, SQLAlchemy 2.0 | PostgreSQL 15 also compatible, 16 has performance improvements |
| PyTorch | 2.x | ONNX Runtime 1.19+, torchvision 0.19+ | PyTorch 1.x deprecated |
| Celery | 5.4.x | Redis 7.x, Python 3.11+ | Celery 4.x not compatible with Python 3.11+ |
| Node.js | 20.x LTS | React Native 0.76.x | Use LTS version for stability |

## Confidence Levels by Technology

| Technology | Confidence | Rationale |
|------------|-----------|-----------|
| React Native + Vision Camera | **HIGH** | Industry-proven combination, 350K+ weekly downloads, active maintenance, extensive real-world usage |
| FastAPI + PostgreSQL | **HIGH** | Standard stack for Python APIs, official Google Cloud guide, mature ecosystem |
| PyTorch + ONNX Runtime | **HIGH** | Industry standard for CV, proven inference optimization, extensive documentation |
| Real-ESRGAN upscaling | **HIGH** | Battle-tested, open-source, widely used in production |
| U-Net iris segmentation | **HIGH** | Academic research shows 98%+ accuracy, proven architecture |
| Celery + Redis | **HIGH** | De facto standard for Python background tasks, handles ML workloads well |
| Reflection removal (LapCAT) | **MEDIUM** | Recent research (2025), may need custom training, less production usage |
| Stable Diffusion 3.5 integration | **MEDIUM** | Open-source but complex integration, resource-intensive, may need optimization |
| MediaPipe on React Native | **MEDIUM** | Requires native bridge, less documentation than web, but proven feasible |
| Google Cloud Run for AI workloads | **MEDIUM** | Excellent for API, but ML inference may need GPU Compute Engine instances |
| RevenueCat Web Billing | **MEDIUM** | New feature (2024-2025), lower conversion rates than native IAP, US-only |

## Technology Decision Log

### React Native vs Flutter (Mobile Framework)
**Decision:** React Native
**Rationale:**
1. **Camera ecosystem:** Vision Camera provides superior Frame Processors for real-time guidance (30-240 FPS)
2. **Native module maturity:** Easier integration with native camera APIs, more community packages
3. **Team knowledge:** JavaScript/TypeScript more common than Dart, easier to hire
4. **Web alignment:** React Native Web possible for future web app

**Trade-offs:**
- Flutter has better default UI consistency (Material/Cupertino)
- Flutter has slightly better performance for complex animations
- Flutter has single codebase for iOS/Android with less platform-specific code

**Confidence:** HIGH - camera requirements drive this decision

### PyTorch vs TensorFlow (ML Framework)
**Decision:** PyTorch
**Rationale:**
1. **Research velocity:** Better for iterating on custom models (iris segmentation, reflection removal)
2. **Ecosystem:** Superior computer vision model ecosystem (timm, torchvision)
3. **DX:** More Pythonic API, easier debugging
4. **Production parity:** ONNX Runtime + TorchServe close deployment gap with TF

**Trade-offs:**
- TensorFlow Lite has slight edge for mobile on-device models
- TensorFlow Serving is more mature than TorchServe
- TensorFlow has better enterprise adoption

**Confidence:** MEDIUM-HIGH - could choose TF, but PyTorch better for CV research

### Celery vs RQ (Task Queue)
**Decision:** Celery
**Rationale:**
1. **Scheduling:** Celery Beat essential for periodic tasks (cleanup, cache warming)
2. **Routing:** Complex AI pipeline needs task routing (GPU vs CPU workers)
3. **Monitoring:** Flower provides essential visibility into ML task queues
4. **Retries:** Built-in retry logic critical for flaky ML inference

**Trade-offs:**
- RQ is simpler to learn and operate
- RQ has less operational overhead
- Celery is more complex to configure

**Confidence:** HIGH - ML workloads justify Celery's complexity

### Google Cloud vs AWS (Cloud Provider)
**Decision:** Google Cloud Platform
**Rationale:**
1. **Simplicity:** Cloud Run is simpler than ECS/EKS for FastAPI deployment
2. **ML integration:** Better integration with AI/ML services (if needed later)
3. **Official support:** FastAPI official quickstart uses Cloud Run (updated Jan 2026)
4. **Cost:** Simpler pricing for serverless auto-scaling

**Trade-offs:**
- AWS has broader service catalog
- AWS has more enterprise adoption
- AWS has more mature ecosystem

**Confidence:** MEDIUM - AWS is viable alternative, team preference matters

### Self-hosted Models vs Hugging Face API (AI Hosting)
**Decision:** Hybrid approach
**Rationale:**
1. **Fast models self-hosted:** Segmentation, upscaling (2-15s) benefit from dedicated GPUs
2. **Slow models API:** Stable Diffusion (10-30s) can use HF Inference Endpoints
3. **Cost optimization:** Self-hosting cheaper at scale, API cheaper for low volume
4. **Flexibility:** Can migrate between approaches as volume scales

**Trade-offs:**
- Self-hosting requires GPU infrastructure management
- API calls have latency overhead and rate limits
- Hybrid adds architectural complexity

**Confidence:** HIGH - pragmatic approach balances cost and complexity

## Sources

### Framework & Library Documentation
- [FastAPI Official Documentation](https://fastapi.tiangolo.com/) - HIGH confidence
- [React Native Vision Camera](https://react-native-vision-camera.com/) - HIGH confidence
- [SQLAlchemy 2.0 Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) - HIGH confidence
- [PyTorch Official Documentation](https://pytorch.org/docs/stable/index.html) - HIGH confidence
- [ONNX Runtime Documentation](https://onnxruntime.ai/docs/) - HIGH confidence
- [Pydantic Documentation](https://docs.pydantic.dev/latest/) - HIGH confidence

### Research Papers (AI/ML Models)
- [Deep Learning for Iris Recognition Survey (ACM 2025)](https://dl.acm.org/doi/10.1145/3651306) - HIGH confidence
- [Neural Style Transfer Research (Nature 2025)](https://www.nature.com/articles/s41598-025-95819-9) - HIGH confidence
- [High-Resolution Reflection Removal (Nature 2025)](https://www.nature.com/articles/s41598-025-94464-6) - MEDIUM confidence
- [Iris Segmentation with U-Net (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7922029/) - HIGH confidence
- [Post-Mortem Iris Segmentation DeepLabV3+ (ArXiv 2024)](https://arxiv.org/abs/2408.03448) - MEDIUM confidence

### Technology Comparisons (2026)
- [Flutter vs React Native 2026](https://limeup.io/blog/flutter-vs-react-native/) - MEDIUM confidence
- [PyTorch vs TensorFlow 2026](https://www.hyperstack.cloud/blog/case-study/pytorch-vs-tensorflow) - MEDIUM confidence
- [Celery vs RQ Comparison](https://python.plainenglish.io/python-celery-vs-python-rq-for-distributed-tasks-processing-20041c346e6) - MEDIUM confidence
- [Cloudinary vs S3 Comparison](https://cloudinary.com/guides/ecosystems/cloudinary-vs-s3) - HIGH confidence

### Deployment & Infrastructure
- [FastAPI Cloud Run Quickstart (Jan 2026)](https://docs.cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-fastapi-service) - HIGH confidence
- [FastAPI Docker Deployment](https://fastapi.tiangolo.com/deployment/docker/) - HIGH confidence
- [Docker Compose FastAPI PostgreSQL Redis](https://www.khueapps.com/blog/article/setup-docker-compose-for-fastapi-postgres-redis-and-nginx-caddy) - MEDIUM confidence
- [GitHub Actions FastAPI CI/CD](https://pyimagesearch.com/2024/11/11/fastapi-with-github-actions-and-ghcr-continuous-delivery-made-simple/) - MEDIUM confidence

### Best Practices
- [FastAPI Best Practices 2026](https://github.com/zhanymkanov/fastapi-best-practices) - HIGH confidence
- [SQLAlchemy 2.0 Async Best Practices](https://leapcell.io/blog/building-high-performance-async-apis-with-fastapi-sqlalchemy-2-0-and-asyncpg) - HIGH confidence
- [FastAPI at Scale 2026](https://medium.com/@kaushalsinh73/fastapi-at-scale-in-2026-pydantic-v2-uvloop-http-3-which-knob-moves-latency-vs-throughput-cd0a601179de) - MEDIUM confidence

### Authentication & Payments
- [Apple Sign In Requirement 2025](https://workos.com/blog/apple-app-store-authentication-sign-in-with-apple-2025) - HIGH confidence
- [RevenueCat Stripe Integration](https://www.revenuecat.com/blog/engineering/can-you-use-stripe-for-in-app-purchases/) - HIGH confidence
- [RevenueCat Pricing 2026](https://www.metacto.com/blogs/the-real-cost-of-revenuecat-what-app-publishers-need-to-know) - MEDIUM confidence
- [Firebase Auth Documentation](https://firebase.google.com/docs/auth/ios/google-signin) - HIGH confidence

### Real-Time Processing
- [MediaPipe Real-Time Body Tracking](https://medium.com/@creativeainspiration/real-time-body-tracking-in-your-browser-what-mediapipe-actually-does-and-how-to-use-it-b31aa96a5071) - MEDIUM confidence
- [MediaPipe Computer Vision Demos](https://github.com/Naveenp7/MediaPipe-Real-Time-Computer-Vision-Demos) - MEDIUM confidence
- [Flutter Camera Real-Time ML](https://medium.com/kbtg-life/real-time-machine-learning-with-flutter-camera-bbcf1b5c3193) - MEDIUM confidence

### AI Model Resources
- [Real-ESRGAN GitHub](https://github.com/xinntao/Real-ESRGAN) - HIGH confidence
- [Best AI Image Upscalers 2026](https://letsenhance.io/blog/all/best-ai-image-upscalers/) - MEDIUM confidence
- [Stable Diffusion vs FLUX 2026](https://www.gradually.ai/en/ai-image-models/) - MEDIUM confidence
- [Hugging Face Inference Providers](https://huggingface.co/docs/inference-providers/en/index) - HIGH confidence
- [ONNX Runtime PyTorch Tutorial](https://onnxruntime.ai/docs/tutorials/accelerate-pytorch/pytorch.html) - HIGH confidence

---

*Stack research for: IrisVue - Cross-platform iris photography AI art mobile app*
*Researched: 2026-02-01*
*Confidence: HIGH (core technologies), MEDIUM (AI model integration details)*

## Next Steps

After reviewing this stack recommendation:

1. **Validate mobile framework choice:** Build React Native Vision Camera prototype with Frame Processors to confirm real-time guidance feasibility
2. **Benchmark AI models:** Test segmentation models (U-Net vs DeepLabV3+) on sample iris images to validate accuracy/speed
3. **Cost modeling:** Calculate cloud infrastructure costs for expected user volume (storage, compute, AI API calls)
4. **Team alignment:** Confirm team has Python + JavaScript/TypeScript expertise, or plan training
5. **Architecture validation:** Review ARCHITECTURE.md for system design that uses this stack
6. **Prototype critical path:** Build end-to-end prototype (camera capture → segmentation → display) to de-risk technical unknowns
