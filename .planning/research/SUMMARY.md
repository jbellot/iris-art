# Project Research Summary

**Project:** IrisVue
**Domain:** AI-powered mobile iris photography and art generation
**Researched:** 2026-02-01
**Confidence:** HIGH

## Executive Summary

IrisVue is a cross-platform mobile app that democratizes iris art photography by replacing expensive professional studio sessions ($30-100+) with an AI-guided smartphone experience. The research reveals a clear blue ocean opportunity: no existing product combines AI-guided mobile iris capture, automated extraction and enhancement, artistic style transfer, and private collaborative galleries (named circles). The recommended stack -- React Native with Vision Camera for the mobile client, FastAPI/PostgreSQL/Celery/Redis for the backend, and PyTorch with ONNX Runtime for the AI pipeline -- is well-established and HIGH confidence across all four researchers. The architecture follows a proven async job processing pattern: lightweight on-device ML (MediaPipe) for real-time camera guidance, with heavy AI processing (segmentation, style transfer, upscaling) offloaded to GPU-backed Celery workers via Redis queues.

The most significant risk to the project is not technical but regulatory and experiential. Iris images are legally classified as biometric identifiers under BIPA, GDPR, and CCPA/CPRA. Failure to implement proper consent flows and data handling from day one exposes the project to catastrophic legal liability ($47.5M-$100M settlements precedent under BIPA alone) and near-certain App Store rejection (12% rejection rate for Privacy Manifest violations in Q1 2025). The second existential risk is camera UX: if users cannot successfully capture a usable iris photo on their first or second attempt, they will abandon the app immediately. Professional photographers report that macro iris photography is challenging even with dedicated equipment. The AI guidance system and multi-frame burst capture with automatic best-frame selection are not nice-to-haves -- they are survival features.

The recommended approach is to build vertically through the critical path (auth, upload, async AI pipeline) before expanding horizontally to social features and payments. Privacy compliance, cost controls, and async processing architecture must be foundational -- they cannot be retrofitted. The freemium model (free basic styles with watermark, 4.99 EUR per HD export) is competitive and viable, but conversion rate optimization should be treated as an ongoing experiment, not a one-time implementation. All four research areas converge on a clear recommendation: invest heavily in the capture-to-art pipeline quality, gate costs aggressively for free users, and treat biometric privacy as a first-class architectural concern.

## Key Findings

### Recommended Stack

The stack centers on React Native (not Flutter) for cross-platform mobile, driven by the critical need for advanced camera control. React Native Vision Camera provides Frame Processors for real-time AI guidance at 30+ FPS with GPU acceleration -- a capability Flutter's camera ecosystem cannot match. The backend is Python/FastAPI (project constraint) with async SQLAlchemy 2.0 over PostgreSQL via asyncpg, and Celery with Redis for background AI processing. The AI pipeline uses PyTorch for model development with ONNX Runtime for 2-3x inference speedup in production. GCP (Cloud Run + Compute Engine with GPU) is recommended over AWS for simpler serverless deployment and better ML tooling.

**Core technologies:**
- **React Native + Vision Camera 4.7.x**: Cross-platform mobile with real-time frame processing for AI camera guidance
- **FastAPI 0.115.x + SQLAlchemy 2.0 (async)**: Async-first API with Pydantic validation, PostgreSQL 16 via asyncpg
- **Celery 5.4.x + Redis 7.x**: Distributed task queue for long-running AI processing with priority-based routing
- **PyTorch 2.x + ONNX Runtime 1.20.x**: Deep learning framework with optimized inference for segmentation, style transfer, upscaling
- **U-Net/DeepLabV3+**: Iris segmentation (98.9%+ IoU on iris datasets, HIGH confidence)
- **Real-ESRGAN**: 4x image upscaling (industry standard, HIGH confidence)
- **Fast Neural Style Transfer + Stable Diffusion 3.5**: Preset styles (<1s) and AI-generated unique styles (10-30s)
- **MediaPipe**: On-device face/iris detection for real-time camera guidance at 30+ FPS
- **Firebase Auth + RevenueCat**: Authentication (Apple + Google Sign In) and cross-platform IAP management
- **S3 + Cloudinary**: Hybrid storage (raw images in S3, CDN delivery via Cloudinary)
- **GCP Cloud Run + Compute Engine (GPU)**: Serverless API hosting with dedicated GPU workers for AI inference

**Critical version requirements:** Python 3.11.x (not 3.12 for ML stability), Node.js 20.x LTS, PostgreSQL 16.x, Pydantic 2.x (breaking changes from v1).

### Expected Features

**Must have (table stakes):**
- Email/password + Apple/Google Sign In authentication
- Camera capture interface with basic controls
- Photo gallery with cloud persistence
- 5-10 preset artistic styles (free tier)
- Standard definition export (with watermark for free tier)
- Basic sharing to social media
- Image preview before export

**Should have (differentiators -- all V1):**
- Real-time AI-guided iris capture (core differentiator, eliminates need for professional equipment)
- AI iris extraction and enhancement (automated reflection removal)
- Named circles for private group galleries (couples, families, friends)
- Iris fusion art (blend two irises into one artwork)
- AI-generated unique styles (one-of-a-kind compositions, premium)
- HD/4K export without watermark (premium, 4.99 EUR)
- 10-15 premium artistic styles
- Progressive quality preview (low-res instant, HD on commit)

**Defer (v2+):**
- Print shop integration (complex fulfillment logistics)
- B2B portal (different product, different go-to-market)
- Video capture mode (exponentially more complex)
- Public gallery/discovery feed (moderation nightmare)
- Multi-language support (start English only)
- AI avatar generation (crowded market, dilutes focus)

### Architecture Approach

The architecture follows a four-layer pattern: Mobile Client (React Native with on-device ML) communicating via REST + WebSocket to an API Gateway (FastAPI, async), which dispatches long-running work to a Background Processing Layer (Celery workers with priority queues on Redis), all backed by a Data Layer (PostgreSQL for metadata, S3 for binary images, Redis for cache/state). The key architectural insight is the hybrid on-device/server processing split: lightweight MediaPipe runs on-device at <30ms for real-time camera guidance, while heavy models (segmentation 5-15s, style transfer 10-30s, upscaling 5-15s) run server-side on GPU workers. Progress is streamed to the mobile client via WebSocket, not HTTP polling.

**Major components:**
1. **Mobile Client (React Native)** -- Camera capture with AI guidance overlay, gallery UI, circles UI, local caching via Zustand + React Query
2. **API Gateway (FastAPI on Cloud Run)** -- Auth, image upload/download, job orchestration, social endpoints, payment endpoints; auto-scales 0-100 instances
3. **Background Workers (Celery on GCE with GPU)** -- Priority-based queues (high: segmentation, normal: style transfer, low: batch/analytics); models loaded once at worker startup via ModelCache pattern
4. **Data Layer** -- PostgreSQL (users, metadata, circles, jobs), S3 (original + processed images), Redis (message broker, result backend, API cache), Cloudinary (CDN delivery)

### Critical Pitfalls

All four researchers flagged these as the highest-risk items:

1. **Biometric privacy compliance failure (CRITICAL)** -- Iris images are legally biometric identifiers. Must implement explicit consent flows, geo-based compliance (GDPR/BIPA/CCPA), encryption at rest, user deletion on demand, and DPIAs BEFORE any iris capture. Non-negotiable for Phase 1. Recovery cost if missed: catastrophic ($50M+ settlements precedent).

2. **App Store rejection for biometric data handling (CRITICAL)** -- 12% rejection rate for Privacy Manifest violations. Must include specific camera permission strings ("IrisVue captures close-up photos of your iris to create personalized art"), comprehensive Privacy Manifest, and in-app privacy controls. Test with TestFlight early. Recovery cost: 2-4 week delay minimum.

3. **Macro photography UX failure (CRITICAL)** -- Users cannot capture usable iris photos without guidance. Must build multi-frame burst capture with auto best-frame selection, real-time alignment/focus/lighting indicators, progressive onboarding. Target: >70% capture success rate in testing with 20+ diverse users. This is the make-or-break feature.

4. **AI processing costs spiral (CRITICAL)** -- Freemium model means 95-98% of users pay nothing but consume AI resources. Must implement strict rate limiting for free users (3 processed images/month), gate expensive features behind paywall, use hybrid self-hosted/API model hosting, and monitor per-user costs. Budget 30-60% higher than initial projections.

5. **Cross-platform camera API issues (HIGH)** -- React Native Vision Camera has known issues (Android crashes, black screen, orientation bugs). Must test on 10+ device models including mid-range Android. Budget 20-30% extra dev time for camera work. Use feature detection and graceful degradation.

## Implications for Roadmap

Based on combined research, the following phase structure reflects the critical path dependencies, architectural constraints, and pitfall avoidance strategies identified across all four research areas.

### Phase 1: Foundation and Privacy Architecture
**Rationale:** Privacy compliance and async processing architecture cannot be retrofitted. All researchers agree these must be foundational. The ARCHITECTURE.md build order and PITFALLS.md both place this first.
**Delivers:** Working API with auth, database schema, S3 storage, privacy consent framework, Celery/Redis infrastructure, Docker Compose dev environment.
**Addresses:** Authentication (table stakes), account data persistence, biometric consent flows.
**Avoids:** Pitfall 1 (biometric privacy), Pitfall 2 (App Store rejection), Pitfall 4 (cost controls built in from start), Pitfall 10 (hybrid storage architecture), Pitfall 11 (async processing from day 1).

### Phase 2: Camera Capture and Image Upload
**Rationale:** The capture-to-upload pipeline is the prerequisite for all AI features. Camera UX is the highest-risk user-facing feature and needs early prototyping and testing.
**Delivers:** React Native app scaffold, Vision Camera integration, image compression and upload with progress, basic gallery view, guided capture prototype.
**Addresses:** Camera capture interface, photo gallery, AI-guided capture (prototype).
**Avoids:** Pitfall 3 (macro photography UX -- start testing early), Pitfall 5 (cross-platform camera issues -- test on device matrix), Pitfall 14 (onboarding friction -- validate capture flow).

### Phase 3: AI Processing Pipeline (Core)
**Rationale:** This is the critical path. The entire product value depends on iris segmentation, extraction, and enhancement working reliably. The async job processing pattern (Celery + WebSocket progress) established here is reused by all subsequent AI features.
**Delivers:** End-to-end flow from capture to AI result. Iris segmentation (U-Net), reflection removal, basic enhancement. WebSocket progress tracking. Job status management.
**Addresses:** AI iris extraction and enhancement (differentiator), basic image editing/enhancement (table stakes).
**Avoids:** Pitfall 8 (AI pipeline failures -- build validation and fallbacks from start), Pitfall 11 (FastAPI bottlenecks -- all AI work in Celery).

### Phase 4: Camera Guidance and Artistic Styles
**Rationale:** Can run in parallel with Phase 3 completion. Camera guidance improves capture success rate (addressing Pitfall 3). Artistic styles are the primary engagement driver and monetization enabler.
**Delivers:** MediaPipe on-device iris detection, real-time guidance overlay (distance, focus, lighting), 5-10 free preset styles via Fast NST, 10-15 premium styles, AI-generated unique style via Stable Diffusion, HD export pipeline, progressive quality preview.
**Addresses:** Real-time AI-guided capture (core differentiator), preset styles (table stakes), premium styles (monetization), HD export (monetization), AI-generated unique style (differentiator).
**Avoids:** Pitfall 6 (image quality -- use quality tiers: fast preview vs. HD export), Pitfall 9 (battery drain -- optimize MediaPipe usage, add battery saver mode).

### Phase 5: Social Features (Named Circles and Fusion)
**Rationale:** Depends on multiple processed images existing (Phases 3-4). Social features are a key differentiator but must not be rushed -- biometric content moderation is complex. Privacy controls must be battle-tested first.
**Delivers:** Circle creation/invitation/management, shared galleries with permissions, iris fusion (Poisson blending for V1), activity within circles.
**Addresses:** Named circles (differentiator), iris fusion (differentiator), basic social sharing.
**Avoids:** Pitfall 12 (social content moderation -- implement reporting, consent for sharing, takedown process).

### Phase 6: Payments and Freemium
**Rationale:** Monetization comes after core value is proven and premium features exist to sell. RevenueCat abstracts iOS/Android IAP complexity. The per-export model (4.99 EUR) aligns with the use case (couples creating 2-4 pieces).
**Delivers:** RevenueCat integration, Stripe web billing (US), feature gating (free vs. premium styles, SD vs. HD export), payment UI, receipt validation.
**Addresses:** Freemium model with clear tiers (table stakes), HD export premium, premium style access.
**Avoids:** Pitfall 7 (conversion rate -- implement strategic gating, contextual upsells, A/B test pricing), Pitfall 13 (payment integration mistakes -- test sandbox thoroughly, server-side receipt validation).

### Phase 7: Polish and Production Readiness
**Rationale:** Optimization and reliability after all features are integrated. CDN setup, load testing, monitoring, and mobile polish.
**Delivers:** Cloudinary CDN integration, Sentry error tracking, PostHog analytics, load testing (1K concurrent users), mobile animations and error handling, offline mode improvements, documentation.
**Addresses:** Performance expectations, production reliability, App Store submission readiness.
**Avoids:** Pitfall 9 (battery optimization), Pitfall 15 (iOS/Android feature parity audit).

### Phase Ordering Rationale

- **Privacy and async architecture first** because all four researchers agree these cannot be retrofitted. PITFALLS.md rates biometric compliance as CRITICAL with "NEVER" acceptable to skip. ARCHITECTURE.md anti-patterns emphasize async processing from day one.
- **Camera before AI** because the processing pipeline depends on having captured images. Early camera testing (Phase 2) surfaces the macro photography UX risk (Pitfall 3) with time to iterate 2-3 cycles.
- **Core AI before styles** because segmentation and enhancement must work reliably before layering artistic transformation on top. The ARCHITECTURE.md dependency graph confirms: capture -> segmentation -> enhancement -> style transfer.
- **Social after AI** because named circles require processed artworks to be meaningful. PITFALLS.md warns explicitly: "Do not rush social features. Privacy must be bulletproof first."
- **Payments after features** because you need premium features to sell. Revenue optimization is an ongoing experiment, not a one-time build.
- **Parallel opportunity:** Phase 4 (camera guidance + styles) can overlap with late Phase 3. Multiple AI tasks in Phase 4 can be built in parallel by different developers.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (AI Processing Pipeline):** Iris segmentation model selection (U-Net vs. DeepLabV3+) needs benchmarking on actual iris images. Reflection removal (LapCAT/RABRRN) is MEDIUM confidence -- newer research, may need custom training or traditional CV fallback. Requires prototype and quality evaluation.
- **Phase 4 (Camera Guidance):** MediaPipe integration with React Native via native bridge has MEDIUM confidence -- less documentation than web, feasible but may need custom native module. Stable Diffusion 3.5 integration complexity is MEDIUM confidence.
- **Phase 5 (Social Features):** Biometric content moderation for shared iris images is novel territory. No established pattern for moderating biometric art. Needs legal review and moderation strategy research.
- **Phase 6 (Payments):** RevenueCat Web Billing is a new feature (2024-2025) with US-only availability and lower conversion rates than native IAP. Needs validation.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** FastAPI + PostgreSQL + Redis + Docker is extremely well-documented. Firebase Auth with Apple/Google Sign In is standard. HIGH confidence.
- **Phase 2 (Camera and Upload):** React Native Vision Camera has extensive documentation and 350K+ weekly downloads. Image upload to S3 is a solved problem. HIGH confidence.
- **Phase 7 (Polish):** CDN setup, monitoring, load testing are standard DevOps patterns. HIGH confidence.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Core technologies (React Native, FastAPI, PostgreSQL, PyTorch) are industry-proven. Camera library choice backed by 350K+ weekly downloads. All sources are official docs and 2025-2026 comparisons. |
| Features | HIGH | Competitive analysis covers iris photography services and AI art apps. Feature prioritization aligns with market data. Freemium pricing benchmarked against competitors. |
| Architecture | HIGH | Async job processing with Celery is a well-documented pattern for ML workloads. Build order follows clear dependency chain. API design follows REST best practices. Verified with official FastAPI/Celery docs. |
| Pitfalls | HIGH | 15 pitfalls identified (7 critical/high), all backed by 2025-2026 sources. Legal research on biometric privacy includes actual settlement amounts and rejection statistics. Recovery strategies documented for each. |

**Overall confidence:** HIGH

The research is thorough, internally consistent, and well-sourced. All four researchers converge on the same core recommendations. The main uncertainty is not in the technology choices but in the AI model quality for iris-specific use cases (segmentation, reflection removal, style transfer quality) -- these need prototyping and benchmarking against real user-generated content.

### Gaps to Address

- **Iris segmentation model benchmarking:** U-Net vs. DeepLabV3+ on actual iris images captured by smartphone (not lab datasets). Need to validate 98%+ accuracy holds for mobile-captured images with varying quality.
- **Reflection removal quality:** LapCAT/RABRRN are from recent research (2025) with limited production usage. May need to start with traditional CV approach and upgrade. Need prototype to evaluate.
- **MediaPipe on React Native:** Feasible but less documented than web. Native bridge integration may have performance implications. Need a proof-of-concept spike.
- **Stable Diffusion 3.5 hosting costs:** Self-hosting requires GPU instances ($0.50-$2/hour). Hugging Face Inference API pricing depends on volume. Need cost modeling at 10K, 50K, 100K images/month.
- **Capture success rate on diverse devices:** All camera UX assumptions need validation with 20+ real users across iPhone, high-end Android, and mid-range Android devices. This is the highest-risk unknown.
- **Freemium conversion rate:** The 2-5% industry benchmark may not apply to a niche creative app with per-export pricing. Need real usage data to optimize.
- **GDPR/BIPA legal review:** Research identifies the requirements but a formal legal review of the consent flow and data architecture is needed before launch.

## Cross-Researcher Consensus

All four research areas converge on these points:

1. **React Native over Flutter** for camera control (STACK confirms ecosystem, ARCHITECTURE builds on Vision Camera, PITFALLS flags cross-platform camera as risk to manage).
2. **Async processing is non-negotiable** (STACK recommends Celery, ARCHITECTURE patterns center on it, PITFALLS lists sync processing as "never acceptable").
3. **Privacy must be foundational** (PITFALLS rates it CRITICAL, ARCHITECTURE places it in Phase 1, FEATURES notes Apple Sign In requirement and biometric nature of data).
4. **Camera UX is the make-or-break feature** (FEATURES identifies AI-guided capture as core differentiator, ARCHITECTURE dedicates a phase to it, PITFALLS rates macro photography failure as CRITICAL).
5. **Hybrid AI hosting** (STACK recommends self-hosted for fast models + API for Stable Diffusion, ARCHITECTURE scales workers independently, PITFALLS warns about cost spirals).
6. **Build vertically, not horizontally** (ARCHITECTURE recommends full-stack per feature, FEATURES defines clear dependency chain, PITFALLS warns against rushing social features).

## Sources

### Primary (HIGH confidence)
- [FastAPI Official Documentation](https://fastapi.tiangolo.com/) -- API framework, deployment, async patterns
- [React Native Vision Camera](https://react-native-vision-camera.com/) -- Camera library, Frame Processors, performance
- [SQLAlchemy 2.0 Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) -- ORM patterns, async session management
- [PyTorch Official Documentation](https://pytorch.org/docs/stable/index.html) -- Deep learning framework
- [ONNX Runtime Documentation](https://onnxruntime.ai/docs/) -- Inference optimization
- [Apple Developer Privacy Guidelines](https://developer.apple.com/app-store/app-privacy-details/) -- App Store requirements
- [FastAPI Cloud Run Quickstart (Jan 2026)](https://docs.cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-fastapi-service) -- Deployment guide

### Secondary (MEDIUM confidence)
- [Deep Learning for Iris Recognition Survey (ACM 2025)](https://dl.acm.org/doi/10.1145/3651306) -- Segmentation model accuracy benchmarks
- [Neural Style Transfer Research (Nature 2025)](https://www.nature.com/articles/s41598-025-95819-9) -- NST quality evaluation
- [High-Resolution Reflection Removal (Nature 2025)](https://www.nature.com/articles/s41598-025-94464-6) -- LapCAT transformer approach
- [Flutter vs React Native 2026](https://limeup.io/blog/flutter-vs-react-native/) -- Framework comparison
- [Privacy Laws 2026: Global Updates](https://secureprivacy.ai/blog/privacy-laws-2026) -- Regulatory landscape
- [Illinois BIPA Litigation Tracker](https://www.stopspying.org/bipa-litigation-tracker) -- Settlement precedents
- [App Store Conversion Rate by Category 2026](https://adapty.io/blog/app-store-conversion-rate/) -- Freemium benchmarks

### Tertiary (needs validation)
- MediaPipe integration with React Native via native bridge -- feasible but needs proof-of-concept
- Stable Diffusion 3.5 self-hosting cost at scale -- needs cost modeling with actual workloads
- RevenueCat Web Billing conversion rates -- new feature, limited data available
- Capture success rate on mid-range Android -- assumption-based, needs real user testing

---
*Research completed: 2026-02-01*
*Ready for roadmap: yes*
