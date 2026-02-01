# Requirements: IrisVue

**Defined:** 2026-02-01
**Core Value:** Any user can capture a beautiful iris photo with their phone and turn it into personalized art

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Authentication & Accounts

- [ ] **AUTH-01**: User can sign up with email and password
- [ ] **AUTH-02**: User can sign in with Apple Sign In (required for iOS App Store)
- [ ] **AUTH-03**: User can sign in with Google Sign In
- [ ] **AUTH-04**: User receives email verification after signup
- [ ] **AUTH-05**: User can reset password via email link
- [ ] **AUTH-06**: User session persists across app restarts (refresh token)
- [ ] **AUTH-07**: User can delete their account and all associated data (GDPR right to erasure)

### Privacy & Compliance

- [ ] **PRIV-01**: App displays biometric data consent screen before first iris capture with explicit opt-in
- [ ] **PRIV-02**: App stores iris images encrypted at rest (S3 server-side encryption)
- [ ] **PRIV-03**: App includes comprehensive Privacy Manifest for iOS submission
- [ ] **PRIV-04**: User can request and download all their personal data (GDPR data portability)
- [ ] **PRIV-05**: App adapts consent flows based on user jurisdiction (GDPR/BIPA/CCPA)
- [ ] **PRIV-06**: Camera permission strings clearly state purpose ("IrisVue captures close-up photos of your iris to create personalized art")

### Camera Capture

- [ ] **CAPT-01**: User can capture an iris photo using the phone camera with basic controls
- [ ] **CAPT-02**: App provides real-time AI-guided overlay showing iris alignment, focus quality, and lighting feedback
- [ ] **CAPT-03**: App uses multi-frame burst capture with automatic best-frame selection
- [ ] **CAPT-04**: Captured photos are uploaded to cloud storage with progress indicator
- [ ] **CAPT-05**: App works reliably on iPhone 12+ and Android devices with camera quality >= 12MP
- [ ] **CAPT-06**: User can view a gallery of their captured iris photos

### AI Processing Pipeline

- [ ] **AIPL-01**: AI extracts the iris from the captured photo (segmentation) with >95% accuracy
- [ ] **AIPL-02**: AI removes light reflections from the extracted iris
- [ ] **AIPL-03**: AI enhances iris quality (color correction, detail enhancement, upscaling via Real-ESRGAN)
- [ ] **AIPL-04**: Processing jobs run asynchronously via Celery workers with WebSocket progress updates
- [ ] **AIPL-05**: User sees real-time progress indicator during AI processing
- [ ] **AIPL-06**: Failed jobs display meaningful error messages and can be retried

### Artistic Styles & Rendering

- [ ] **STYL-01**: User can apply 5-10 curated free preset styles to their iris art
- [ ] **STYL-02**: User can apply 10-15 premium preset styles (paid feature)
- [ ] **STYL-03**: User can generate AI-unique artistic compositions from their iris patterns and colors
- [ ] **STYL-04**: User sees low-resolution preview instantly, then progressive enhancement to HD
- [ ] **STYL-05**: User can export/download HD version of their art (paid feature at 4.99 EUR)
- [ ] **STYL-06**: Free exports include watermark at standard definition; paid exports are HD without watermark

### Social Features (Circles & Fusion)

- [ ] **SOCL-01**: User can create a named circle (couple, family, friends)
- [ ] **SOCL-02**: User can invite members to a circle via shareable link
- [ ] **SOCL-03**: Circle members can view a shared gallery of all members' iris art
- [ ] **SOCL-04**: User can blend two or more irises into a single fused artistic composition
- [ ] **SOCL-05**: User can compose two or more irises side-by-side in a combined artwork
- [ ] **SOCL-06**: Circle members must consent before their iris art is used in fusion/compositions
- [ ] **SOCL-07**: User can leave a circle and remove their content from the shared gallery

### Payments & Monetization

- [ ] **PAYS-01**: App integrates RevenueCat for cross-platform in-app purchase management
- [ ] **PAYS-02**: User can purchase HD export per-image at 4.99 EUR
- [ ] **PAYS-03**: Premium styles are gated behind purchase (per-export or style pack)
- [ ] **PAYS-04**: Free users are rate-limited to 3 AI-processed images per month
- [ ] **PAYS-05**: Receipt validation happens server-side to prevent fraud

### Infrastructure

- [ ] **INFR-01**: Backend API runs on FastAPI with async SQLAlchemy 2.0 and PostgreSQL
- [ ] **INFR-02**: AI processing runs on Celery workers with Redis as message broker
- [ ] **INFR-03**: Images stored in S3 with CDN delivery (Cloudinary or CloudFront)
- [ ] **INFR-04**: Docker Compose configuration for local development
- [ ] **INFR-05**: CI/CD pipeline via GitHub Actions (build, test, deploy)
- [ ] **INFR-06**: Error tracking and monitoring in production (Sentry)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Print Shop & E-Commerce

- **PRNT-01**: User can order prints of their iris art (canvas, plexiglass, metal)
- **PRNT-02**: User can customize print size and material
- **PRNT-03**: Fulfillment via third-party partner integration

### B2B Features

- **B2B-01**: Opticians/jewelers can license iris art for products
- **B2B-02**: White-label portal for B2B partners
- **B2B-03**: Bulk processing API for professional photographers

### Advanced Social

- **ADV-01**: Public gallery / discovery feed for shared artworks
- **ADV-02**: Activity notifications within circles
- **ADV-03**: Multi-language support (French, German, Spanish)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Video capture of iris | Exponentially more complex; still photography sufficient for v1 |
| Real-time chat between circle members | Async sharing via galleries is sufficient; chat adds moderation burden |
| Phone number / OTP authentication | Email + social login covers v1 needs |
| Full social network (feeds, profiles, notifications) | Massive complexity; circles provide focused social layer |
| AI avatar generation | Crowded market (Lensa), dilutes iris art focus |
| Comprehensive photo editor | Feature bloat; iris-specific editing only |
| Offline AI processing | Heavy models require GPU; server-side only for v1 |
| Multi-language support | English only for v1; defer localization to v2 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Pending |
| AUTH-02 | Phase 1 | Pending |
| AUTH-03 | Phase 1 | Pending |
| AUTH-04 | Phase 1 | Pending |
| AUTH-05 | Phase 1 | Pending |
| AUTH-06 | Phase 1 | Pending |
| AUTH-07 | Phase 1 | Pending |
| PRIV-01 | Phase 1 | Pending |
| PRIV-02 | Phase 1 | Pending |
| PRIV-03 | Phase 1 | Pending |
| PRIV-04 | Phase 1 | Pending |
| PRIV-05 | Phase 1 | Pending |
| PRIV-06 | Phase 1 | Pending |
| CAPT-01 | Phase 2 | Pending |
| CAPT-02 | Phase 4 | Pending |
| CAPT-03 | Phase 4 | Pending |
| CAPT-04 | Phase 2 | Pending |
| CAPT-05 | Phase 2 | Pending |
| CAPT-06 | Phase 2 | Pending |
| AIPL-01 | Phase 3 | Pending |
| AIPL-02 | Phase 3 | Pending |
| AIPL-03 | Phase 3 | Pending |
| AIPL-04 | Phase 3 | Pending |
| AIPL-05 | Phase 3 | Pending |
| AIPL-06 | Phase 3 | Pending |
| STYL-01 | Phase 4 | Pending |
| STYL-02 | Phase 4 | Pending |
| STYL-03 | Phase 4 | Pending |
| STYL-04 | Phase 4 | Pending |
| STYL-05 | Phase 4 | Pending |
| STYL-06 | Phase 4 | Pending |
| SOCL-01 | Phase 5 | Pending |
| SOCL-02 | Phase 5 | Pending |
| SOCL-03 | Phase 5 | Pending |
| SOCL-04 | Phase 5 | Pending |
| SOCL-05 | Phase 5 | Pending |
| SOCL-06 | Phase 5 | Pending |
| SOCL-07 | Phase 5 | Pending |
| PAYS-01 | Phase 6 | Pending |
| PAYS-02 | Phase 6 | Pending |
| PAYS-03 | Phase 6 | Pending |
| PAYS-04 | Phase 6 | Pending |
| PAYS-05 | Phase 6 | Pending |
| INFR-01 | Phase 1 | Pending |
| INFR-02 | Phase 1 | Pending |
| INFR-03 | Phase 1 | Pending |
| INFR-04 | Phase 1 | Pending |
| INFR-05 | Phase 7 | Pending |
| INFR-06 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 47 total
- Mapped to phases: 47
- Unmapped: 0

---
*Requirements defined: 2026-02-01*
*Last updated: 2026-02-01 after research synthesis*
