# IrisVue

## What This Is

IrisVue is a cross-platform mobile app that democratizes iris art photography. Users capture a photo of their iris (or a loved one's) using real-time AI-guided camera controls, then transform it into artistic renderings — from curated preset styles to AI-generated unique compositions. Named circles let couples, families, and friends collect and combine their irises into shared galleries and fusion artwork. Freemium model with premium styles and HD export at 4.99 EUR.

## Core Value

Any user can capture a beautiful iris photo with their phone and turn it into personalized art — an experience that currently costs 400 EUR+ at specialized galleries.

## Requirements

### Validated

- ✓ User can register and log in (email/password, Apple Sign In, Google Sign In) — v1.0
- ✓ User can capture an iris photo using guided real-time camera overlay with auto-detection — v1.0
- ✓ AI extracts the iris from the photo, removes light reflections, and enhances quality — v1.0
- ✓ User can generate artistic renderings using curated preset styles (free basic + paid premium) — v1.0
- ✓ User can generate AI-unique artistic compositions inspired by their iris patterns and colors — v1.0
- ✓ User can blend two or more irises into a single fused artistic composition — v1.0
- ✓ User can compose two or more irises side-by-side in a combined artwork — v1.0
- ✓ User can create named circles (couple, family, friends) and invite members via link — v1.0
- ✓ Circle members can view a shared gallery of all members' iris art — v1.0
- ✓ User can export/download HD versions of their art (paid feature at 4.99 EUR) — v1.0
- ✓ User can save artwork to device camera roll from all result screens — v1.0
- ✓ Full GDPR/BIPA/CCPA biometric consent with jurisdiction-aware flows and audit trail — v1.0
- ✓ Freemium monetization with RevenueCat, rate limiting (3 free/month), premium style gating — v1.0
- ✓ CI/CD pipeline, Sentry monitoring, production Docker setup with Traefik — v1.0

### Active

(None yet — define in next milestone)

### Out of Scope

- Print shop / e-commerce for physical products (canvas, plexiglass, jewelry) — deferred to v2, requires fulfillment partnerships
- B2B licensing for opticians/jewelers — deferred to post-launch, needs proven product first
- Full social network features (activity feeds, profiles, notifications) — v1 focuses on shared galleries within circles
- Phone number / OTP authentication — email + social login sufficient
- Video capture of iris — still photography only
- Real-time chat between circle members — sharing is async through galleries
- AI avatar generation — crowded market, dilutes iris art focus
- Offline AI processing — heavy models require GPU, server-side only
- Multi-language support — English only for now, defer localization

## Context

Shipped v1.0 MVP with 352 files across 8 phases in 10 days.
Tech stack: FastAPI + PostgreSQL + Redis + Celery + MinIO (backend), React Native 0.83 + Vision Camera (mobile).
~13,100 LOC TypeScript, ~237,700 LOC Python (includes generated/vendor).
AI pipeline uses dev-mode fallbacks (OpenCV) — production needs real model weights (segmentation, NST, SDXL Turbo, Real-ESRGAN).
RevenueCat API keys and Sentry DSN are placeholder — need production values.
Test coverage at 30% (7 smoke tests) — needs expansion.
PRIV-03 (Privacy Manifest) and PRIV-06 (camera permission strings) need device/App Store validation.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Cloud-based AI processing (not on-device) | Heavy AI models need GPU compute; phone hardware too variable | ✓ Good |
| Python + FastAPI backend | Native access to ML ecosystem, async performance, clean API design | ✓ Good |
| PostgreSQL database | Structured data needs, extensibility (pgvector), reliability | ✓ Good |
| React Native + Vision Camera for mobile | Cross-platform with native camera access; research HIGH confidence | ✓ Good |
| Freemium: free basic styles, paid premium + HD export | Lower barrier to entry, monetize on value, 4.99 EUR price point | ✓ Good |
| Shared galleries (not full social network) for v1 | Focused social layer that drives viral invites without social network complexity | ✓ Good |
| Real-time guided capture (not burst+select or wizard) | Best UX for the hardest technical challenge; live feedback helps non-photographers | ✓ Good |
| Privacy/biometric compliance in Phase 1 | Cannot be retrofitted; legal prerequisite for iris capture | ✓ Good |
| Vertical build order (full-stack per feature) | Validates end-to-end early; avoids integration surprises | ✓ Good |
| SQLAlchemy 2.0 async with expire_on_commit=False | Prevents lazy load errors in async context | ✓ Good |
| JWT HS256 symmetric with Redis refresh token hashing | Simple for single backend, secure refresh token management | ✓ Good |
| Presigned URLs for direct S3 upload | Avoids streaming through backend, better performance | ✓ Good |
| Dev-mode AI fallbacks (OpenCV) | Enables full development without GPU; production upgradeable | ✓ Good |
| WebSocket for real-time progress | Better UX than polling; reused across processing, styles, fusion | ✓ Good |
| RevenueCat for payment management | Cross-platform IAP handling, webhook-driven, receipt validation | ✓ Good |
| Traefik v3.0 for production reverse proxy | Automatic Let's Encrypt, Docker-native routing | ✓ Good |

## Constraints

- **Tech stack (backend)**: Python + FastAPI — chosen for direct access to ML/AI ecosystem (PyTorch, OpenCV, diffusion models)
- **Database**: PostgreSQL — structured data for users, circles, galleries; extensible with pgvector for future similarity features
- **Platform**: React Native 0.83 (bare workflow) for iOS + Android
- **AI processing**: Server-side — phone sends captured photo to backend, AI processes on server, returns results
- **App Store compliance**: Apple Sign In required when offering social login options on iOS

---
*Last updated: 2026-02-10 after v1.0 milestone*
