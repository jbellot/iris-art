---
phase: 07-polish-and-production-readiness
plan: 01
subsystem: ci-cd-monitoring
tags: [ci, testing, monitoring, docker, sentry, github-actions]
dependency_graph:
  requires: []
  provides:
    - backend-ci-pipeline
    - mobile-android-ci-pipeline
    - backend-pytest-suite
    - sentry-error-tracking
    - production-docker-image
    - health-check-endpoints
  affects:
    - backend/tests/
    - backend/Dockerfile
    - backend/app/main.py
    - backend/app/api/routes/health.py
    - .github/workflows/
    - mobile/index.js
tech_stack:
  added:
    - pytest
    - pytest-asyncio
    - pytest-cov
    - sentry-sdk[fastapi]
    - @sentry/react-native
    - GitHub Actions
  patterns:
    - async-test-fixtures
    - multi-stage-docker-build
    - non-root-container-user
    - health-probes-k8s
    - ci-with-service-containers
key_files:
  created:
    - backend/tests/__init__.py
    - backend/tests/conftest.py
    - backend/tests/test_health.py
    - backend/tests/test_auth.py
    - backend/pytest.ini
    - .github/workflows/backend-ci.yml
    - .github/workflows/mobile-android.yml
    - mobile/sentry.properties
  modified:
    - backend/requirements.txt
    - backend/Dockerfile
    - backend/.dockerignore
    - backend/app/main.py
    - backend/app/core/config.py
    - backend/app/api/routes/health.py
    - mobile/index.js
    - mobile/package.json
decisions:
  - Backend CI runs pytest with PostgreSQL and Redis services, builds Docker image on main push
  - Multi-stage Dockerfile reduces image size and runs as non-root user for security
  - Sentry enabled only when SENTRY_DSN is set (production-only, not dev)
  - Health endpoints follow Kubernetes patterns: /health/liveness (simple) and /health/readiness (checks DB + Redis + MinIO)
  - Mobile Sentry wrapped with Sentry.wrap(App) for automatic React component error capture
  - Coverage threshold set at 30% for initial smoke tests (can be increased as tests grow)
metrics:
  duration_seconds: 278
  tasks_completed: 2
  files_created: 8
  files_modified: 8
  commits: 2
  completed_at: 2026-02-10T13:51:48Z
---

# Phase 07 Plan 01: CI/CD, Testing, and Production Monitoring

**One-liner:** Established CI/CD pipelines with pytest smoke tests, Sentry error monitoring for backend and mobile, multi-stage Docker build with non-root user, and Kubernetes-ready health probes.

## Objective

Set up automated quality gates (CI tests), production error visibility (Sentry), and optimized deployment pipeline to support continuous delivery and fast debugging.

## Execution Summary

Executed both tasks successfully with no deviations. Plan executed exactly as written.

**Task 1:** Backend testing infrastructure, Sentry monitoring, multi-stage Dockerfile, and health improvements
- Created pytest suite with async fixtures for FastAPI testing
- Added smoke tests for health and auth endpoints
- Integrated Sentry SDK for FastAPI and Celery (conditional init)
- Converted Dockerfile to multi-stage build with non-root user (app:1000)
- Added /health/liveness and /health/readiness endpoints for container orchestration
- Updated .dockerignore to exclude tests and dev artifacts

**Task 2:** GitHub Actions CI workflows and Sentry mobile integration
- Created backend-ci.yml workflow with pytest, coverage checks, and Docker build/push to GHCR
- Created mobile-android.yml workflow with TypeScript check, Jest, and APK build with Gradle caching
- Integrated Sentry React Native SDK in mobile entry point with production-only enablement
- Added sentry.properties for source map uploads (auth token via CI env)

## Deviations from Plan

None - plan executed exactly as written.

## Technical Implementation

### Backend Testing Infrastructure

Created pytest suite with async test fixtures in `conftest.py`:
- Session-scoped `test_engine` creates/drops test database tables
- Function-scoped `test_session` provides isolated transactions with rollback
- Function-scoped `client` overrides FastAPI dependency for async HTTP testing

Smoke tests cover:
- Health endpoints: liveness, readiness, db check
- Auth endpoints: registration, duplicate email, login success/failure

### Sentry Integration

**Backend (FastAPI + Celery):**
- Conditional initialization in `main.py` before app creation
- Only enabled when `SENTRY_DSN` is set (production-only)
- 10% traces sample rate
- PII scrubbing disabled by default

**Mobile (React Native + Hermes):**
- Initialization in `index.js` before AppRegistry
- Enabled only in production builds (`!__DEV__`)
- Wrapped App component with `Sentry.wrap()` for automatic error capture
- Cookie scrubbing in `beforeSend` hook

### Docker Optimization

Multi-stage build reduces image size:
- Stage 1 (builder): Installs dependencies to `/install` prefix
- Stage 2 (runtime): Copies installed deps, runs as non-root user (app:1000)
- `.dockerignore` excludes tests, cache, .env files

### Health Endpoints for Kubernetes

**Liveness probe** (`/health/liveness`):
- Simple alive check, no dependencies
- Used by orchestrators to restart unhealthy containers

**Readiness probe** (`/health/readiness`):
- Checks DB (SELECT 1), Redis (ping), MinIO (head_bucket)
- Returns 503 if any service is unavailable
- Used by load balancers to route traffic only to ready instances

### CI/CD Pipelines

**Backend CI:**
- Triggers on push/PR to `backend/**` paths
- Runs pytest with PostgreSQL and Redis service containers
- Checks 30% code coverage threshold
- Builds Docker image and pushes to GHCR on main branch
- Uses GitHub Actions cache for pip and Docker layers

**Mobile Android CI:**
- Triggers on push/PR to `mobile/**` paths
- Runs TypeScript check and Jest tests
- Builds release APK with Gradle caching (speeds up 30min build)
- Uploads APK artifact with 30-day retention

## Key Files

**Backend:**
- `backend/tests/conftest.py` - Async test fixtures with DB override
- `backend/tests/test_health.py` - Health endpoint smoke tests
- `backend/tests/test_auth.py` - Auth endpoint smoke tests
- `backend/app/main.py` - Sentry initialization before app
- `backend/app/api/routes/health.py` - Added liveness and readiness endpoints
- `backend/Dockerfile` - Multi-stage build with non-root user

**CI/CD:**
- `.github/workflows/backend-ci.yml` - Backend CI pipeline
- `.github/workflows/mobile-android.yml` - Android build pipeline

**Mobile:**
- `mobile/index.js` - Sentry initialization with Sentry.wrap(App)
- `mobile/sentry.properties` - Sentry CLI config for source maps

## Testing & Verification

All verification steps passed:
- ✓ Test files exist (conftest, test_health, test_auth)
- ✓ CI workflows are valid YAML
- ✓ Sentry backend integration in main.py
- ✓ Sentry mobile integration in index.js
- ✓ Multi-stage Dockerfile with AS builder
- ✓ Non-root user (useradd) in Dockerfile
- ✓ /health/readiness endpoint exists
- ✓ /health/liveness endpoint exists

## Success Criteria

- [x] Backend pytest suite discovers and runs smoke tests (health + auth endpoints)
- [x] GitHub Actions workflows for backend CI and Android build are syntactically valid
- [x] Sentry is integrated in both backend (FastAPI + Celery) and mobile (React Native)
- [x] Backend Docker image uses multi-stage build with non-root user
- [x] Health endpoints include /health/liveness and /health/readiness for container orchestration

## Next Steps

**For Plan 02 (Phase 7):**
- Set up actual Sentry projects and configure DSN environment variables
- Configure Android keystore secrets for release signing in CI
- Add integration tests beyond smoke tests (user flows, payment flows)
- Set up staging environment with actual MinIO/S3 for readiness checks
- Consider adding iOS CI workflow

**Future Improvements:**
- Increase coverage threshold as test suite grows (target 80%+)
- Add performance monitoring (Sentry transactions for slow endpoints)
- Set up automated security scanning (Dependabot, Snyk)
- Add E2E tests with Detox for mobile

## Self-Check: PASSED

Verified all created files exist:
- ✓ backend/tests/__init__.py
- ✓ backend/tests/conftest.py
- ✓ backend/tests/test_health.py
- ✓ backend/tests/test_auth.py
- ✓ backend/pytest.ini
- ✓ .github/workflows/backend-ci.yml
- ✓ .github/workflows/mobile-android.yml
- ✓ mobile/sentry.properties

Verified all commits exist:
- ✓ 77a7714: feat(07-01): add backend testing, Sentry monitoring, multi-stage Docker, and health improvements
- ✓ 24ecd4a: feat(07-01): add GitHub Actions CI workflows and Sentry mobile integration
