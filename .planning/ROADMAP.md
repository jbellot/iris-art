# Roadmap: IrisVue

## Overview

IrisVue delivers a complete iris art photography experience across 7 phases, building vertically from foundational infrastructure and privacy compliance through the capture-to-art pipeline, social features, and monetization. The critical path runs through auth and privacy (Phase 1), camera capture (Phase 2), and AI processing (Phase 3) -- everything else builds on these. Privacy and async architecture are foundational because they cannot be retrofitted, and biometric compliance is a legal prerequisite for any iris capture.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation and Privacy Architecture** - Auth, database, storage, privacy consent, async infrastructure, dev environment ✅
- [x] **Phase 2: Camera Capture and Image Upload** - React Native app, Vision Camera, upload pipeline, basic gallery ✅
- [x] **Phase 3: AI Processing Pipeline** - Iris segmentation, reflection removal, enhancement, async job processing with progress ✅
- [x] **Phase 4: Camera Guidance and Artistic Styles** - AI-guided capture overlay, preset and AI-generated styles, HD export ✅
- [ ] **Phase 5: Social Features (Circles and Fusion)** - Named circles, invitations, shared galleries, iris fusion and composition
- [ ] **Phase 6: Payments and Freemium** - RevenueCat, in-app purchases, feature gating, rate limiting
- [ ] **Phase 7: Polish and Production Readiness** - CI/CD, monitoring, CDN optimization, App Store submission readiness

## Phase Details

### Phase 1: Foundation and Privacy Architecture
**Goal**: Users can create accounts, authenticate securely, and the app handles biometric iris data with full legal compliance -- all on a properly scaffolded async backend
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06, AUTH-07, PRIV-01, PRIV-02, PRIV-03, PRIV-04, PRIV-05, PRIV-06, INFR-01, INFR-02, INFR-03, INFR-04
**Success Criteria** (what must be TRUE):
  1. User can sign up with email/password and sign in with Apple or Google, and their session persists across app restarts
  2. User receives email verification after signup and can reset a forgotten password via email link
  3. User can delete their account and all associated data is removed (GDPR erasure)
  4. App displays biometric consent screen with explicit opt-in before any iris capture, adapting consent flows based on user jurisdiction (GDPR/BIPA/CCPA)
  5. Docker Compose starts the full local dev stack (FastAPI, PostgreSQL, Redis, Celery worker, S3-compatible storage) with a single command
**Plans**: 3 plans (3/3 complete) ✅

Plans:
- [x] 01-01-PLAN.md -- Backend scaffolding: FastAPI, PostgreSQL, SQLAlchemy 2.0 async, Docker Compose, S3 storage, Celery/Redis
- [x] 01-02-PLAN.md -- Authentication: email/password signup, Apple/Google Sign In, JWT tokens, email verification, password reset, session persistence
- [x] 01-03-PLAN.md -- Privacy and compliance: jurisdiction-aware consent flows, biometric consent with audit trail, data export, account deletion with full erasure

### Phase 2: Camera Capture and Image Upload
**Goal**: Users can open the mobile app, capture an iris photo with basic camera controls, upload it to the cloud, and browse their photo gallery
**Depends on**: Phase 1
**Requirements**: CAPT-01, CAPT-04, CAPT-05, CAPT-06
**Success Criteria** (what must be TRUE):
  1. User can open the app on iPhone 12+ or a 12MP+ Android device and capture an iris photo using basic camera controls
  2. Captured photo uploads to cloud storage with a visible progress indicator
  3. User can view a gallery of all their previously captured iris photos
  4. Camera permission dialog clearly states the purpose of iris capture
**Plans**: 3 plans (3/3 complete) ✅

Plans:
- [x] 02-01-PLAN.md -- App scaffold and backend photo API: React Native project setup, navigation, auth integration, onboarding flow, backend Photo model and upload/gallery endpoints
- [x] 02-02-PLAN.md -- Camera capture and upload pipeline: Vision Camera viewfinder with iris guide overlay, camera controls, photo review screen, S3 upload with progress and retry
- [x] 02-03-PLAN.md -- Gallery and device testing: masonry gallery with FlashList, upload progress on thumbnails, photo detail with zoom, device validation on iOS and Android

### Phase 3: AI Processing Pipeline
**Goal**: The app can take a captured iris photo and automatically extract the iris, remove reflections, and enhance quality -- delivering visible results back to the user with real-time progress
**Depends on**: Phase 2
**Requirements**: AIPL-01, AIPL-02, AIPL-03, AIPL-04, AIPL-05, AIPL-06
**Success Criteria** (what must be TRUE):
  1. User submits a captured iris photo and receives a cleanly segmented iris with reflections removed and quality enhanced
  2. User sees real-time progress updates during AI processing (not a static spinner)
  3. If processing fails, user sees a meaningful error message and can retry the job
  4. Processing runs asynchronously -- the user can navigate the app while waiting for results
**Plans**: 3 plans (3/3 complete) ✅

Plans:
- [x] 03-01-PLAN.md -- Backend AI pipeline and processing API: ProcessingJob model, AI model infrastructure (segmentation, reflection removal, enhancement), Celery pipeline tasks with priority queues, processing REST API
- [x] 03-02-PLAN.md -- WebSocket progress and reliability: Real-time WebSocket progress streaming with magical step names, granular error classification, retry handlers, partial cleanup on failure
- [x] 03-03-PLAN.md -- Mobile processing UX and results: Processing service, WebSocket hook, gallery processing badges, before/after slider result screen, save/share/reprocess actions, batch processing

### Phase 4: Camera Guidance and Artistic Styles
**Goal**: Users get real-time AI feedback while capturing (alignment, focus, lighting) and can transform their processed iris into art using curated presets, AI-generated compositions, and HD export
**Depends on**: Phase 3 (needs working AI pipeline); camera guidance can begin in parallel with late Phase 3
**Requirements**: CAPT-02, CAPT-03, STYL-01, STYL-02, STYL-03, STYL-04, STYL-05, STYL-06
**Success Criteria** (what must be TRUE):
  1. User sees real-time overlay showing iris alignment, focus quality, and lighting feedback while capturing
  2. App uses multi-frame burst capture and automatically selects the best frame
  3. User can apply free preset styles (5-10) and preview premium styles (10-15) on their iris art
  4. User can generate an AI-unique artistic composition from their iris patterns
  5. User sees a low-res preview instantly, then progressive enhancement to HD; free exports include watermark, paid exports are HD without watermark
**Plans**: 3 plans (3/3 complete) ✅

Plans:
- [x] 04-01-PLAN.md -- Camera guidance: Native frame processor plugins (Apple Vision + ML Kit) for iris detection, blur/lighting analysis, real-time overlay UI, burst capture with best-frame selection
- [x] 04-02-PLAN.md -- Preset artistic styles: StylePreset/StyleJob models, Fast NST with ONNX (dev-mode OpenCV fallback), Celery tasks, style API, mobile style gallery and preview with progressive loading
- [x] 04-03-PLAN.md -- AI-generated styles and HD export: SDXL Turbo generator with ControlNet, AI art Celery task, HD export pipeline with Real-ESRGAN upscale, server-side watermark, mobile generation and export screens

### Phase 5: Social Features (Circles and Fusion)
**Goal**: Users can create named circles, invite others, share iris art in group galleries, and combine irises into fusion artwork -- with consent controls throughout
**Depends on**: Phase 3 (needs processed artworks); Phase 4 (styles make shared galleries meaningful)
**Requirements**: SOCL-01, SOCL-02, SOCL-03, SOCL-04, SOCL-05, SOCL-06, SOCL-07
**Success Criteria** (what must be TRUE):
  1. User can create a named circle (couple, family, friends) and invite members via a shareable link
  2. Circle members can view a shared gallery containing all members' iris art
  3. User can blend two or more irises into a fused composition, and compose irises side-by-side in combined artwork
  4. Circle members must give explicit consent before their iris art is used in fusion or compositions
  5. User can leave a circle and their content is removed from the shared gallery
**Plans**: 3 plans

Plans:
- [ ] 05-01-PLAN.md -- Circles CRUD and invitations: Circle/CircleMembership models, invite token system (itsdangerous), circle management API, mobile circle screens with deep link navigation
- [ ] 05-02-PLAN.md -- Shared galleries and consent: ArtworkConsent model, shared gallery API, consent request/grant/deny/revoke flow, mobile gallery with owner badges and consent modal
- [ ] 05-03-PLAN.md -- Iris fusion and composition: FusionArtwork model, Poisson blending Celery task with alpha fallback, side-by-side composition (hconcat/vconcat), consent gate, mobile builder and result screens

### Phase 6: Payments and Freemium
**Goal**: The app monetizes through gated premium features -- users can purchase HD exports, unlock premium styles, and free users are rate-limited
**Depends on**: Phase 4 (premium styles and HD export must exist to sell); Phase 5 (fusion is a premium driver)
**Requirements**: PAYS-01, PAYS-02, PAYS-03, PAYS-04, PAYS-05
**Success Criteria** (what must be TRUE):
  1. User can purchase an HD export of their art at 4.99 EUR through in-app purchase (iOS and Android)
  2. Premium styles are locked behind purchase and unlock after payment
  3. Free users are rate-limited to 3 AI-processed images per month with clear messaging when limit is reached
  4. All purchase receipts are validated server-side to prevent fraud
**Plans**: TBD

Plans:
- [ ] 06-01: RevenueCat integration -- SDK setup, product configuration, cross-platform IAP, server-side receipt validation
- [ ] 06-02: Feature gating and payment UI -- premium style locks, HD export purchase flow, rate limiting for free users, upsell touchpoints

### Phase 7: Polish and Production Readiness
**Goal**: The app is production-ready with CI/CD, monitoring, optimized delivery, and is prepared for App Store and Play Store submission
**Depends on**: Phase 6 (all features integrated)
**Requirements**: INFR-05, INFR-06
**Success Criteria** (what must be TRUE):
  1. CI/CD pipeline automatically builds, tests, and deploys on push to main
  2. Production errors are captured in Sentry with actionable context and alerting
  3. Images load fast via CDN (Cloudinary or CloudFront) across regions
  4. App passes App Store and Play Store review guidelines (Privacy Manifest, permissions, content policies)
**Plans**: TBD

Plans:
- [ ] 07-01: CI/CD and monitoring -- GitHub Actions pipeline, Sentry integration, health checks, alerting
- [ ] 07-02: CDN optimization and store submission -- Cloudinary/CloudFront setup, image delivery optimization, App Store and Play Store submission prep

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation and Privacy Architecture | 3/3 | Complete ✅ | 2026-02-01 |
| 2. Camera Capture and Image Upload | 3/3 | Complete | 2026-02-01 |
| 3. AI Processing Pipeline | 3/3 | Complete ✅ | 2026-02-09 |
| 4. Camera Guidance and Artistic Styles | 3/3 | Complete ✅ | 2026-02-09 |
| 5. Social Features (Circles and Fusion) | 0/3 | Not started | - |
| 6. Payments and Freemium | 0/2 | Not started | - |
| 7. Polish and Production Readiness | 0/2 | Not started | - |

---
*Roadmap created: 2026-02-01*
*Last updated: 2026-02-09 (Phase 4 complete)*
