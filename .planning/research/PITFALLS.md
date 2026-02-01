# Pitfalls Research: IrisVue

**Domain:** AI-powered iris photography mobile app
**Researched:** 2026-02-01
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Biometric Data Privacy Compliance Failure

**Severity:** CRITICAL

**What goes wrong:**
Apps collecting iris images without proper biometric privacy compliance face catastrophic legal and financial consequences. Illinois' BIPA law alone has generated settlements ranging from $47.5M to $100M for companies like Google Photos and TikTok. Recent 2025-2026 data shows at least 100+ new BIPA class actions filed annually, with 12% of App Store submissions rejected for Privacy Manifest violations in Q1 2025.

**Why it happens:**
Developers treat iris photos as "just images" rather than sensitive biometric identifiers. They underestimate multi-jurisdictional requirements (GDPR, CCPA/CPRA, BIPA, state-specific laws) and fail to implement proper consent flows before launch. The regulatory landscape changed significantly in 2026 with expanded definitions covering "biometric-derived data" and new DPIA requirements for sensitive data processing.

**How to avoid:**
- Implement explicit, separate consent for biometric data collection BEFORE capturing any iris images
- Never store raw iris images unless absolutely necessary; use derived artistic outputs instead
- Conduct Data Protection Impact Assessments (DPIAs) during architecture phase
- Implement geo-detection to apply appropriate consent standards (GDPR for EU, BIPA for Illinois, etc.)
- Use encryption and access controls for any stored biometric data
- Allow user deletion of ALL biometric data on demand (not just soft-delete)
- Document data retention policies and automated deletion schedules
- Consider storing only processed art outputs, not source iris images

**Warning signs:**
- User flows that capture iris images before showing consent dialogs
- Database schemas storing raw iris images without encryption or TTL
- No geographic-based consent variation in the app
- Privacy policy that doesn't specifically mention "biometric identifiers" or "iris patterns"
- No automated data deletion mechanism
- Sharing iris data with third-party AI services without explicit user permission

**Phase to address:**
Phase 1 (Architecture & Privacy Foundation) - This MUST be in the initial architecture. Retrofitting privacy compliance is expensive and risky. GDPR fines can reach €20M or 4% of global revenue; BIPA provides statutory damages of $1,000-$5,000 per violation.

---

### Pitfall 2: App Store Rejection for Biometric Data Handling

**Severity:** CRITICAL

**What goes wrong:**
Apple rejected 12% of App Store submissions in Q1 2025 for Privacy Manifest violations, with biometric data handling being a primary concern. Apps face rejection or removal for: unclear camera permission descriptions, missing Privacy Manifest declarations, insufficient explanation of biometric data usage, and third-party AI data sharing without disclosure. The review process can take weeks, delaying launches and updates.

**Why it happens:**
Developers copy generic permission strings ("This app needs camera access to take photos") instead of specific explanations. They fail to disclose where iris data will be processed (on-device vs. cloud) and which third-party services receive biometric data. Apple's 2025-2026 guidelines specifically require apps to "clearly disclose where personal data will be shared with third parties, including with third-party AI, and obtain explicit permission before doing so."

**How to avoid:**
- Write specific camera permission strings: "IrisVue captures close-up photos of your iris to create personalized art. Your iris images are processed securely and can be deleted anytime."
- Create comprehensive Privacy Manifest declaring all data collection, including biometric identifiers
- Document exactly where iris data is processed (on-device, your servers, third-party AI APIs)
- Implement App Tracking Transparency (ATT) if any tracking occurs
- Show in-app privacy summaries before first data collection
- Test App Store review process early with TestFlight build
- Prepare detailed Review Notes explaining biometric data flow and privacy controls

**Warning signs:**
- Generic "needs camera access" permission strings
- No Privacy Manifest file in the Xcode project
- Iris images sent to third-party APIs without user disclosure
- Missing data retention explanations in privacy policy
- No in-app privacy controls for users to view/delete their data

**Phase to address:**
Phase 1 (Architecture) for technical implementation; Phase 2 (MVP) for review submission testing. This cannot be added retroactively without significant rework.

---

### Pitfall 3: Macro Photography UX Failure

**Severity:** CRITICAL

**What goes wrong:**
Users cannot successfully capture usable iris photos, leading to immediate app abandonment. Iris macro photography requires 2-inch working distance, near-perfect focus on a moving target (eyes have involuntary saccadic movement), razor-thin depth of field (< 1cm), and steady hands. Professional photographers report "focus is killing us" even with dedicated macro equipment and focus rails. Mobile users lack this equipment and expertise. If the capture success rate is below 50%, users will rage-quit during onboarding.

**Why it happens:**
Developers test on their own eyes (static, cooperative subject) or assume phone autofocus "just works." They don't account for: varying phone camera capabilities across Android devices, hand shake at 2-inch distance, eye movement during capture, poor lighting conditions, reflections on iris surface, and user difficulty seeing the screen while holding phone near their own eye.

**How to avoid:**
- Build real-time guidance system with visual feedback (distance indicators, focus quality, brightness checks)
- Implement multi-frame capture with automatic best-frame selection
- Use burst mode and AI to select sharpest frame
- Provide alignment guides (overlays showing ideal iris position)
- Add stabilization time (countdown after positioning)
- Support external lighting recommendations or flash guidance
- Consider capturing 5-10 frames and selecting best one server-side
- Test with 20+ diverse users, including those with glasses, older users, low-end Android phones
- Implement progressive onboarding: first capture is guided like a game tutorial
- Add escape hatches: "Having trouble? Try these tips..." with video examples

**Warning signs:**
- Capture success rate below 70% in user testing
- Users taking 5+ attempts to get acceptable photo
- High drop-off rate (>50%) during first capture
- Complaints about blur, darkness, or "can't focus"
- Support tickets asking "how do I take the photo?"
- No metrics tracking capture attempts vs. successes

**Phase to address:**
Phase 2 (MVP) - This is make-or-break for user onboarding. Prototype and test with real users before full development. Plan 2-3 iteration cycles based on user feedback.

---

### Pitfall 4: AI Processing Costs Spiral Out of Control

**Severity:** CRITICAL

**What goes wrong:**
AI-powered apps routinely underestimate costs by 500-1000% when scaling from pilot to production. Cloud AI processing for iris segmentation, enhancement, and style transfer can cost $1.50 per 1,000 images (Google Cloud Vision baseline), but custom AI models are far more expensive. Style transfer and generation can cost $0.05-$0.50 per image depending on model complexity. With freemium model where most users pay nothing, costs quickly exceed revenue. A app with 10,000 active users processing 5 images each per month = 50,000 images = $25-$2,500/month in AI costs alone, before infrastructure, storage, or CDN costs.

**Why it happens:**
Developers test with small datasets and don't model costs at scale. They fail to differentiate between processing costs for free vs. paid users. They enable all AI features for all users without usage caps. API costs scale linearly with usage but revenue doesn't (only 2-5% convert in freemium models).

**How to avoid:**
- Model costs at 3 scales: 1K users, 10K users, 100K users
- Implement strict rate limiting for free users (e.g., 3 processed images per month)
- Gate expensive features (HD export, advanced styles) behind paywall
- Use hybrid approach: basic processing on-device, advanced processing in cloud
- Implement processing queue with batching to optimize API usage
- Cache common style transfers (if user A and B both want "Van Gogh" style on similar iris, can you reuse?)
- Monitor per-user costs and flag/limit outliers
- Consider model hosting: self-host models vs. API calls for cost optimization at scale
- Budget 30-60% higher than initial projections for TCO over 2 years
- Use serverless architecture and spot instances to reduce baseline costs

**Warning signs:**
- No cost-per-user calculation in financial model
- Same processing limits for free and paid users
- No usage monitoring or alerting on API costs
- Processing all uploads immediately rather than queuing
- No caching strategy for common operations
- Month-over-month cost growth exceeding user growth
- Gross margin below 50% (unsustainable for SaaS/mobile app)

**Phase to address:**
Phase 1 (Architecture) - Cost model must be built into architecture. Rate limiting, queuing, and caching cannot be easily retrofitted. Phase 3+ (Scale) - Revisit with actual usage data and optimize.

---

### Pitfall 5: Cross-Platform Camera API Nightmare

**Severity:** HIGH

**What goes wrong:**
Camera APIs differ dramatically between iOS and Android, and between React Native and Flutter. Flutter can "struggle with features that require deep native integrations like advanced camera processing." React Native "excels at native features like GPS and cameras but relies on third-party libraries creating maintenance challenges." The react-native-vision-camera library (current standard) has reported issues with crashes on Android barcode scanning, black screen bugs, orientation problems, and frame processor instability. About 35% of developers face API inconsistencies in cross-platform development. Users on older Android devices or iOS versions experience different camera capabilities.

**Why it happens:**
Developers test on latest flagship devices (iPhone 15, Pixel 8) and don't test on mid-range Android phones from 2021. They assume camera APIs work the same across platforms. They use deprecated camera libraries or outdated SDK versions. Platform-specific bugs emerge only after production deployment.

**How to avoid:**
- Choose cross-platform framework carefully: Flutter has more consistent UI but weaker native integration; React Native has better native access but more platform-specific code
- Use maintained, actively-updated camera libraries (react-native-vision-camera for RN)
- Build platform-specific codepaths for critical camera features
- Test on device matrix: iPhone (latest, -2 years), high-end Android, mid-range Android, low-end Android
- Implement feature detection: check camera capabilities before using advanced features
- Monitor crash reports by device/OS version to catch platform-specific issues
- Budget 20-30% extra dev time for cross-platform camera work vs. single-platform
- Consider progressive enhancement: basic camera works everywhere, advanced features on supported devices only
- Keep native modules minimal and well-documented for maintenance

**Warning signs:**
- Only testing on iOS or only on flagship Android
- Using deprecated camera libraries (react-native-camera instead of vision-camera)
- No device capability detection code
- Crashes reported on specific Android models (Samsung, Xiaomi variations)
- Black screen issues on certain devices
- Camera orientation bugs on tablets
- Frame rate drops or performance issues on older devices
- Different photo quality/resolution across platforms

**Phase to address:**
Phase 1 (Architecture) - Framework and library choice. Phase 2-3 (MVP & Iteration) - Extensive device testing and platform-specific fixes.

---

### Pitfall 6: Image Quality Falls Short of User Expectations

**Severity:** HIGH

**What goes wrong:**
In 2026, smartphone photography has reached professional levels. Users expect AI-processed images to match or exceed their phone's native quality. 91% of photos are taken on smartphones; 86% of Americans consider camera quality when buying phones; 64% of professional photographers use smartphones for personal photos. When IrisVue's output looks worse than a phone's native camera or like a "generic AI filter," users perceive it as low-quality and abandon the app. Style transfer that looks "generic, flattened, and disconnected from the original" kills retention.

**Why it happens:**
AI models trained on lower-resolution data produce artifacts when processing high-res phone cameras (48MP+). Style transfer models struggle with consistency ("style consistency is one of the biggest challenges with AI image generation"). Developers don't benchmark against user expectations (Instagram filters, professional photo apps like Lightroom Mobile, native AI features in iPhone/Pixel). They optimize for speed over quality. They don't test on actual user-generated content (poorly lit, blurry, suboptimal iris photos).

**How to avoid:**
- Define quality benchmarks: what does "good enough" look like? Compare to competitors and native photo features
- Implement quality gates: AI evaluates output quality before showing to user (re-process if quality score too low)
- Train/fine-tune models on high-resolution iris images, not general image datasets
- Offer quality tiers: fast preview (lower quality) vs. final export (high quality)
- A/B test different AI models and style transfer approaches
- Collect user feedback: "Did this meet your expectations?" after each processing
- Show before/after comparisons prominently so users see the enhancement
- Invest in model fine-tuning for iris-specific features (texture, color, reflection handling)
- Consider multiple models: cheap/fast for previews, expensive/slow for paid HD exports
- Test on "bad" inputs: blurry photos, poor lighting, occluded iris

**Warning signs:**
- Users downloading original photos more than AI-processed versions
- Low social sharing rates (users don't want to share low-quality outputs)
- User reviews mentioning "blurry," "pixelated," "worse than original," "artificial-looking"
- High ratio of processing requests to downloads (users try it, dislike result, don't save)
- No quality metrics tracking (PSNR, SSIM, perceptual quality scores)
- Free tier and paid tier use same quality models (no incentive to upgrade)

**Phase to address:**
Phase 2-3 (MVP & Iteration) - Requires extensive testing with real users and iteration. Phase 4+ (Enhancement) - Continuous model improvement based on user feedback.

---

### Pitfall 7: Freemium Conversion Rate Below Viability Threshold

**Severity:** HIGH

**What goes wrong:**
Freemium conversion rates of 2-5% are "good," 6-8% are "great." If IrisVue achieves only 1-2% conversion, the economics break down: with 10,000 users, 2% conversion = 200 paid users × €4.99 = €998/month revenue, but with AI processing costs, infrastructure, and development, this is unsustainable. The app generates high costs (AI processing, storage, bandwidth) but low revenue. Most users churn before reaching the paywall. Hard paywall apps achieve 12.11% median conversion vs. 2.18% for freemium, but hard paywall limits growth.

**Why it happens:**
Free tier offers too much value (users never need to upgrade) or too little value (users churn before seeing value). Paywall timing is wrong (too early = immediate churn, too late = users already satisfied). Value proposition is unclear ("Why pay €4.99?"). No FOMO or urgency. Generic upsell prompts that users ignore. Not using product usage data to trigger contextual upgrades (e.g., when user creates their 4th artwork and loves it, THEN show upgrade prompt).

**How to avoid:**
- Design free tier strategically: enough to demonstrate value (2-3 basic styles, low-res exports) but create desire for more
- Gate compelling features behind paywall: HD export, premium styles, iris fusion, no watermark, unlimited processing
- Show premium previews: let users see what Van Gogh style would look like (with watermark), then prompt to upgrade
- Personalized onboarding: "What do you want to create?" and show them that their goal requires premium
- Time upsell prompts strategically: after user creates artwork they love (detected by time spent viewing, sharing, etc.)
- Create urgency: "Unlock all styles - 50% off for first 24 hours" during onboarding
- Social proof: "Join 10,000+ users creating stunning iris art"
- Implement usage-based triggers: after 3 free images processed, show "Love your results? Upgrade for unlimited"
- Test pricing: €4.99 vs. €7.99 vs. €2.99 - find optimal price point
- Consider tiered pricing: Basic (€2.99), Pro (€4.99), Artist (€9.99) to capture different segments

**Warning signs:**
- Conversion rate below 2% after 30 days of user cohort
- Users hitting free tier limits and churning instead of converting
- High engagement but low conversion (users love it but won't pay)
- No A/B testing of paywall presentation, pricing, or feature gating
- Same upsell prompt for all users regardless of behavior
- Paid features that users don't value (e.g., HD export when users only share on Instagram at lower res)
- Free tier has no limitations (unlimited processing, all styles free)

**Phase to address:**
Phase 2-3 (MVP & Iteration) - Implement initial freemium model with conservative gating. Phase 4+ (Optimization) - Iterate based on conversion data, A/B test pricing and features.

---

## Moderate Pitfalls

### Pitfall 8: AI Pipeline Failures Degrade User Trust

**What goes wrong:**
Iris segmentation fails on images with glasses, strong reflections, or poor lighting. Reflection removal introduces artifacts. Style transfer produces "bland," "generic," or inconsistent results. Users encounter "processing failed" errors without explanation. Even with identical prompts, results vary wildly between processing runs. The "worst performance occurs when models attempt to imitate naïve art, primarily due to the challenge most models face in handling the 'flat' perspective typical of this style."

**Prevention:**
- Implement multi-stage validation: input quality check → segmentation → reflection removal → enhancement → style transfer, with fallback at each stage
- Pre-process images to improve AI success rate: auto-brightness, contrast adjustment, denoise
- Add "preparing your image..." step that applies enhancements before AI processing
- Train models specifically on iris images with common failure modes (glasses, reflections, low light)
- Provide clear error messages: "We couldn't detect your iris clearly. Try retaking the photo in better lighting."
- Implement graceful degradation: if advanced style fails, fall back to simpler filter
- Show processing confidence to users: "This result is experimental - try different lighting for better results"
- A/B test multiple AI models and select best output
- Monitor AI failure rates by image characteristics to identify patterns

**Phase to address:** Phase 3 (AI Pipeline Refinement)

---

### Pitfall 9: Mobile Performance and Battery Drain

**What goes wrong:**
Real-time camera preview with AI guidance drains battery rapidly. Camera and sensor usage are "particularly power-hungry, with camera preview alone using considerable processing power." Users complain about battery drain within minutes of using app. Starting March 2026, Google Play Store will flag and badge apps that "may drain your phone's battery faster," damaging app reputation and downloads. Battery drain is "one of the biggest complaints users have about mobile apps" and "when apps drain battery excessively, users will delete them quickly."

**Prevention:**
- Minimize camera preview time: capture image quickly, then process offline
- Disable real-time AI processing during capture (too expensive computationally)
- Use efficient camera modes: lower preview resolution, avoid HDR during preview
- Implement smart sensor usage: only run camera when app is in foreground and on capture screen
- Test battery usage across devices before launch
- Add settings: "Battery Saver Mode" reduces camera quality and processing features
- Batch processing: queue captured images and process when phone is charging
- Profile app with Xcode Instruments / Android Profiler to identify battery hotspots
- Monitor battery usage metrics post-launch

**Phase to address:** Phase 3-4 (Optimization)

---

### Pitfall 10: Database Performance Bottlenecks with Image Metadata

**What goes wrong:**
Storing large binary images directly in PostgreSQL degrades performance. "Very large files (100MB+), where performance is critical to the application, the database layer adds a lot of overhead and complexity that may not be required." User galleries load slowly. Database backups become massive and time-consuming. Queries slow down as image table grows.

**Prevention:**
- Use hybrid storage: PostgreSQL for metadata (user_id, created_at, tags, style_type) and external storage (S3, Cloudflare R2) for actual images
- Store image URLs in database, not binary data
- Implement CDN for image delivery (CloudFront, Cloudflare)
- Add database indexes on common query patterns (user_id, created_at)
- Separate tables: user_profiles, iris_captures, processed_artworks, styles
- Use connection pooling for database access
- Implement caching layer (Redis) for frequently accessed metadata
- Compress images before storage (WebP format reduces size 25-35% vs JPEG with same quality)
- Set up automated cleanup: delete unprocessed uploads after 24 hours

**Phase to address:** Phase 1 (Architecture) - Storage strategy must be correct from start

---

### Pitfall 11: FastAPI CPU-Bound Processing Bottlenecks

**What goes wrong:**
FastAPI is excellent for I/O-bound operations but "encounters serious performance challenges" with CPU-bound tasks like image processing due to Python's Global Interpreter Lock (GIL). "Async is not magic - it helps with I/O, not CPU, and if you do heavy computation inside async endpoints, you may make things worse." Server response times spike. Requests queue up. Users see "processing..." for minutes.

**Prevention:**
- Offload CPU-intensive tasks (AI inference, image processing) to separate worker processes using Celery or RQ
- Use asynchronous task queue: user uploads → immediate response → background processing → webhook/notification when complete
- Implement horizontal scaling: multiple workers behind load balancer
- Use GPU-accelerated instances for AI inference (CUDA-enabled servers)
- Consider serverless functions for burst processing (AWS Lambda, Google Cloud Functions)
- Monitor request latency and queue length to detect bottlenecks early
- Use ProcessPoolExecutor for CPU-bound tasks within FastAPI
- Profile endpoints to identify CPU-intensive operations

**Phase to address:** Phase 1 (Architecture) - Background processing architecture required from start

---

### Pitfall 12: Social Features Create Biometric Content Moderation Nightmare

**What goes wrong:**
Users share iris images in galleries and circles. These are biometric identifiers, not just photos. Content moderation for biometric images introduces unique challenges: detecting when users share others' iris photos without consent, identifying if iris images are used for identification/surveillance purposes, moderating AI-generated deepfake iris images, handling GDPR/CCPA deletion requests that span shared content. "Content is now produced at a speed and scale that makes manual moderation impossible." Multimodal content (iris images with captions) requires unified moderation.

**Prevention:**
- Implement AI content moderation from day 1 (AWS Rekognition Content Moderation, Azure Content Safety)
- Require explicit consent before allowing iris artwork to be shared publicly
- Watermark shared images to prevent misuse for identification purposes
- Add reporting mechanism: "This isn't my iris" or "Inappropriate content"
- Auto-blur or pixelate iris detail in public shares (show artistic version only, not raw capture)
- Monitor for biometric data misuse (users trying to build iris databases)
- Consider limiting social features initially (Phase 5+) until privacy controls are battle-tested
- Implement takedown process: if user deletes account, all their shared content must be removed
- Log consent trail: who shared what, when, with whom

**Phase to address:** Phase 5+ (Social Features) - Do not rush social features. Privacy must be bulletproof first.

---

## Minor Pitfalls

### Pitfall 13: Payment Integration Mistakes

**What goes wrong:**
Developers skip sandbox testing of IAP, leading to broken purchases at launch. They fail to handle refunds or failed payments gracefully. They skip receipt validation, making app vulnerable to fraud. They use outdated StoreKit/Play Billing SDKs causing compatibility issues. They violate Apple/Google commission rules by steering users to external payments inappropriately (30% commission applies in most cases).

**Prevention:**
- Test IAP thoroughly in sandbox before launch (both iOS and Android)
- Implement server-side receipt validation (never trust client-side only)
- Handle edge cases: purchase interrupted, receipt expired, refund issued
- Update user access immediately upon successful purchase and upon refund
- Use current SDK versions: StoreKit 2 (iOS), Google Play Billing Library 6+
- For subscription management, consider RevenueCat or Adapty to abstract platform differences
- Understand 2026 payment rules: external payments allowed in some jurisdictions but with restrictions
- Never implement workarounds to avoid platform fees without legal review

**Phase to address:** Phase 2 (MVP) - IAP must work correctly at launch

---

### Pitfall 14: Onboarding Friction Kills Activation

**What goes wrong:**
90% of users churn if they don't understand product value within first week. 77% of daily active users stop using an app within first three days. For iris photography app, if first capture attempt fails or takes too long (>2 minutes), users abandon. Forced account creation before demonstrating value causes immediate drop-off.

**Prevention:**
- Progressive onboarding: capture iris → see AI result → THEN ask for account to save
- Delay friction points: don't require email verification immediately
- Show value fast: within 60 seconds of app open, user should see impressive iris art result
- Use AI to personalize onboarding: "What style interests you?" and show relevant examples
- Provide skip options: "Try it first, create account later"
- Implement adaptive UI: collapse multi-step processes based on user behavior
- Test onboarding with 20+ new users, measure completion rate (target: >60%)
- Add contextual help: "Having trouble? Watch this 15-second guide"

**Phase to address:** Phase 2-3 (MVP & Iteration) - Critical for retention

---

### Pitfall 15: Neglecting iOS vs. Android Feature Parity

**What goes wrong:**
Flutter apps experience "minor issues or delays in updates for iOS apps" because "it was released by Google. Naturally, Android is more compatible with it than the iOS platform." Camera APIs, permissions, and capabilities differ. Features work perfectly on iOS but crash on Android. UI looks native on one platform but foreign on the other.

**Prevention:**
- Test equally on both platforms throughout development
- Budget separate QA time for iOS and Android
- Use platform-specific UI components where necessary (don't force one platform's patterns onto the other)
- Monitor crash reports and performance separately by platform
- Consider platform-specific releases: launch iOS first (single platform), then Android (easier to fix iOS-specific issues before expanding)
- Maintain device testing lab or use cloud testing (Firebase Test Lab, AWS Device Farm)

**Phase to address:** Phase 2-4 (MVP through Polish)

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip DPIA and privacy compliance initially | Launch 2-3 months faster | Legal liability, potential $50M+ settlements, app store rejection | NEVER - Privacy must be day 1 |
| Store iris images directly in PostgreSQL | Simpler architecture | Database performance issues, expensive storage, slow backups | Only for MVP with <1K users, must migrate |
| Use pre-trained generic style transfer models without fine-tuning | No model training cost/time | Poor quality, generic outputs, low differentiation | Acceptable for MVP testing, must improve for launch |
| Single-platform launch (iOS only) | Half the dev/testing effort | Miss 70% of global mobile market, lose Android users | Acceptable for initial validation, plan Android within 3 months |
| Manual content moderation for social features | No AI moderation costs | Doesn't scale, slow response, potential legal issues | Acceptable for private beta with <100 users |
| Hard-code payment flow without abstraction layer | Faster initial implementation | Difficult to change pricing, add features, or support multiple payment methods | Acceptable for MVP if using RevenueCat/Adapty |
| Skip background processing queue, do sync processing | Simpler architecture | Poor user experience, server overload, no scalability | Never acceptable - async required day 1 |
| No usage analytics or monitoring | Faster launch | Flying blind, can't optimize conversion, debug issues, or understand users | Never acceptable - basic analytics required day 1 |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Google Cloud Vision API | Sending full-resolution iris images (4000x3000px) unnecessarily, driving up costs | Downscale images to minimum required resolution (512x512px for segmentation) before API call |
| FastAPI + Celery | Not configuring result backend, losing track of async tasks | Use Redis as result backend, implement task status endpoints, store task_id in database |
| React Native Vision Camera | Using frame processors for iris capture, causing performance issues | Disable frame processors during capture, use them only for preview guidance |
| PostgreSQL + S3 | Storing S3 URLs as TEXT without validation | Use URL validation, store bucket/key separately for flexibility, implement signed URL generation |
| Stripe/IAP | Implementing both but not handling users who switch payment methods | Store payment_provider field, handle migration, allow users to manage billing from either system |
| CloudFront CDN | Serving all images through CDN without cache headers | Set appropriate Cache-Control headers: public assets (1 year), user content (1 week), with ETags |
| Apple Sign-In | Not handling user deletion properly (Apple requirement) | Implement account deletion endpoint, notify Apple of deletion, handle Sign In With Apple token revocation |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| N+1 queries loading user galleries | Gallery page takes 5+ seconds, database CPU spikes | Use eager loading/JOIN queries, implement pagination, add Redis cache | >1,000 images per user or >100 concurrent users |
| Processing all uploads immediately in request handler | API timeouts, slow response times, server overload | Implement background job queue (Celery), return immediately with task_id | >10 concurrent uploads |
| Storing full-resolution processed images (4000x3000px) | Slow loading, excessive CDN costs, mobile data usage | Generate multiple sizes (thumbnail 150px, preview 800px, full 2000px), serve appropriate size | >10,000 stored images |
| Loading all user data on app launch | Slow app startup, high memory usage, poor perceived performance | Lazy load data, implement pagination, cache critical data locally | >100 user artworks saved |
| Running AI models on CPU instead of GPU | Processing takes 30-120 seconds per image | Use GPU-enabled instances (AWS P3, GCP GPU VMs), or switch to GPU-optimized API provider | From day 1 of production |
| No connection pooling for database | "Too many connections" errors, connection overhead | Implement connection pooling (SQLAlchemy pool_size=20, max_overflow=40) | >50 concurrent users |
| Synchronous file uploads to S3 | Request hangs during upload, poor user experience | Use pre-signed URLs for direct client-to-S3 upload, or upload async in background | >1MB file sizes |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing raw iris images without encryption at rest | Biometric data breach, massive fines (€20M GDPR, $5K per record BIPA) | Enable encryption at rest for S3, database field-level encryption for sensitive data |
| Exposing S3 bucket URLs directly in API responses | Users can access other users' private iris images by guessing URLs | Use pre-signed URLs with 5-minute expiration, implement authorization checks |
| No rate limiting on AI processing endpoints | Abuse, runaway costs, API quota exhaustion | Implement rate limiting (10 requests/hour for free, 100/hour for paid) |
| Insecure token storage in mobile app | Session hijacking, unauthorized access to biometric data | Use iOS Keychain / Android Keystore for tokens, never store in AsyncStorage/SharedPreferences |
| Logging iris image URLs or user biometric data | Compliance violation, data breach via log files | Sanitize logs, never log biometric identifiers, use structured logging with PII filtering |
| Missing HTTPS pinning | Man-in-the-middle attacks, intercepted biometric data | Implement certificate pinning for API communication (iOS: TrustKit, Android: Network Security Config) |
| No input validation on uploaded images | Malicious file uploads, XSS via SVG, server compromise | Validate file types, scan for malware, strip EXIF metadata, re-encode images server-side |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing "Processing..." for 30+ seconds with no progress indication | Users think app crashed, abandon processing | Show progress bar (even if estimated), fun loading messages ("Capturing iris details...", "Applying Van Gogh style..."), allow backgrounding |
| Requiring account creation before first iris capture | Immediate drop-off, users want to try before committing | Allow guest mode with 1 test capture, show impressive result, THEN prompt to save |
| Generic error messages ("An error occurred") | Users don't know what to do, submit vague support tickets | Specific, actionable errors: "Iris not detected. Make sure your eye is in the center and well-lit." with retry button |
| No offline mode or graceful degradation | App unusable without internet, poor experience on slow connections | Cache AI models for basic styles on-device, queue uploads for later, show cached user gallery |
| Hiding quality/resolution options deep in settings | Users export low-res and are disappointed | Present quality choice at export time: "Share (optimized for social)" vs "Save Full Quality (HD)" |
| Auto-playing all animations, transitions, and effects | App feels slow, battery drain, accessibility issues | Use progressive enhancement, respect "Reduce Motion" accessibility setting |
| Overwhelming users with 50+ style choices immediately | Decision paralysis, analysis paralysis | Show 5 curated styles initially, "See more styles" reveals full catalog, recommend styles based on iris colors |
| No way to undo or re-edit processed images | Users make mistake (wrong style), have to start over | Keep editing history, allow style changes without re-capture |

---

## "Looks Done But Isn't" Checklist

Critical items that appear complete but are missing pieces:

- [ ] **Privacy Compliance:** Built consent flow BUT haven't conducted DPIA, haven't implemented geo-based consent variation, haven't tested GDPR data export, haven't documented data retention policy
- [ ] **Camera Capture:** Camera works BUT no guidance overlay, no quality validation, no burst mode for sharp capture, not tested on low-end Android devices
- [ ] **AI Processing:** Style transfer works BUT no failure handling, no quality validation, results inconsistent between runs, not tested on poor-quality inputs
- [ ] **IAP Integration:** Purchases work in sandbox BUT not tested on real devices with real payment methods, refund handling not implemented, receipt validation client-side only
- [ ] **Image Storage:** Images save to S3 BUT no CDN setup, no image optimization, URLs are public not pre-signed, no cleanup of failed uploads
- [ ] **User Accounts:** Login/signup works BUT password reset not implemented, email verification not required, account deletion not functional, no session timeout
- [ ] **Performance:** App works BUT no monitoring/logging, no error tracking, no analytics, no performance profiling, not load tested
- [ ] **Social Features:** Sharing works BUT no moderation, no reporting, consent for public sharing not clear, shared content not removed when user deletes account

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Privacy compliance failure discovered post-launch | HIGH (legal fees, potential settlement, app rebuild) | 1. Immediately stop collecting biometric data, 2. Engage privacy lawyer, 3. Conduct emergency DPIA, 4. Implement compliant consent flows, 5. Notify users of changes, 6. Offer data deletion to existing users |
| App Store rejection for Privacy Manifest | MEDIUM (2-4 weeks delay, emergency dev work) | 1. Create comprehensive Privacy Manifest, 2. Update permission strings, 3. Add in-app privacy controls, 4. Prepare detailed Review Notes, 5. Resubmit with explanation |
| AI processing costs exceed revenue by 10x | HIGH (financial crisis, emergency architecture change) | 1. Implement aggressive rate limiting immediately, 2. Add processing caps for free users, 3. Pause free tier temporarily, 4. Migrate to self-hosted models, 5. Re-evaluate pricing |
| Camera capture success rate <30% | MEDIUM (UX rebuild, user research) | 1. Add extensive guidance system, 2. Implement burst capture + auto-select, 3. Conduct user research to identify failure modes, 4. Consider alternative capture methods (video → frame extraction) |
| Database performance degradation | MEDIUM (migration to external storage) | 1. Audit database queries, add indexes, 2. Implement caching layer (Redis), 3. Migrate images to S3, update URLs, 4. Optimize database schema |
| Cross-platform camera issues on Android | MEDIUM (platform-specific code, extensive testing) | 1. Implement Android-specific camera module, 2. Test on 10+ Android devices, 3. Add device capability detection, 4. Create fallback for unsupported devices |
| Freemium conversion <1% | LOW-MEDIUM (pricing/feature iteration) | 1. Analyze user behavior (where do they drop off), 2. A/B test different paywalls, 3. Adjust free tier limitations, 4. Test different price points, 5. Improve value proposition messaging |
| Battery drain complaints | LOW (optimization work) | 1. Profile app to identify hotspots, 2. Reduce camera preview time, 3. Optimize AI processing, 4. Add battery saver mode, 5. Educate users on efficient usage |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Biometric privacy compliance failure | Phase 1: Architecture | Legal review of privacy flows, DPIA completed, consent flow user tested, geo-based compliance verified |
| App Store rejection | Phase 1: Architecture, Phase 2: MVP submission | TestFlight beta approved, Privacy Manifest validated, permission strings reviewed |
| Macro photography UX failure | Phase 2: MVP (prototype & test early) | Capture success rate >70% in user testing with 20+ participants across devices |
| AI processing costs spiral | Phase 1: Architecture (cost model), Phase 3+: Scale (monitor & optimize) | Cost-per-user <25% of LTV, usage monitoring alerts configured, rate limiting tested |
| Cross-platform camera issues | Phase 1: Architecture (framework choice), Phase 2-3: Testing | Tested on 10+ device models, crash rate <1%, platform-specific codepaths documented |
| Image quality below expectations | Phase 2-3: MVP & Iteration | User satisfaction score >4/5, quality metrics (SSIM >0.85), A/B tested models |
| Freemium conversion too low | Phase 3-4: Iteration & Optimization | Conversion rate >3% after 30 days, A/B tests running, upsell timing optimized |
| AI pipeline failures | Phase 3: AI Pipeline Refinement | Failure rate <5%, graceful degradation working, error messages user tested |
| Mobile performance issues | Phase 3-4: Optimization | Battery usage <10%/hour active use, no Google Play Store battery warnings |
| Database performance | Phase 1: Architecture, Phase 4: Scale | Query time <100ms for galleries, load test passed (1K concurrent users) |
| FastAPI bottlenecks | Phase 1: Architecture (async processing), Phase 4: Scale | Background jobs processing correctly, p95 latency <500ms, horizontal scaling tested |
| Social features moderation | Phase 5: Social Features (don't rush) | Content moderation API integrated, reporting system working, takedown process <24 hours |
| Payment integration mistakes | Phase 2: MVP | Sandbox testing complete, real purchase tested, refund handling verified |
| Onboarding friction | Phase 2-3: MVP & Iteration | Onboarding completion >60%, time-to-value <60 seconds, drop-off points identified |
| Platform feature parity | Phase 2-4: MVP through Polish | Feature parity list maintained, crash rates equal across platforms, UX reviewed separately |

---

## Sources

**Biometric Privacy & Legal:**
- [Privacy Laws 2026: Global Updates](https://secureprivacy.ai/blog/privacy-laws-2026)
- [Biometric Privacy Laws Overview](https://www.getfocal.co/post/biometric-privacy-laws-overview)
- [Biometric data and privacy laws (GDPR, CCPA/CPRA)](https://www.thalesgroup.com/en/markets/digital-identity-and-security/government/biometrics/biometric-data)
- [Data, privacy, and cybersecurity developments in 2026](https://www.mwe.com/insights/data-privacy-and-cybersecurity-developments-we-are-watching-in-2026/)
- [CCPA Requirements 2026](https://secureprivacy.ai/blog/ccpa-requirements-2026-complete-compliance-guide)
- [Illinois BIPA Litigation Tracker](https://www.stopspying.org/bipa-litigation-tracker)
- [2025 Year-In-Review: Biometric Privacy Litigation](https://www.privacyworld.blog/2025/12/2025-year-in-review-biometric-privacy-litigation/)
- [Aura Frames BIPA Settlement](https://openclassactions.com/settlements/aura-frames-biometric-privacy-class-action-settlement.php)

**App Store Guidelines & Review:**
- [Updated App Review Guidelines](https://developer.apple.com/news/?id=ey6d8onl)
- [Mobile App Consent for iOS 2025](https://secureprivacy.ai/blog/mobile-app-consent-ios-2025)
- [App Privacy Details - Apple](https://developer.apple.com/app-store/app-privacy-details/)
- [Privacy - Apple HIG](https://developer.apple.com/design/human-interface-guidelines/privacy/)

**Iris Photography Technical Challenges:**
- [Complete macro setup for photographing eyes](https://www.diyphotography.net/heres-the-complete-macro-setup-for-photographing-your-own-eye/)
- [Challenges in Macro Photography - MIOPS](https://www.miops.com/blogs/news/challenges-in-macro-photography-and-how-to-overcome-them)
- [11 Tips for Beautiful Macro Eye Photography](https://digital-photography-school.com/macro-eye-photography/)
- [Macro Eye Photography with Your Phone](https://irisblink.com/en-in/blogs/iris-art-photography-blog/macro-eye-photos)

**AI Image Processing Costs:**
- [AI-Powered Mobile App Development Cost 2026](https://www.whitehalltechnologies.com/blog/cost-to-develop-an-ai-powered-mobile-app/)
- [How Much Does AI Cost in 2026](https://www.designrush.com/agency/ai-companies/trends/how-much-does-ai-cost)
- [Vertex AI Pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)

**Cross-Platform Development:**
- [Flutter vs React Native 2026](https://dev.to/prateekshaweb/flutter-vs-react-native-which-is-better-for-cross-platform-app-development-in-2026-1e5f)
- [Why Flutter Isn't Ideal for Cross-Platform](https://kitrum.com/blog/why-flutter-isnt-ideal-for-cross-platform-development/)
- [React Native vs Flutter Field Apps Complaints](https://altersquare.medium.com/react-native-vs-flutter-for-field-apps-what-construction-users-complain-about-after-go-live-5151ddfb2314)

**React Native Vision Camera:**
- [VisionCamera Troubleshooting](https://react-native-vision-camera.com/docs/guides/troubleshooting)
- [VisionCamera Performance Guide](https://react-native-vision-camera.com/docs/guides/performance)
- [VisionCamera GitHub Issues](https://github.com/mrousavy/react-native-vision-camera/issues)

**Freemium Conversion:**
- [App Store Conversion Rate by Category 2026](https://adapty.io/blog/app-store-conversion-rate/)
- [SaaS Freemium Conversion Rates 2026](https://firstpagesage.com/seo-blog/saas-freemium-conversion-rates/)
- [How to increase free-to-paid conversion rates](https://www.plotline.so/blog/increase-free-to-paid-conversions-app)
- [State of Subscription Apps 2025](https://www.revenuecat.com/state-of-subscription-apps-2025/)

**AI Iris Segmentation:**
- [Deep Learning for Iris Recognition Survey](https://dl.acm.org/doi/10.1145/3651306)
- [Robust Iris Segmentation in Non-Cooperative Environments](https://pmc.ncbi.nlm.nih.gov/articles/PMC7922029/)
- [Comprehensive Evaluation of Iris Segmentation](https://pmc.ncbi.nlm.nih.gov/articles/PMC11548766/)
- [The removal of specular reflection in noisy iris image](https://www.researchgate.net/publication/309769406_The_removal_of_specular_reflection_in_noisy_iris_image)

**Mobile Photography User Expectations:**
- [iPhone Photography Trends 2026](https://www.shiftcam.com/blogs/gear-guides/mobile-photography-trends-in-2026-how-iphone-photography-became-a-real-camera-system)
- [23+ Mobile Photography Statistics 2026](https://passport-photo.online/blog/mobile-photography-trends-and-stats/)
- [Photography Trends 2026](https://www.pixpa.com/blog/photography-trends)

**AI Style Transfer Quality:**
- [Applying deep learning for style transfer in digital art](https://www.nature.com/articles/s41598-025-95819-9)
- [Consistent AI image generation style - Figma Forum](https://forum.figma.com/ask-the-community-7/consistent-ai-image-generation-style-43431)
- [Best AI Style Transfer Tools 2026](https://www.myarchitectai.com/blog/ai-style-transfer-tools)
- [Qualitative Failures of Image Generation Models](https://arxiv.org/html/2304.06470v5)

**Onboarding & User Activation:**
- [100+ User Onboarding Statistics 2026](https://userguiding.com/blog/user-onboarding-statistics)
- [Ultimate Mobile App Onboarding Guide 2026](https://vwo.com/blog/mobile-app-onboarding-guide/)
- [Best Mobile App Onboarding Examples 2026](https://www.plotline.so/blog/mobile-app-onboarding-examples)
- [Drop-off analysis - Sprig](https://sprig.com/blog/drop-off-analysis)

**FastAPI Performance:**
- [Profiling FastAPI Applications](https://pysquad.com/blogs/profiling-fastapi-applications-demystifying-perfor)
- [FastAPI Mistakes That Kill Performance](https://dev.to/igorbenav/fastapi-mistakes-that-kill-your-performance-2b8k)
- [Understanding Performance Bottlenecks in FastAPI](https://medium.com/@rameshkannanyt0078/understanding-performance-bottlenecks-in-fastapi-with-cpu-bound-tasks-f26b718cdced)
- [FastAPI Performance Optimization Guide](https://pytutorial.com/fastapi-performance-optimization-guide/)

**Content Moderation:**
- [AI Content Moderation Trends 2026](https://www.conectys.com/blog/posts/ai-content-moderation-trends-for-2026/)
- [Future of Content Moderation 2026 - Imagga](https://imagga.com/blog/the-future-of-content-moderation-trends-for-2026-and-beyond/)
- [Content Moderation Definitive 2026 Guide](https://www.webpurify.com/blog/content-moderation-definitive-guide/)
- [AI Social Feeds 2026: Biometrics and Ethical Risks](https://www.webpronews.com/ai-social-feeds-in-2026-hyper-personalization-biometrics-and-ethical-risks/)

**PostgreSQL Image Storage:**
- [Optimizing Image Storage in PostgreSQL](https://medium.com/@ajaymaurya73130/optimizing-image-storage-in-postgresql-tips-for-performance-scalability-fd4d575a6624)
- [BinaryFilesInDB - PostgreSQL wiki](https://wiki.postgresql.org/wiki/BinaryFilesInDB)
- [Handling Large Objects in Postgres](https://www.tigerdata.com/learn/handling-large-objects-in-postgres)

**Battery Drain:**
- [Top 10 Apps Draining Battery 2026](https://www.techloy.com/top-10-apps-draining-your-smartphone-battery-in-2026-and-how-to-stop-them/)
- [Solving Battery Drain in Mobile Apps](https://netforemost.com/solving-battery-drain-in-mobile-apps/)
- [Google Play Store Battery-Draining Warnings 2026](https://www.webpronews.com/google-play-store-to-warn-users-of-battery-draining-apps-in-2026/)
- [How to Reduce App's Battery Drain](https://thisisglance.com/learning-centre/how-do-i-reduce-my-apps-battery-drain-on-users-phones)

**Payment Integration:**
- [Avoid Apple's 30% App Store Cut](https://passion.io/blog/avoid-apple-30-app-store-cut-a-creators-guide)
- [Payment Guide for Mobile Applications: IAP](https://medium.com/@phamtuanchip/payment-guide-for-mobile-applications-in-app-purchases-6742ba15afdf)
- [Can You Use Stripe for In-App Purchases 2026](https://adapty.io/blog/can-you-use-stripe-for-in-app-purchases/)
- [Best Practices for In-App Purchase Integration](https://www.sevensquaretech.com/best-practices-in-app-purchase-integration/)

---

*Pitfalls research for: IrisVue - AI-powered iris photography mobile app*
*Researched: 2026-02-01*
*Confidence: HIGH (all findings based on 2025-2026 sources, legal research, and technical documentation)*
