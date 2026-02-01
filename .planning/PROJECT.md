# IrisVue

## What This Is

IrisVue is a cross-platform mobile app that democratizes iris art photography. Users capture a photo of their iris (or a loved one's) using real-time AI-guided camera controls, then transform it into artistic renderings — from curated preset styles to AI-generated unique compositions. Named circles let couples, families, and friends collect and combine their irises into shared galleries and fusion artwork. Freemium model with premium styles and HD export at 4.99EUR.

## Core Value

Any user can capture a beautiful iris photo with their phone and turn it into personalized art — an experience that currently costs 400EUR+ at specialized galleries.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] User can register and log in (email/password, Apple Sign In, Google Sign In)
- [ ] User can capture an iris photo using guided real-time camera overlay with auto-detection
- [ ] AI extracts the iris from the photo, removes light reflections, and enhances quality
- [ ] User can generate artistic renderings using curated preset styles (free basic + paid premium)
- [ ] User can generate AI-unique artistic compositions inspired by their iris patterns and colors
- [ ] User can blend two or more irises into a single fused artistic composition
- [ ] User can compose two or more irises side-by-side in a combined artwork
- [ ] User can create named circles (couple, family, friends) and invite members via link
- [ ] Circle members can view a shared gallery of all members' iris art
- [ ] User can export/download HD versions of their art (paid feature at 4.99EUR)

### Out of Scope

- Print shop / e-commerce for physical products (canvas, plexiglass, jewelry) — deferred to v2, requires fulfillment partnerships
- B2B licensing for opticians/jewelers — deferred to post-launch, needs proven product first
- Full social network features (activity feeds, profiles, notifications) — v1 focuses on shared galleries within circles
- Phone number / OTP authentication — email + social login sufficient for v1
- Video capture of iris — still photography only for v1
- Real-time chat between circle members — out of scope, sharing is async through galleries

## Context

- Iris photography is currently a luxury niche: specialized galleries in Paris/NYC charge 400EUR+ per session using professional macro equipment
- The technical challenge is getting a sharp macro iris photo from a phone camera not designed for it — the guided capture with real-time AI feedback is the critical differentiator
- The viral loop is built into the product: inviting someone to scan their iris drives organic growth (low CAC)
- Key emotional use cases: couples combining irises, parents capturing children's irises, unique personalized gifts for birthdays/weddings/births
- The AI pipeline must handle: iris segmentation, reflection removal, quality enhancement/upscaling, and artistic style transfer/generation
- Market context: personalized art market is growing, driven by demand for authentic, unique gifts

## Constraints

- **Tech stack (backend)**: Python + FastAPI — chosen for direct access to ML/AI ecosystem (PyTorch, OpenCV, diffusion models)
- **Database**: PostgreSQL — structured data for users, circles, galleries; extensible with pgvector for future similarity features
- **Platform**: Cross-platform mobile (iOS + Android simultaneously) — framework TBD by research (React Native or Flutter)
- **AI processing**: Server-side — phone sends captured photo to backend, AI processes on server, returns results
- **App Store compliance**: Apple Sign In required when offering social login options on iOS

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Cloud-based AI processing (not on-device) | Heavy AI models (segmentation, style transfer, generation) need GPU compute; phone hardware too variable | — Pending |
| Python + FastAPI backend | Native access to ML ecosystem, async performance, clean API design | — Pending |
| PostgreSQL database | Structured data needs, extensibility (pgvector), reliability | — Pending |
| Freemium: free basic styles, paid premium + HD export | Lower barrier to entry, monetize on value (art quality), 4.99EUR price point | — Pending |
| Shared galleries (not full social network) for v1 | Focused social layer that drives viral invites without social network complexity | — Pending |
| Real-time guided capture (not burst+select or wizard) | Best UX for the hardest technical challenge; live feedback helps users who aren't photographers | — Pending |

---
*Last updated: 2026-02-01 after initialization*
