# Phase 7: Polish and Production Readiness - Research

**Researched:** 2026-02-10
**Domain:** CI/CD automation, production monitoring, CDN optimization, app store compliance
**Confidence:** HIGH

## Summary

Phase 7 brings IrisVue from a functional full-stack application to a production-ready product ready for App Store and Play Store submission. This phase focuses on four critical areas: CI/CD automation for reliable builds and deployments, production monitoring with Sentry for error tracking, CDN optimization for fast global image delivery, and app store compliance (Privacy Manifest, permissions, review guidelines).

The standard stack is well-established and mature: GitHub Actions for CI/CD (native to the repository with excellent React Native and Docker support), Sentry for error tracking (official SDKs for both React Native and FastAPI with Hermes support), CloudFront + MinIO for CDN (leveraging existing S3-compatible storage), and Fastlane for mobile build automation (industry standard for iOS and Android releases).

Current state: The project has no CI/CD pipeline (.github directory doesn't exist), no tests (backend/tests and mobile minimal test coverage), no production monitoring, and direct MinIO access without CDN. Docker Compose is dev-only. The mobile app uses React Native 0.83.1 with Hermes enabled by default, FastAPI backend with Docker, and MinIO for object storage.

**Primary recommendation:** Build CI/CD incrementally — start with automated testing and linting, add Docker builds and push to registry, then add iOS/Android builds with caching. Deploy Sentry early for pre-launch testing. Use CloudFront as CDN origin for MinIO with bucket policies. Defer over-the-air (OTA) updates to post-launch (CodePush retiring, alternatives immature).

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| GitHub Actions | Native | CI/CD pipeline automation | Native to GitHub, excellent ecosystem, free for public repos, generous free tier for private, mature React Native and Docker support |
| Sentry | Latest SDK | Error tracking and performance monitoring | Industry standard for production monitoring, official React Native and FastAPI SDKs, source map support for Hermes, distributed tracing between frontend and backend |
| Fastlane | Latest (Ruby) | Mobile build automation | De facto standard for React Native iOS/Android automation, handles certificates, provisioning, TestFlight, Play Console |
| Amazon CloudFront | AWS Service | CDN for global image delivery | AWS-native CDN, integrates with S3-compatible origins (MinIO via bucket policy), pay-as-you-go pricing, global edge network |
| pytest | 7.x+ | Backend testing framework | Python standard for testing, excellent FastAPI support via TestClient, async support, fixture management |
| Jest | 29.x (already installed) | Mobile testing framework | React Native default, component testing, snapshot testing, mocking |
| Detox | 20.x+ | Mobile E2E testing | Gray-box testing specifically built for React Native, automatic synchronization, CI-friendly, reduces flakiness |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-asyncio | Latest | Async test support for pytest | Testing async FastAPI endpoints and Celery tasks |
| pytest-cov | Latest | Code coverage reporting | CI pipeline coverage checks, enforce minimum coverage thresholds |
| @sentry/cli | Latest | Sentry release management | Upload source maps, create releases, associate commits with deploys |
| fastapi-healthchecks | Latest | Health check endpoints | Kubernetes/Docker liveness and readiness probes |
| actions/cache@v3 | GitHub Action | Build caching | Speed up CI builds (Gradle, CocoaPods, node_modules, Docker layers) |
| mikehardy/buildcache-action | GitHub Action | Advanced build caching | Further optimize React Native native compilation (50% improvement) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| GitHub Actions | CircleCI, GitLab CI | GitHub Actions integrates natively, free tier sufficient, ecosystem mature for React Native |
| Sentry | Bugsnag, Rollbar | Sentry has superior React Native Hermes support, distributed tracing, official FastAPI integration |
| CloudFront | Cloudinary | Cloudinary offers built-in transformations but costs more; we already have MinIO, CloudFront leverages it |
| Fastlane | Manual Xcode/Android Studio | Fastlane automates certificate management, version bumping, store submission — essential for CI/CD |
| Detox | Appium, Maestro | Detox is purpose-built for React Native with automatic synchronization, less flaky than Appium |

**Installation:**

Backend testing:
```bash
# Backend (add to requirements.txt)
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
httpx>=0.24.0  # Already installed for FastAPI TestClient
fastapi-healthchecks>=0.1.0
```

Mobile testing:
```bash
# Mobile (Detox — run from mobile/)
npm install --save-dev detox detox-cli
# iOS simulator tools
brew tap wix/brew
brew install applesimutils
```

CI/CD and monitoring:
```bash
# Fastlane (macOS with Ruby)
gem install fastlane

# Sentry CLI (for source maps)
npm install --save-dev @sentry/cli

# Sentry SDKs
npm install --save @sentry/react-native  # Mobile
pip install sentry-sdk[fastapi]          # Backend
```

## Architecture Patterns

### Recommended Project Structure

```
.github/
├── workflows/
│   ├── backend-ci.yml          # Backend: test, lint, build Docker, push to registry
│   ├── mobile-android.yml      # Android: test, lint, build APK/AAB, cache Gradle
│   ├── mobile-ios.yml          # iOS: test, lint, build IPA, cache CocoaPods
│   └── deploy.yml              # Deploy backend Docker image to production server
backend/
├── tests/
│   ├── conftest.py             # Pytest fixtures (TestClient, test DB, async session)
│   ├── test_auth.py            # Auth endpoints
│   ├── test_photos.py          # Photo upload/gallery
│   ├── test_processing.py      # AI processing pipeline
│   └── test_health.py          # Health check endpoints
├── app/
│   ├── health.py               # /health/readiness and /health/liveness
│   └── main.py                 # Sentry init, health routes
├── Dockerfile                  # Multi-stage build (builder + runtime)
└── .env.production             # Production environment variables (not committed)
mobile/
├── e2e/                        # Detox E2E tests
│   ├── auth.test.js            # Login flow
│   ├── capture.test.js         # Camera capture flow
│   └── gallery.test.js         # Gallery navigation
├── .detoxrc.js                 # Detox configuration
├── ios/
│   └── fastlane/
│       ├── Fastfile            # iOS lanes: beta (TestFlight), release (App Store)
│       └── Appfile             # App identifier, team ID
├── android/
│   └── fastlane/
│       ├── Fastfile            # Android lanes: beta (internal track), release
│       └── Appfile             # Package name
└── sentry.properties           # Sentry org/project for source map upload
```

### Pattern 1: GitHub Actions Workflow Structure

**What:** Modular CI/CD with separate workflows for backend and mobile, using matrix builds for multi-platform, and caching for speed.

**When to use:** All projects with backend + mobile apps. Separates concerns, parallelizes builds, and speeds up feedback loops.

**Example:**
```yaml
# .github/workflows/backend-ci.yml
name: Backend CI

on:
  push:
    branches: [main, develop]
    paths:
      - 'backend/**'
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
      redis:
        image: redis:7-alpine
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests --cov --cov-report=xml
      - uses: codecov/codecov-action@v4  # Optional: upload coverage

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: backend
          push: true
          tags: ghcr.io/${{ github.repository }}/backend:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Pattern 2: Multi-Stage Docker Build for Production

**What:** Separate builder and runtime stages to minimize final image size, improve security (non-root user), and optimize layer caching.

**When to use:** All production Docker images. Reduces image size by 30-50%, speeds up deployments, and removes build tools from runtime.

**Example:**
```dockerfile
# backend/Dockerfile (multi-stage optimized)
FROM python:3.12-slim AS builder

WORKDIR /build
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim

# Non-root user for security
RUN useradd -m -u 1000 app

WORKDIR /code
# Copy installed packages from builder
COPY --from=builder /install /usr/local
COPY --chown=app:app app/ ./app/
COPY --chown=app:app alembic/ ./alembic/
COPY --chown=app:app alembic.ini .

USER app
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Pattern 3: Fastlane Lanes for Beta and Release

**What:** Fastlane "lanes" automate iOS/Android build steps: increment build number, sync certificates, build, upload to TestFlight/Play Console.

**When to use:** React Native projects targeting App Store and Play Store. Eliminates manual certificate management and store submission errors.

**Example:**
```ruby
# mobile/ios/fastlane/Fastfile
default_platform(:ios)

platform :ios do
  desc "Push a new beta build to TestFlight"
  lane :beta do
    # Sync code signing (match or cert/sigh)
    sync_code_signing(type: "appstore", readonly: true)

    # Increment build number based on TestFlight
    increment_build_number(
      xcodeproj: "IrisArt.xcodeproj",
      build_number: latest_testflight_build_number + 1
    )

    # Build the app
    build_app(
      scheme: "IrisArt",
      export_method: "app-store",
      output_directory: "./build",
      clean: true
    )

    # Upload to TestFlight
    upload_to_testflight(
      skip_waiting_for_build_processing: true
    )
  end

  desc "Deploy to App Store"
  lane :release do
    sync_code_signing(type: "appstore", readonly: true)
    build_app(scheme: "IrisArt", export_method: "app-store")
    upload_to_app_store(
      submit_for_review: true,
      automatic_release: false
    )
  end
end
```

### Pattern 4: Sentry Initialization and Release Tracking

**What:** Initialize Sentry in app entry points, upload source maps on build, and associate releases with commits for traceable error reports.

**When to use:** All production apps. Enables one-click navigation from error to source code line, and correlates errors with deployments.

**Example (Mobile):**
```typescript
// mobile/index.js
import * as Sentry from '@sentry/react-native';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: __DEV__ ? 'development' : 'production',
  enabled: !__DEV__,  // Disable in dev to avoid noise
  tracesSampleRate: 0.1,  // 10% performance monitoring
  integrations: [
    new Sentry.ReactNativeTracing({
      routingInstrumentation: new Sentry.ReactNavigationInstrumentation(),
    }),
  ],
  beforeSend(event) {
    // Scrub sensitive data
    if (event.request?.cookies) {
      delete event.request.cookies;
    }
    return event;
  },
});
```

**Example (Backend):**
```python
# backend/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    integrations=[
        FastApiIntegration(),
        CeleryIntegration(),
    ],
    traces_sample_rate=0.1,  # 10% performance monitoring
    profiles_sample_rate=0.1,  # 10% profiling
    before_send=scrub_sensitive_data,
)
```

### Pattern 5: Health Check Endpoints for Production

**What:** Separate liveness (is the app running?) and readiness (can it serve traffic?) probes for container orchestration.

**When to use:** Docker/Kubernetes deployments. Prevents routing traffic to unhealthy containers and auto-restarts dead containers.

**Example:**
```python
# backend/app/health.py
from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from app.database import get_db
from app.redis_client import get_redis

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/liveness", status_code=status.HTTP_200_OK)
async def liveness():
    """Simple check: is the app process running?"""
    return {"status": "alive"}

@router.get("/readiness")
async def readiness(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """Complex check: can we serve traffic? (DB + Redis reachable)"""
    try:
        # Check DB
        await db.execute("SELECT 1")
        # Check Redis
        await redis.ping()
        return {"status": "ready", "db": "ok", "redis": "ok"}
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}, 503
```

### Anti-Patterns to Avoid

- **Committing secrets to .env files:** Use GitHub Secrets for CI/CD, environment variables on production servers. Never commit API keys, tokens, or passwords.
- **Running tests only locally:** CI/CD must run tests on every push. "Works on my machine" is not production-ready.
- **No caching in CI:** React Native builds take 15-30min without caching. Use actions/cache for node_modules, Gradle, CocoaPods, and Docker layers.
- **Exposing Flower without authentication:** Flower on port 5555 with no auth is a common security vulnerability. Use --basic_auth or reverse proxy with OAuth.
- **Manual app version bumping:** Fastlane should auto-increment build numbers based on latest TestFlight/Play Console build to avoid conflicts.
- **Ignoring health checks:** Without /health/readiness, load balancers route traffic to containers still initializing databases, causing 500 errors.
- **One-size-fits-all Docker image:** Separate dev (with hot reload, debug tools) and production (optimized, non-root user) Dockerfiles or stages.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CI/CD pipeline | Custom Jenkins server, bash scripts | GitHub Actions | Native integration, free tier, mature ecosystem, no server maintenance, excellent React Native and Docker support |
| iOS code signing | Manual certificate management | Fastlane Match or sync_code_signing | iOS certificates expire, provisioning profiles conflict, Match stores certs in encrypted Git repo, auto-renews |
| Error tracking | Logging + manual log review | Sentry | Aggregates errors, source maps, stack traces, release tracking, alerting, integrations — logging alone is insufficient at scale |
| Mobile OTA updates | Custom update server | Defer to post-launch; if needed, use react-native-ota-hot-update or hot-updater | CodePush retiring, alternatives immature, adds complexity, not needed for v1 launch |
| CDN | Self-hosted CDN, proxy layer | CloudFront with MinIO origin | Global edge network, HTTPS, pay-as-you-go, leverages existing MinIO storage, no maintenance |
| Build caching | Manual cache management | actions/cache + mikehardy/buildcache-action | Proper cache invalidation is hard; GitHub Actions cache is free, automatic, and well-tested |
| Health checks | Custom monitoring scripts | fastapi-healthchecks library | Kubernetes-ready liveness/readiness probes with built-in checks for PostgreSQL, Redis, RabbitMQ |
| App Store submission | Manual Xcode uploads | Fastlane upload_to_testflight and upload_to_app_store | Automates metadata, screenshots, version bumping, and submission — eliminates human error |

**Key insight:** Production readiness is 80% integration work and 20% custom code. Don't rebuild GitHub Actions, Sentry, or Fastlane. Use the standard stack and focus on app-specific logic (test cases, health checks, deployment configs). The ecosystem is mature — leverage it.

## Common Pitfalls

### Pitfall 1: Missing Privacy Manifest on iOS Submission

**What goes wrong:** App Store rejects app with error "Missing Privacy Manifest" (ITMS-91053) for third-party SDKs using required reason APIs (e.g., UserDefaults, file timestamps).

**Why it happens:** Apple requires privacy manifests since May 1, 2024. React Native and third-party libraries may not include PrivacyInfo.xcprivacy files, and the app must provide one.

**How to avoid:**
1. Create `mobile/ios/IrisArt/PrivacyInfo.xcprivacy` with required reason APIs used by the app (NSPrivacyAccessedAPITypes).
2. List all third-party SDKs that use required reason APIs (e.g., @react-native-async-storage/async-storage, react-native-fs).
3. Use Xcode's "Generate Privacy Report" to audit SDK usage.
4. Test submission with TestFlight before final release.

**Warning signs:** App Store Connect emails about missing privacy manifests, rejection during review with ITMS-91053 error code.

### Pitfall 2: Hermes Source Maps Not Uploaded to Sentry

**What goes wrong:** Production crashes in React Native show minified stack traces like `value.map is not a function at anonymous (index.android.bundle:1:234567)` — impossible to debug.

**Why it happens:** Hermes uses bytecode compilation, requiring Hermes-specific source maps. Default React Native build doesn't auto-upload to Sentry, and manual upload requires specific configuration.

**How to avoid:**
1. Enable Hermes (default in RN 0.83+).
2. Configure Sentry CLI with `sentry.properties` (org, project, auth token).
3. Add Sentry React Native Gradle plugin to `android/app/build.gradle` and Xcode build phase for iOS.
4. Verify source maps with `sentry-cli sourcemaps explain <event-id>` after first production error.

**Warning signs:** Sentry errors show `<unknown>` file names or bytecode offsets instead of source file paths.

### Pitfall 3: CI Build Times Exceeding Free Tier Limits

**What goes wrong:** GitHub Actions free tier (2,000 minutes/month for private repos) consumed in 1-2 weeks due to 30-minute React Native builds. CI becomes bottleneck or incurs costs.

**Why it happens:** React Native Android builds compile native C++ libraries for 4 ABIs (arm64-v8a, armeabi-v7a, x86, x86_64) — takes 15-30min on first build. iOS builds compile Swift/Objective-C. No caching = every push repeats full build.

**How to avoid:**
1. Enable caching for Gradle, CocoaPods, node_modules, and Docker layers (actions/cache@v3).
2. Use mikehardy/buildcache-action for React Native native compilation (50% improvement).
3. Enable Gradle configuration caching (RN 0.79+): `org.gradle.configuration-cache=true` in `gradle.properties`.
4. Run iOS builds only on release branches or manually to save macOS runner minutes (10x cost vs Linux).
5. Use matrix builds to parallelize Android/iOS when budget allows.

**Warning signs:** GitHub Actions usage dashboard shows rapid minute consumption, CI queues build due to minute limits.

### Pitfall 4: Exposed Flower Dashboard Without Authentication

**What goes wrong:** Celery Flower monitoring dashboard (port 5555) exposed to internet without authentication. Attackers can view sensitive task data, cancel jobs, or stop workers.

**Why it happens:** Default Flower configuration has no authentication. Developers expose port in docker-compose.yml for convenience, forget to add --basic_auth in production, or assume firewall is sufficient.

**How to avoid:**
1. **Never expose Flower to public internet in production.** Use SSH tunnel or VPN for access.
2. If public access needed, enable basic auth: `celery -A app.workers.celery_app flower --basic_auth=admin:secure_password_here`
3. Better: Use reverse proxy (Caddy, Nginx) with OAuth or JWT authentication.
4. In docker-compose, bind Flower to localhost: `127.0.0.1:5555:5555` and access via SSH tunnel.

**Warning signs:** Port 5555 accessible from public IP without login prompt, Shodan scan finds your Flower instance.

### Pitfall 5: MinIO Presigned URLs Not Working with CloudFront

**What goes wrong:** Mobile app requests presigned URL from backend, URL contains MinIO's internal hostname (e.g., `http://minio:9000/...`), fails with DNS resolution error or wrong hostname.

**Why it happens:** MinIO generates presigned URLs based on the `Host` header in the request. In Docker Compose, backend calls MinIO via service name `minio`, but mobile app can't resolve that hostname.

**How to avoid:**
1. Configure MinIO with public domain: `MINIO_SERVER_URL=https://storage.example.com` in environment variables.
2. Use CloudFront as origin for MinIO bucket, set CloudFront domain in presigned URL generation.
3. Alternatively, generate presigned URLs with explicit `endpoint_url` parameter pointing to public domain.
4. Test presigned URLs from outside Docker network (e.g., from mobile device) before production.

**Warning signs:** Mobile app gets S3 presigned URLs but upload/download fails with DNS errors or connection refused.

### Pitfall 6: Docker Image Size Bloating Production Deploys

**What goes wrong:** Backend Docker image is 2-3GB due to build tools, dev dependencies, and cache files. Deployments are slow, registry storage costs increase.

**Why it happens:** Single-stage Dockerfile installs all dependencies including build tools (gcc, g++, etc.), doesn't remove pip cache, and includes unnecessary files (tests, docs).

**How to avoid:**
1. Use multi-stage build: builder stage installs dependencies, runtime stage only copies installed packages.
2. Use `--no-cache-dir` with pip to skip cache: `pip install --no-cache-dir -r requirements.txt`
3. Use slim base images: `python:3.12-slim` instead of `python:3.12` (saves ~500MB).
4. Create non-root user in final stage for security.
5. Use .dockerignore to exclude tests, .git, node_modules, etc.

**Warning signs:** Docker image exceeds 1GB, `docker history` shows large layers from pip cache or build tools.

## Code Examples

Verified patterns from official sources and production-tested configurations.

### GitHub Actions: React Native Android Build with Caching

```yaml
# .github/workflows/mobile-android.yml
name: Android Build

on:
  push:
    branches: [main]
    paths:
      - 'mobile/**'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: mobile/package-lock.json

      - uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '21'

      # Cache Gradle dependencies
      - uses: actions/cache@v3
        with:
          path: |
            ~/.gradle/caches
            ~/.gradle/wrapper
          key: ${{ runner.os }}-gradle-${{ hashFiles('mobile/android/**/*.gradle*', 'mobile/android/**/gradle-wrapper.properties') }}

      # Cache node_modules
      - run: npm ci
        working-directory: mobile

      # Decode and save Android keystore from secrets
      - name: Decode Keystore
        run: |
          echo "${{ secrets.ANDROID_KEYSTORE_BASE64 }}" | base64 -d > mobile/android/app/release.keystore

      # Build release APK
      - name: Build Android Release
        working-directory: mobile/android
        run: ./gradlew assembleRelease
        env:
          KEYSTORE_PASSWORD: ${{ secrets.ANDROID_KEYSTORE_PASSWORD }}
          KEY_ALIAS: ${{ secrets.ANDROID_KEY_ALIAS }}
          KEY_PASSWORD: ${{ secrets.ANDROID_KEY_PASSWORD }}

      # Upload APK artifact
      - uses: actions/upload-artifact@v4
        with:
          name: app-release.apk
          path: mobile/android/app/build/outputs/apk/release/app-release.apk
```

### GitHub Actions: iOS Build with CocoaPods Caching

```yaml
# .github/workflows/mobile-ios.yml
name: iOS Build

on:
  workflow_dispatch:  # Manual trigger only (save macOS minutes)
  push:
    branches: [main]
    paths:
      - 'mobile/ios/**'

jobs:
  build:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: mobile/package-lock.json

      # Cache CocoaPods
      - uses: actions/cache@v3
        with:
          path: mobile/ios/Pods
          key: ${{ runner.os }}-pods-${{ hashFiles('mobile/ios/Podfile.lock') }}

      - run: npm ci
        working-directory: mobile

      # Install CocoaPods dependencies
      - name: Install Pods
        working-directory: mobile/ios
        run: pod install

      # Setup Fastlane
      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.2'
          bundler-cache: true
          working-directory: mobile/ios

      # Build with Fastlane
      - name: Build iOS
        working-directory: mobile/ios
        run: bundle exec fastlane build_for_testing
        env:
          MATCH_PASSWORD: ${{ secrets.MATCH_PASSWORD }}
          FASTLANE_USER: ${{ secrets.FASTLANE_USER }}
          FASTLANE_PASSWORD: ${{ secrets.FASTLANE_PASSWORD }}
```

### Pytest: FastAPI Test Fixtures and Test Case

```python
# backend/tests/conftest.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/iris_art_test"

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def test_db(test_engine):
    """Create test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(test_db):
    """Create test client with dependency override."""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

# backend/tests/test_health.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_liveness(client: AsyncClient):
    """Test liveness probe returns 200."""
    response = await client.get("/health/liveness")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"

@pytest.mark.asyncio
async def test_readiness(client: AsyncClient):
    """Test readiness probe checks DB and Redis."""
    response = await client.get("/health/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["db"] == "ok"
    assert data["redis"] == "ok"
```

### Detox: E2E Test Configuration and Test Case

```javascript
// mobile/.detoxrc.js
module.exports = {
  testRunner: {
    args: {
      $0: 'jest',
      config: 'e2e/jest.config.js',
    },
    jest: {
      setupTimeout: 120000,
    },
  },
  apps: {
    'ios.debug': {
      type: 'ios.app',
      binaryPath: 'ios/build/Build/Products/Debug-iphonesimulator/IrisArt.app',
      build: 'xcodebuild -workspace ios/IrisArt.xcworkspace -scheme IrisArt -configuration Debug -sdk iphonesimulator -derivedDataPath ios/build',
    },
    'android.debug': {
      type: 'android.apk',
      binaryPath: 'android/app/build/outputs/apk/debug/app-debug.apk',
      build: 'cd android && ./gradlew assembleDebug assembleAndroidTest -DtestBuildType=debug',
    },
  },
  devices: {
    simulator: {
      type: 'ios.simulator',
      device: {
        type: 'iPhone 15',
      },
    },
    emulator: {
      type: 'android.emulator',
      device: {
        avdName: 'Pixel_6_API_34',
      },
    },
  },
  configurations: {
    'ios.sim.debug': {
      device: 'simulator',
      app: 'ios.debug',
    },
    'android.emu.debug': {
      device: 'emulator',
      app: 'android.debug',
    },
  },
};

// mobile/e2e/auth.test.js
describe('Authentication Flow', () => {
  beforeAll(async () => {
    await device.launchApp();
  });

  it('should show login screen on app launch', async () => {
    await expect(element(by.id('login-screen'))).toBeVisible();
  });

  it('should login with email and password', async () => {
    await element(by.id('email-input')).typeText('test@example.com');
    await element(by.id('password-input')).typeText('password123');
    await element(by.id('login-button')).tap();

    // Wait for navigation to home screen
    await waitFor(element(by.id('home-screen')))
      .toBeVisible()
      .withTimeout(5000);
  });
});
```

### Sentry: React Native Source Map Upload (Gradle Plugin)

```gradle
// mobile/android/app/build.gradle (add after apply plugin: "com.facebook.react")
apply plugin: 'io.sentry.android.gradle'

sentry {
    autoUploadProguardMapping = true
    uploadNativeSymbols = false  // Not needed for Hermes
    includeNativeSources = false

    org = System.env.SENTRY_ORG ?: ""
    project = System.env.SENTRY_PROJECT ?: ""
    authToken = System.env.SENTRY_AUTH_TOKEN ?: ""
}
```

```bash
# mobile/ios/Podfile (add Sentry dependency)
pod 'Sentry', :git => 'https://github.com/getsentry/sentry-cocoa.git', :tag => '8.38.0'
```

```bash
# mobile/ios Xcode Build Phase (add script after "Bundle React Native code and images")
export SENTRY_ORG=your-org
export SENTRY_PROJECT=your-project
export SENTRY_AUTH_TOKEN=your-token
../node_modules/@sentry/cli/bin/sentry-cli releases \
  files "$SENTRY_RELEASE" \
  upload-sourcemaps \
  --dist "$SENTRY_DIST" \
  --rewrite \
  "$CONFIGURATION_BUILD_DIR/$UNLOCALIZED_RESOURCES_FOLDER_PATH/main.jsbundle.map"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| CodePush for OTA updates | Self-hosted OTA (hot-updater, react-native-ota-hot-update) or defer | 2024 (CodePush retiring) | Must evaluate alternatives or skip OTA for v1; self-hosted adds complexity |
| Manual iOS certificate management | Fastlane Match | ~2016 | Auto-renews certificates, stores in encrypted Git repo, eliminates provisioning profile conflicts |
| Cloudinary for all images | CloudFront + origin storage (MinIO) | Ongoing | Cloudinary excellent for transformations but expensive; CloudFront + MinIO leverages existing storage, pay-as-you-go |
| JavaScript Core (JSC) | Hermes (default since RN 0.70) | 2021-2022 | 20-40% startup improvement, smaller bundle size, requires Hermes-specific source maps for Sentry |
| Bugsnag, custom logging | Sentry (React Native + FastAPI official SDKs) | 2020+ | Distributed tracing, source maps, release tracking, superior Hermes support, FastAPI integration |
| CircleCI, Jenkins | GitHub Actions | 2019+ | Native to GitHub, no server maintenance, free tier sufficient, mature ecosystem for React Native and Docker |
| Single-stage Dockerfile | Multi-stage builds | ~2017 | 30-50% smaller images, faster deployments, better security (non-root user, no build tools in runtime) |

**Deprecated/outdated:**
- **CodePush (Microsoft)**: Officially retiring, no long-term support. Alternatives: hot-updater (self-hosted) or defer OTA to post-launch.
- **React Native < 0.70 without Hermes**: Hermes is now default and recommended for all production apps. JSC still supported but not optimized.
- **Manual app version bumping**: Fastlane automates version bumping based on latest TestFlight/Play Console build, eliminates human error.

## Open Questions

1. **What's the production deployment target for the backend?**
   - What we know: Docker Compose is dev-only. Backend needs production deployment (cloud VM, managed container service, etc.).
   - What's unclear: AWS EC2, DigitalOcean Droplet, Kubernetes, or managed service (Render, Railway, Fly.io)? Impacts CI/CD deploy step.
   - Recommendation: Defer to planning phase. If simple VM, use Docker Compose with docker-compose.production.yml. If Kubernetes, add Helm charts. For MVP, single VM with Docker Compose + Traefik reverse proxy is sufficient.

2. **What's the budget for GitHub Actions macOS runners for iOS builds?**
   - What we know: macOS runners cost 10x Linux runners. Free tier: 2,000 minutes/month (private repos) = ~200 macOS minutes.
   - What's unclear: Build frequency, iOS vs Android priority, manual vs automatic iOS builds.
   - Recommendation: Run iOS builds only on release branches or manually (workflow_dispatch) to conserve macOS minutes. Use Linux for all other jobs (Android, backend).

3. **Should we implement OTA (over-the-air) updates for Phase 7?**
   - What we know: CodePush is retiring. Alternatives exist (hot-updater, react-native-ota-hot-update) but add complexity.
   - What's unclear: User need for instant bug fixes vs app store review time (iOS ~1-3 days, Android ~hours).
   - Recommendation: Defer OTA to post-launch. App Store and Play Store review times are acceptable for MVP. OTA adds complexity (update server, version management, rollback logic) without validated user need.

4. **What's the test coverage target for CI?**
   - What we know: No tests currently exist (backend/tests empty, mobile minimal coverage).
   - What's unclear: Minimum coverage threshold for CI to pass (e.g., 80%, 60%, or just smoke tests?).
   - Recommendation: Start with smoke tests (health checks, auth login, critical paths) and set coverage target at 60% for Phase 7, increase incrementally post-launch. Perfect is the enemy of shipped.

5. **Should Celery workers be separate CI/CD pipeline or bundled with backend?**
   - What we know: Celery workers use same codebase as backend but run different processes. Production may need separate scaling.
   - What's unclear: If workers need independent deployment or if they share backend Docker image.
   - Recommendation: Same Docker image, different entrypoint command. CI builds one backend image, docker-compose.production.yml runs `celery worker` for worker service and `uvicorn` for web service. Simplifies CI/CD and ensures version parity.

## Sources

### Primary (HIGH confidence)

**CI/CD and GitHub Actions:**
- [React Native CI/CD using GitHub Actions - LogRocket](https://blog.logrocket.com/react-native-ci-cd-using-github-actions/)
- [React Native + Github Action = ❤️ - Obytes](https://www.obytes.com/blog/react-native-ci-cd-github-action)
- [FastAPI with GitHub Actions and GHCR - PyImageSearch](https://pyimagesearch.com/2024/11/11/fastapi-with-github-actions-and-ghcr-continuous-delivery-made-simple/)
- [FastAPI Docker Best Practices - Better Stack](https://betterstack.com/community/guides/scaling-python/fastapi-docker-best-practices/)

**Sentry Integration:**
- [Sentry for React Native - Official Docs](https://docs.sentry.io/platforms/react-native/)
- [Sentry for FastAPI - Official](https://sentry.io/for/fastapi/)
- [Hermes Source Maps - Sentry Docs](https://docs.sentry.io/platforms/react-native/manual-setup/hermes/)

**Fastlane Automation:**
- [React Native - Fastlane Docs](https://docs.fastlane.tools/getting-started/cross-platform/react-native/)
- [Fastlane: Build, test, and ship React Native apps - LogRocket](https://blog.logrocket.com/fastlane-build-test-ship-react-native-apps/)
- [React Native Build Pipeline Guide Using EAS and Fastlane - Medium](https://medium.com/@ali.shabbir6706/react-native-build-pipeline-guide-using-eas-and-fastlane-d71889ef8d07)

**App Store Requirements:**
- [Adding a privacy manifest to your app - Apple Developer](https://developer.apple.com/documentation/bundleresources/adding-a-privacy-manifest-to-your-app-or-third-party-sdk)
- [Privacy updates for App Store submissions - Apple](https://developer.apple.com/news/?id=3d8a9yyh)
- [Publishing to Google Play Store - React Native](https://reactnative.dev/docs/signed-apk-android)

**React Native Performance:**
- [How to Use Hermes Engine for Better React Native Performance - OneUpTime](https://oneuptime.com/blog/post/2026-01-15-react-native-hermes-engine/view)
- [Using Hermes - React Native Docs](https://reactnative.dev/docs/hermes)

### Secondary (MEDIUM confidence)

**Testing:**
- [The Complete FastAPI × pytest Guide - Greeden Blog](https://blog.greeden.me/en/2026/01/06/the-complete-fastapi-x-pytest-guide-building-fearless-to-change-apis-with-unit-tests-api-tests-integration-tests-and-mocking-strategies/)
- [Simple Step-by-Step Setup Detox for React Native Android E2E Testing 2026 - Medium](https://medium.com/@svbala99/simple-step-by-step-setup-detox-for-react-native-android-e2e-testing-2026-ed497fd9d301)
- [How to Write Integration Tests for React Native with Detox - OneUpTime](https://oneuptime.com/blog/post/2026-01-15-react-native-detox-testing/view)

**Build Optimization:**
- [Slimmer FastAPI Docker Images with Multi-Stage Builds](https://davidmuraya.com/blog/slimmer-fastapi-docker-images-multistage-builds/)
- [GitHub Actions build caching React Native - Callstack](https://www.callstack.com/blog/caching-react-native-builds-on-s3-and-r2)
- [Speeding up your Build phase - React Native](https://reactnative.dev/docs/build-speed)

**CDN and Storage:**
- [Cloudinary vs CloudFront - StackShare](https://stackshare.io/stackups/amazon-cloudfront-vs-cloudinary)
- [Comparing Cloudinary CDN and Amazon AWS CDN CloudFront - HackerNoon](https://hackernoon.com/comparing-cloudinary-cdn-and-amazon-aws-cdn-cloudfront)

**Monitoring:**
- [FastAPI Health Checks and Timeouts - Medium](https://medium.com/@bhagyarana80/fastapi-health-checks-and-timeouts-avoiding-zombie-containers-in-production-411a27c2a019)
- [Monitoring Celery Workers with Flower - DEV Community](https://dev.to/soumyajyoti-devops/monitoring-celery-workers-with-flower-your-tasks-need-babysitting-3ime)
- [How I Found and reported 50+ Exposed Celery Flower Dashboards - Medium](https://vijetareigns.medium.com/how-i-found-and-reported-50-exposed-celery-flower-dashboards-on-shodan-f4de4289630c)

### Tertiary (LOW confidence, flagged for validation)

**OTA Updates:**
- [React Native CodePush Explained - Agile Soft Labs](https://www.agilesoftlabs.com/blog/2026/02/react-native-codepush-explained-instant_01310605320) — Recent but CodePush is retiring, alternatives not yet battle-tested
- [Hot Updater - GitHub](https://github.com/gronxb/hot-updater) — Self-hosted OTA alternative, relatively new project (2024), limited production usage data

**MinIO CDN:**
- [Building a Scalable Image CDN with MinIO, imgproxy, and Cloudflare - Medium](https://medium.com/@lorenzo_33729/building-a-scalable-image-cdn-with-minio-imgproxy-and-cloudflare-4694ad4b93df) — Community architecture example, not official MinIO documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - GitHub Actions, Sentry, Fastlane, and pytest are mature, well-documented, and widely adopted for React Native and FastAPI production deployments.
- Architecture patterns: HIGH - Patterns sourced from official documentation (GitHub Actions, Sentry, Fastlane) and verified production implementations.
- Pitfalls: HIGH - Based on common production issues documented in official Apple Developer notices (Privacy Manifest), Sentry troubleshooting guides (Hermes source maps), and security research (Flower authentication).
- CDN optimization: MEDIUM - CloudFront + MinIO is architecturally sound but community-documented; official MinIO docs focus on direct S3 compatibility, not CDN integration specifics.
- OTA updates: LOW - CodePush retiring creates uncertainty; alternatives (hot-updater, react-native-ota-hot-update) are newer and lack extensive production validation.

**Research date:** 2026-02-10
**Valid until:** 2026-03-10 (30 days — stable domain with mature tools; some areas like OTA updates evolving rapidly)
