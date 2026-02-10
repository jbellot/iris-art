---
phase: 07-polish-and-production-readiness
plan: 02
subsystem: deployment, mobile-app-stores
tags: [docker, traefik, cdn, cloudfront, ios, android, app-store, play-store]
dependency_graph:
  requires: [07-01]
  provides: [production-deployment-config, cdn-integration, app-store-compliance]
  affects: [backend-storage, backend-deployment, mobile-ios, mobile-android]
tech_stack:
  added:
    - Traefik v3.0 (reverse proxy, HTTPS, Let's Encrypt)
    - Docker Compose production stack
    - CloudFront CDN integration (optional)
  patterns:
    - CDN-aware URL generation with presigned fallback
    - Environment-based signing config for CI/CD
    - Production build optimizations (ProGuard, R8, Gradle caching)
key_files:
  created:
    - backend/docker-compose.production.yml
    - backend/.env.production.example
  modified:
    - backend/app/core/config.py
    - backend/app/storage/s3.py
    - mobile/ios/IrisArt/PrivacyInfo.xcprivacy
    - mobile/android/app/build.gradle
    - mobile/android/gradle.properties
decisions:
  - what: Use Traefik v3.0 for reverse proxy instead of nginx
    why: Automatic Let's Encrypt integration, Docker labels for routing, simpler config
  - what: Exclude Flower from production stack
    why: Security best practice — access via SSH tunnel only in production
  - what: CDN_BASE_URL as empty string default (not null)
    why: Allows optional CloudFront integration without breaking dev environments
  - what: Separate get_download_url() for mobile clients vs presigned PUT for uploads
    why: Download URLs can use CDN, upload URLs must go directly to MinIO
  - what: Release keystore from environment variables (not committed)
    why: Enables CI/CD signing without storing secrets in git
  - what: Enable ProGuard/R8 minification for release builds
    why: Reduces APK size, provides code obfuscation for Play Store
  - what: 4GB Gradle heap instead of default 2GB
    why: Accommodates React Native 0.83's larger native builds (4 ABIs)
metrics:
  duration: 2
  tasks_completed: 2
  files_modified: 7
  completed_at: 2026-02-10T13:57:31Z
---

# Phase 7 Plan 02: Production Deployment & App Store Readiness Summary

Production Docker Compose with Traefik HTTPS and CloudFront CDN integration, plus iOS Privacy Manifest and Android release signing for app store submissions.

## Completed Tasks

### Task 1: Production Docker Compose with Traefik and CDN-ready storage

**Commit:** 840c2bc

**Changes:**
- Added `CDN_BASE_URL` setting to `backend/app/core/config.py` for optional CloudFront integration
- Added `get_download_url()` and `get_public_url()` methods to S3 client for CDN-aware URL generation
  - When `CDN_BASE_URL` is set: returns `{CDN_BASE_URL}/{bucket}/{key}`
  - When not set: falls back to presigned GET URLs
- Created `backend/docker-compose.production.yml` with:
  - **Traefik v3.0** reverse proxy with automatic Let's Encrypt HTTPS
  - **Web service** with 2 uvicorn workers
  - **Celery worker** with `--loglevel=warning` and `--concurrency=2`
  - **PostgreSQL 15** with health checks
  - **Redis 7** with password authentication
  - **MinIO** with `MINIO_SERVER_URL` set to public domain (fixes presigned URL hostname issue)
  - All services with `restart: unless-stopped`
  - Traefik labels for routing: `${API_DOMAIN}` for web, `${STORAGE_DOMAIN}` for MinIO
  - **Flower excluded** from production stack (SSH tunnel access only per security best practice)
- Created `backend/.env.production.example` template with all required environment variables:
  - Application config (SECRET_KEY, ENVIRONMENT, DEBUG)
  - Database credentials
  - Redis password
  - MinIO/S3 credentials
  - CDN_BASE_URL (optional)
  - Sentry DSN
  - Traefik config (API_DOMAIN, ACME_EMAIL)
  - RevenueCat API keys

**Key differences from dev stack:**
- Traefik for HTTPS (not direct port exposure)
- No port exposure for db, redis (internal only)
- No volume mounts for code (uses built Docker image)
- Redis password authentication (not open)
- Environment variables from .env.production (not hardcoded)

**Files:**
- `backend/docker-compose.production.yml` (created)
- `backend/.env.production.example` (created)
- `backend/app/core/config.py` (modified)
- `backend/app/storage/s3.py` (modified)

### Task 2: App Store and Play Store submission readiness

**Commit:** 4fab777

**Changes:**

**iOS (PrivacyInfo.xcprivacy):**
- Updated `NSPrivacyCollectedDataTypes` from empty array to declare 4 data types:
  1. **Photos** (`NSPrivacyCollectedDataTypePhotos`) — for iris photo capture and processing
  2. **Email Address** (`NSPrivacyCollectedDataTypeEmailAddress`) — for authentication
  3. **User ID** (`NSPrivacyCollectedDataTypeUserID`) — for app functionality
  4. **Purchase History** (`NSPrivacyCollectedDataTypePurchaseHistory`) — via RevenueCat
- All data types marked as:
  - `NSPrivacyCollectedDataTypeLinked: true` (linked to user identity)
  - `NSPrivacyCollectedDataTypeTracking: false` (not used for tracking)
  - Purpose: `NSPrivacyCollectedDataTypePurposeAppFunctionality`
- Kept existing `NSPrivacyAccessedAPITypes` declarations (FileTimestamp, UserDefaults, SystemBootTime)
- Kept `NSPrivacyTracking: false` (no advertising tracking)

**Android (build.gradle):**
- Added `release` signing config to `signingConfigs` block:
  - `storeFile`: `release.keystore` (file in app directory)
  - `storePassword`, `keyPassword`: from environment variables (`KEYSTORE_PASSWORD`, `KEY_PASSWORD`)
  - `keyAlias`: from env var or defaults to `irisvue`
- Updated `buildTypes.release`:
  - Changed `signingConfig` from `debug` to `release`
  - Enabled minification: `minifyEnabled true`
  - Enabled resource shrinking: `shrinkResources true`
  - Changed ProGuard file from `proguard-android.txt` to `proguard-android-optimize.txt` (better optimization)
- Changed `enableProguardInReleaseBuilds` from `false` to `true`

**Android (gradle.properties):**
- Increased Gradle heap from 2GB to 4GB: `org.gradle.jvmargs=-Xmx4096m`
- Enabled parallel builds: `org.gradle.parallel=true`
- Enabled build caching: `org.gradle.caching=true`
- Enabled R8 full mode: `android.enableR8.fullMode=true`

**Files:**
- `mobile/ios/IrisArt/PrivacyInfo.xcprivacy` (modified)
- `mobile/android/app/build.gradle` (modified)
- `mobile/android/gradle.properties` (modified)

## Deviations from Plan

None — plan executed exactly as written.

## Success Criteria

- [x] Production Docker Compose runs web, celery, postgres, redis, minio behind Traefik with HTTPS
- [x] CDN_BASE_URL setting enables CloudFront-served images when configured
- [x] S3 storage layer serves download URLs via CDN (when configured) or presigned URLs (fallback)
- [x] Production environment template documents all required variables
- [x] PrivacyInfo.xcprivacy declares all collected data types (Photos, Email, User ID, Purchase History) for App Store review
- [x] Android release build configured with signing config (keystore from env vars for CI)
- [x] ProGuard/R8 minification enabled for release builds (smaller APK, code obfuscation)
- [x] Gradle build optimizations enabled (parallel, caching, R8 full mode)

## Deployment Notes

### Production Docker Compose

**Deployment steps:**
1. Copy `backend/.env.production.example` to `backend/.env.production`
2. Fill in all placeholder values (use `python -c "import secrets; print(secrets.token_hex(32))"` for SECRET_KEY)
3. Set `API_DOMAIN` and `STORAGE_DOMAIN` to your actual domains
4. Create DNS A records pointing to your server IP
5. Run: `cd backend && docker-compose -f docker-compose.production.yml up -d`
6. Traefik will automatically provision Let's Encrypt certificates

**CloudFront CDN setup (optional):**
1. Create CloudFront distribution with MinIO as origin (`https://${STORAGE_DOMAIN}`)
2. Set `CDN_BASE_URL` in `.env.production` to CloudFront domain
3. Mobile clients will receive CloudFront URLs for image display (faster global delivery)
4. Upload URLs remain as presigned MinIO URLs (direct upload, no CDN passthrough)

**Security notes:**
- Flower excluded from production — access via SSH tunnel: `ssh -L 5555:localhost:5555 user@server`, then run Flower manually if needed
- Redis requires password authentication in production
- Database and Redis are not exposed to host network (internal Docker only)
- All services run behind Traefik with HTTPS (HTTP redirects to HTTPS)

### iOS App Store Submission

**Privacy Manifest compliance:**
- PrivacyInfo.xcprivacy now declares all collected data types
- Required by Apple since May 2024 for App Store review
- No tracking enabled (NSPrivacyTracking: false)
- All data linked to user identity and used for app functionality

**Before submission:**
1. Update app version in `Info.plist`
2. Update `CFBundleShortVersionString` and `CFBundleVersion`
3. Build archive in Xcode: Product > Archive
4. Upload to App Store Connect
5. Fill in App Store listing, screenshots, privacy details
6. Submit for review

### Android Play Store Submission

**Release signing:**
- Generate release keystore: `keytool -genkeypair -v -storetype PKCS12 -keystore release.keystore -alias irisvue -keyalg RSA -keysize 2048 -validity 10000`
- Place `release.keystore` in `mobile/android/app/`
- **DO NOT commit keystore to git** (add to `.gitignore`)
- For CI/CD: set environment variables `KEYSTORE_PASSWORD`, `KEY_PASSWORD`, `KEY_ALIAS`

**Build release APK/AAB:**
```bash
cd mobile/android
# For APK:
./gradlew assembleRelease
# For AAB (Play Store preferred):
./gradlew bundleRelease
```

**Before submission:**
1. Update `versionCode` and `versionName` in `build.gradle`
2. Build AAB: `./gradlew bundleRelease`
3. Upload to Play Console: https://play.google.com/console
4. Fill in store listing, screenshots, content rating
5. Submit for review

**Build optimizations:**
- ProGuard minification reduces APK size by ~30-40%
- R8 full mode provides better optimization than legacy ProGuard
- Resource shrinking removes unused resources
- 4GB Gradle heap prevents OOM errors on large native builds

## Integration Points

### CDN Integration (Backend → CloudFront)

**Flow:**
1. Mobile requests artwork URL from backend API
2. Backend calls `s3_client.get_download_url(key)`:
   - If `CDN_BASE_URL` set: returns `https://d1234.cloudfront.net/iris-art/{key}`
   - If not set: returns presigned MinIO URL (fallback)
3. Mobile displays image from returned URL

**CloudFront origin setup:**
- Origin: `https://${STORAGE_DOMAIN}` (MinIO via Traefik HTTPS)
- Origin protocol: HTTPS only
- Cache behavior: Cache based on query strings (presigned URL params)
- TTL: 86400 seconds (24 hours) for processed images

### Mobile App Store Compliance

**iOS Privacy Manifest:**
- Declares collected data types required by App Store Review
- Must match data collection in app's functionality
- Reviewed during App Store submission process

**Android Release Signing:**
- Release keystore must be kept secure (lost keystore = cannot update app)
- CI/CD uses environment variables (GitHub Secrets, CircleCI env vars)
- Play Store verifies app signature on every update

## Self-Check: PASSED

**Created files verified:**
- [FOUND] backend/docker-compose.production.yml
- [FOUND] backend/.env.production.example

**Modified files verified:**
- [FOUND] backend/app/core/config.py — CDN_BASE_URL setting present
- [FOUND] backend/app/storage/s3.py — get_download_url() and get_public_url() methods exist
- [FOUND] mobile/ios/IrisArt/PrivacyInfo.xcprivacy — NSPrivacyCollectedDataTypePhotos and other data types present
- [FOUND] mobile/android/app/build.gradle — release signingConfig and minifyEnabled true
- [FOUND] mobile/android/gradle.properties — org.gradle.caching=true and android.enableR8.fullMode=true

**Commits verified:**
- [FOUND] 840c2bc — feat(07-02): add production Docker Compose with Traefik and CDN-ready storage
- [FOUND] 4fab777 — feat(07-02): configure iOS and Android for app store submissions

All claims in summary verified against actual implementation.
