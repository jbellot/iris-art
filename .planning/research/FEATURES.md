# Feature Research

**Domain:** Iris Photography & AI Art Mobile App
**Researched:** 2026-02-01
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Authentication - Email/Password** | Standard across all mobile apps | LOW | Basic requirement for account creation and data persistence |
| **Authentication - Social Login (Apple, Google)** | Apple mandates Sign in with Apple when other social logins present; users expect quick signup | LOW | Apple App Store requirement when offering other third-party logins; reduces friction |
| **Camera Capture Interface** | Core function - users expect intuitive photo capture | MEDIUM | Must work reliably across different device cameras and lighting conditions |
| **Photo Gallery/Library** | Users expect to see and manage their captured irises | LOW | Standard gallery UI pattern with thumbnail views |
| **Basic Image Editing/Enhancement** | Users expect some control over brightness, contrast, etc. | MEDIUM | Common in all photo apps; iris-specific: reflection removal, color enhancement |
| **HD/High-Resolution Export** | Professional print quality expected for artistic output | LOW | Standard image export at full resolution (minimum 4K for prints) |
| **Image Preview Before Export** | Users need to see final result before committing | LOW | Standard preview modal with zoom capability |
| **Preset Art Styles** | AI art apps always offer predefined styles for quick transformation | MEDIUM | 5-10 free styles minimum; users expect instant preview |
| **Save/Download to Device** | Basic expectation - users want to keep their creations | LOW | Standard photo library integration |
| **Basic Sharing (Social Media)** | Users expect to share creations to Instagram, Facebook, etc. | LOW | Native share sheet integration |
| **Account Data Persistence** | Users expect their photos and settings to persist across sessions | LOW | Cloud storage for user data; local caching for performance |
| **Freemium Model with Clear Tiers** | Standard monetization approach for creative apps | LOW | Free tier must be valuable enough to engage users; premium must be compelling |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Real-Time AI-Guided Iris Capture** | Makes professional iris photography accessible to anyone without special equipment | HIGH | IrisVue's core differentiator; provides real-time feedback on focus, lighting, distance, and eye positioning; eliminates need for macro lenses and professional setup |
| **AI Iris Extraction & Enhancement** | Automatically removes reflections and enhances iris detail | HIGH | Critical for quality; existing services like IRIS PHOTO.ART and Eyemazy do this manually with specialized equipment; automating this with AI democratizes the process |
| **Named Circles (Private Shared Galleries)** | Enables couples/families to collect and organize iris photos together | MEDIUM | Unique to IrisVue; different from generic photo sharing - purpose-built for iris collections; inspired by PhotoCircle and Family Circle apps but iris-specific |
| **Iris Fusion Art** | Blend multiple irises into single artistic piece or side-by-side compositions | MEDIUM | Romantic/family appeal; couple designs popular in market (Cosmic Eye offers this as premium service); technical challenge: seamless blending of circular images |
| **AI-Generated Unique Styles** | Beyond presets - AI creates one-of-a-kind artistic interpretations | HIGH | Differentiates from simple filter apps; leverages neural style transfer; requires robust AI infrastructure; Dream by WOMBO has 200M+ users with this capability |
| **In-App Camera Controls for Macro Photography** | Provides manual controls optimized for iris capture (focus, exposure, stabilization guides) | MEDIUM | Addresses technical challenge of iris photography; guides users through optimal settings (f/8-f/11 aperture equivalent, ISO 100, focus distance) |
| **Instant Processing** | AI processing completes in seconds, not minutes | MEDIUM | Speed matters - IRIS PHOTO.ART promises 10 minutes with specialized equipment; mobile app should deliver results instantly for competitive advantage |
| **Offline Capture Capability** | Can capture and queue processing when offline | MEDIUM | Differentiator for mobile app; sync when connected; important for on-the-go use |
| **Progressive Quality Preview** | Show low-res style preview immediately, progressively enhance to HD | MEDIUM | Improves perceived performance; lets users iterate quickly on style choices before committing to HD render |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Full Social Network** | Users want to share and discover | Massive complexity; moderation costs; shifts focus from core value; crowded market | Private named circles + standard share to existing social platforms; focus on intimate sharing, not public discovery |
| **Unlimited Free HD Exports** | Users always want everything free | No monetization path; HD rendering is computationally expensive; unsustainable | Generous free tier with watermarked exports or SD resolution; HD as premium feature at 4.99EUR is competitive and sustainable |
| **Real-Time Video Processing** | "Make it work in video too!" | Exponentially more complex than static images; massive compute requirements; battery drain; market not proven | Focus on perfecting still photography first; capture multiple frames for best shot selection, not video |
| **Comprehensive Photo Editor** | "Add all Photoshop features!" | Bloat and complexity; feature creep; slower app; confused value prop | Iris-specific editing only (reflection removal, iris enhancement, artistic rendering); integrate with system photo editor for general edits |
| **Print Shop in V1** | Natural extension of art creation | Complex fulfillment, shipping, customer service, quality control; inventory management; diverts engineering from core product | Partner with existing print services or defer to V2; let users export HD and print anywhere |
| **AI Avatar Generation (like Lensa)** | AI avatars are trendy | Different AI models; different UX; dilutes focus on iris photography; crowded market with many competitors | Stay focused on iris art photography as unique positioning; iris fusion offers personalization without competing in oversaturated avatar market |
| **Every Art Style Imaginable** | More = better, right? | Style fatigue; maintenance burden; quality dilution; analysis paralysis for users | Curate 15-20 high-quality styles (5-10 free, 10-15 premium); emphasize AI-generated unique styles over preset quantity |
| **B2B Features in V1** | Revenue opportunity from photographers/optometrists | Different UX needs; different pricing model; enterprise features (multi-user accounts, licensing, white-label); support complexity | Explicitly defer to post-V1; validate consumer product first; B2B requires separate go-to-market strategy |

## Feature Dependencies

```
[Authentication]
    └──required_for──> [Account Data Persistence]
                           └──required_for──> [Named Circles]
                           └──required_for──> [Cloud Gallery]

[Camera Capture]
    └──required_for──> [AI Iris Extraction]
                           └──required_for──> [Artistic Rendering]
                                                  └──optional──> [Iris Fusion]

[Real-Time AI Guidance]
    └──enhances──> [Camera Capture]

[Artistic Rendering]
    └──required_for──> [HD Export (Premium)]
    └──required_for──> [Named Circles (sharing rendered art)]

[Preset Styles]
    └──parallel_to──> [AI-Generated Unique Styles]

[Basic Image Enhancement]
    └──required_for──> [Artistic Rendering]
    └──required_for──> [Iris Fusion]

[Named Circles]
    └──optional_enhancement_of──> [Photo Gallery]
    └──enables──> [Iris Fusion (multi-user collaboration)]
```

### Dependency Notes

- **Authentication → Named Circles:** Cannot share galleries without user accounts; authentication must be implemented first
- **Camera Capture → AI Extraction → Rendering:** Sequential pipeline; each stage depends on previous; quality of extraction affects final render quality
- **Real-Time AI Guidance enhances Camera Capture:** Not required but significantly improves capture success rate; can be iteratively improved post-launch
- **Preset Styles ⊥ AI-Generated Styles:** These are parallel offerings, not sequential; both rely on artistic rendering infrastructure
- **Named Circles ⊥ Iris Fusion:** While named circles enable multi-user iris collection which enhances fusion use cases, fusion can work standalone with single user's multiple irises

## MVP Definition

### Launch With (V1)

Minimum viable product — what's needed to validate the concept.

- [x] **Email/Password + Apple/Google Authentication** — Table stakes for account management; Apple App Store requirement
- [x] **AI-Guided Real-Time Iris Capture** — Core differentiator; validates technology feasibility; addresses main pain point (professional iris photography is inaccessible)
- [x] **AI Iris Extraction & Enhancement** — Required for quality output; validates AI pipeline
- [x] **5-10 Preset Artistic Styles (Free)** — Table stakes for AI art app; enough variety to demonstrate value
- [x] **10-15 Premium Artistic Styles** — Monetization path; demonstrates value of upgrade
- [x] **AI-Generated Unique Style (Premium)** — Key differentiator; "one-of-a-kind art" is compelling value prop
- [x] **Iris Fusion (Blend + Side-by-Side)** — Differentiator; romantic/family appeal; validates collaborative use case
- [x] **Named Circles (Shared Galleries)** — Differentiator; enables viral growth (invite partners/family); validates social feature
- [x] **HD Export (Premium, 4.99EUR)** — Core monetization; competitive pricing
- [x] **Basic Share to Social Media** — Table stakes; enables organic marketing
- [x] **Local + Cloud Gallery** — Table stakes; expected data persistence

### Add After Validation (V1.x)

Features to add once core is working.

- [ ] **Progressive Quality Preview** — Improves UX but not blocking; can optimize based on usage patterns
- [ ] **Additional Art Style Packs** — After validating which free/premium styles perform best
- [ ] **Iris Enhancement Fine-Tuning Controls** — Advanced users may want granular control (brightness, contrast, saturation specific to iris)
- [ ] **Batch Processing** — Process multiple irises with same style; QoL improvement for power users
- [ ] **Activity Feed in Named Circles** — See when family members add new irises; adds engagement without full social network complexity
- [ ] **Custom Iris Names/Labels** — "Mom's left eye," "Sarah's hazel iris" - improves organization
- [ ] **Style Favorites** — Let users save preferred styles for quick access
- [ ] **Offline Mode Enhancements** — Better offline capture queuing and sync management
- [ ] **Watermark Customization** — Free tier watermark options (corner position, size, etc.)

### Future Consideration (V2+)

Features to defer until product-market fit is established.

- [ ] **Print Shop Integration** — Defer to V2; requires fulfillment partnerships, complex logistics
- [ ] **B2B Portal** — Different product; professional photographers, optometrists, retail iris photo booths
- [ ] **Video Capture Mode** — After still photography is perfected; much higher technical complexity
- [ ] **AI Avatar Generation** — Avoid diluting focus; crowded market; stick to iris art differentiation
- [ ] **White-Label Offering** — B2B opportunity but requires enterprise features and sales motion
- [ ] **Physical Product Marketplace** — Jewelry, keychains, etc. with iris art; requires partners and quality control
- [ ] **Public Gallery/Discovery** — Full social network; moderation complexity; stick to private circles
- [ ] **Animated Iris Art** — Movement effects on iris images; interesting but lower priority than core quality
- [ ] **Multi-Language Support** — Start with English; expand based on market traction
- [ ] **Gift/Send Credits** — Allow users to gift HD exports or premium access to circle members

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| AI-Guided Real-Time Capture | HIGH | HIGH | P1 |
| AI Iris Extraction | HIGH | HIGH | P1 |
| Auth (Email + Social) | HIGH | LOW | P1 |
| Preset Artistic Styles (5-10 free) | HIGH | MEDIUM | P1 |
| HD Export (Premium) | HIGH | LOW | P1 |
| Named Circles | MEDIUM | MEDIUM | P1 |
| Iris Fusion | MEDIUM | MEDIUM | P1 |
| Premium Styles (10-15) | HIGH | MEDIUM | P1 |
| AI-Generated Unique Style | HIGH | HIGH | P1 |
| Basic Social Sharing | MEDIUM | LOW | P1 |
| Cloud Gallery Storage | HIGH | LOW | P1 |
| Progressive Preview | MEDIUM | MEDIUM | P2 |
| Iris Enhancement Controls | MEDIUM | MEDIUM | P2 |
| Batch Processing | MEDIUM | MEDIUM | P2 |
| Activity Feed (Circles) | MEDIUM | LOW | P2 |
| Custom Labels | LOW | LOW | P2 |
| Style Favorites | LOW | LOW | P2 |
| Print Shop | LOW | HIGH | P3 |
| B2B Portal | LOW | HIGH | P3 |
| Video Capture | LOW | HIGH | P3 |
| Public Gallery | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for launch — validates core value proposition and enables monetization
- P2: Should have, add when possible — enhances UX and engagement post-launch
- P3: Nice to have, future consideration — deferred until product-market fit established

## Competitor Feature Analysis

| Feature | Iris Photo Services (IRIS PHOTO.ART, Eyemazy, Cosmic Eye) | AI Art Apps (WOMBO Dream, Lensa, Prisma) | IrisVue Approach |
|---------|----------------------------------|--------------------------|------------------|
| **Iris Capture** | Professional equipment (macro lenses, specialized lighting, studio setup) | N/A | AI-guided mobile camera with real-time feedback — democratizes access |
| **Processing Time** | 10 minutes in-person (IRIS PHOTO.ART) | 5-30 seconds for style transfer | Target: <10 seconds for style preview, <30 seconds for HD render |
| **Art Styles** | Limited to photography + standard print treatments | 20-100+ preset styles; AI-generated variations | Hybrid: curated presets (15-20) + AI-generated unique styles |
| **Delivery** | Physical print + optional digital | Digital only with download | Digital-first; HD export premium; defer print to V2 |
| **Pricing** | $30-100+ per session/print | Freemium: Free with ads/watermarks; $3-10/month for premium | Freemium: Free basic styles + SD export; 4.99EUR per HD export (competitive with AI art apps, much cheaper than in-person services) |
| **Collaboration** | N/A - individual service | N/A - individual creation | Named circles for couples/families; iris fusion art |
| **Location** | Physical locations (galleries, malls); mail-in selfie service (Cosmic Eye) | Available anywhere with smartphone | Available anywhere with smartphone |
| **Quality** | Professional macro photography; very high resolution | Varies; dependent on input quality | AI-enhanced from mobile camera; HD output competitive with professional |
| **Reflection Removal** | Manual editing by professionals | N/A | Automated AI removal during extraction |
| **Customization** | Limited - choose print format | High - adjust styles, upload reference images | High - preset styles + AI-generated + fusion options |
| **Social Features** | None | Limited - share to social media | Named circles (private groups) + standard social sharing |
| **Unique Selling Point** | Professional quality, studio experience | AI art generation from any photo | Professional iris photography on mobile + AI art + private collaboration |

### Key Competitive Insights

**vs. Iris Photography Services:**
- **IrisVue Advantage:** Accessibility (anywhere, anytime), lower cost, instant results, collaborative features
- **Service Advantage:** Professional equipment quality, in-person guidance, immediate physical product
- **IrisVue Strategy:** Position as "professional iris art at home" rather than competing on absolute image quality

**vs. AI Art Apps:**
- **IrisVue Advantage:** Specialized for iris photography (AI-guided capture + extraction), named circles for meaningful sharing, iris fusion unique to use case
- **AI Art Apps Advantage:** Broader use case (any photo), larger style libraries, established user base
- **IrisVue Strategy:** Own the iris art category; leverage specificity as strength (purpose-built vs. general-purpose)

**Blue Ocean Opportunity:**
- Neither category offers AI-guided mobile iris capture + artistic rendering + private collaborative galleries
- IrisVue combines accessibility of AI art apps with specialization of iris photography services
- Named circles and fusion features create network effects without full social network complexity

## Monetization Features

### Free Tier (Acquisition & Engagement)

**Goal:** Demonstrate value; create "aha moment"; drive viral growth through named circles

- Email/password authentication
- Apple/Google social login
- AI-guided iris capture (unlimited)
- AI iris extraction & enhancement (unlimited)
- 5-10 preset artistic styles (curated free tier)
- Standard definition export (1080p with small IrisVue watermark)
- Share to social media with watermark
- Join named circles (unlimited)
- Create up to 3 named circles
- Basic iris fusion (up to 2 irises, SD export only)
- Cloud storage for up to 10 iris photos

**Value Proposition:** "Create beautiful iris art free. Professional results without professional equipment."

### Premium Features (Monetization)

**Goal:** Convert engaged users; provide clear value for 4.99EUR price point

**Per-Export Premium (4.99EUR per HD export):**
- HD/4K export (no watermark)
- Print-ready resolution (suitable for 8x10" prints minimum)
- Commercial usage rights

**Subscription Model Consideration (Deferred to V1.x):**
- If user data shows frequent HD exports, consider 9.99EUR/month unlimited HD
- Current one-time pricing better for occasional users (couples doing iris art once)
- Subscription makes sense if users export frequently (multiple circles, experimentation)

**Premium Style Access (Included in HD Export Purchase):**
- 10-15 premium preset styles (exclusive)
- AI-generated unique style (one-of-a-kind composition)
- Premium iris fusion effects (advanced blending algorithms)
- Multi-iris fusion (3+ irises in single artwork)

**Storage Expansion (Potential Future Monetization):**
- Free tier: 10 iris photos
- Power users may want 50+ (large families, multiple circle memberships)
- Consider storage tiers if data shows need: 0.99EUR/month for 50 irises

### Monetization Strategy

**V1 Focus: Per-Export HD Sales**
- Clear value: "Pay for what you print"
- Low friction: No commitment, no subscription fatigue
- Aligns with use case: Couples doing iris art create 2-4 final pieces
- Competitive: Much cheaper than in-person services ($30-100), competitive with AI art apps ($3-10/month but require ongoing subscription)

**Expected Conversion Funnel:**
1. **100 downloads** (organic + circles invites)
2. **60 capture iris** (60% activation - guided capture reduces friction)
3. **45 apply styles** (75% of captured - style preview is instant gratification)
4. **15 export SD** (33% of styled - validate output before purchase)
5. **3-5 purchase HD** (20-33% conversion - couples typically buy 2-4 HD exports)

**Revenue per 100 downloads:** 3-5 HD exports × 4.99EUR = 15-25EUR
**Target CAC:** <10EUR to achieve profitability with V1 pricing

## Sources

### Iris Photography Services
- [Iris Photo - irisphoto.com](https://irisphoto.com/)
- [IRIS PHOTO.ART](https://irisphoto.art/)
- [Cosmic Eye Iris Photo](https://cosmiceye.us/)
- [Eyemazy Iris Photography](https://www.eyemazy.com/)
- [Eyepic: Epic Iris Photos - App Store](https://apps.apple.com/us/app/eyepic-epic-iris-photos/id6449165241)
- [Iris Photography Complete Guide - Maurizio Mercorella](https://www.mauriziomercorella.com/color-grading-blog/complete-guide-iris-photography-tips)
- [Eye Photography Guide - Adorama](https://www.adorama.com/alc/eye-photography-guide/)
- [Professional Eye Photography Tutorial - Adaptalux](https://adaptalux.com/professional-eye-photography-tutorial/)

### AI Art Generation Apps
- [Top 10 Mobile AI Art Generator Apps in 2026 - Metaverse Post](https://mpost.io/top-10-mobile-ai-art-generator-apps-in-2026-for-android-and-ios/)
- [WOMBO Dream - AI Art Generator - App Store](https://apps.apple.com/us/app/wombo-dream-ai-art-generator/id1586366816)
- [Dream by WOMBO: Key Features, Pricing, & Alternatives in 2026 - TechShark](https://techshark.io/tools/dream-by-wombo/)
- [How To Build An App Like WOMBO Dream - DevTechnosys](https://devtechnosys.com/insights/build-an-app-like-wombo-dream/)
- [Best AI Style Transfer Tools 2026 - MyArchitectAI](https://www.myarchitectai.com/blog/ai-style-transfer-tools)
- [AI Image Generators 2026 Comparison - Felo Search](https://felo.ai/blog/ai-image-generators-2026/)

### Personalized Art & Gift Platforms
- [Personalized Gifts Market - Custom Gift Trends 2026 - InkedJoy](https://inkedjoy.com/blog/trending-custom-gifts-ideas-2026)
- [Future of Personalized Gifts 2026 - Customily](https://www.customily.com/post/the-future-of-personalized-gifts-whats-coming)
- [Top Personalized Gifts Companies 2026 - Global Growth Insights](https://www.globalgrowthinsights.com/blog/personalized-gifts-companies-1101)
- [Uncommon Goods - Personalized Art Gift Ideas 2026](https://www.uncommongoods.com/home-garden/art/personalized)

### Mobile Photography Apps
- [Mobile Photography Trends 2026 - ShiftCam](https://www.shiftcam.com/blogs/gear-guides/mobile-photography-trends-in-2026-how-iphone-photography-became-a-real-camera-system)
- [Best Photography Apps for Smartphone 2026 - Photography Playground](https://photography-playground.com/photography-apps-smartphone-photography/)
- [Smartphone Cameras 2026: AI and Advanced Features - Tech Times](https://www.techtimes.com/articles/314267/20260124/smartphone-cameras-2026-how-ai-advanced-features-outperform-megapixels.htm)
- [Best Photo Editing Apps 2026 - Imagine.art](https://www.imagine.art/blogs/best-photo-editing-apps)

### Shared Galleries & Social Features
- [PhotoCircle - Private Photo Sharing App](https://www.photocircleapp.com/)
- [Family Circle App - App Store](https://apps.apple.com/us/app/family-circle-app/id1499315456)
- [Best Family Photo-Sharing Apps - TinyBeans](https://tinybeans.com/modern-photo-sharing-apps/)

### Mobile App Monetization
- [12 Mobile App Monetisation Strategies for 2026 - Publift](https://www.publift.com/blog/app-monetization)
- [Mobile App Monetization Strategies 2026 - Onix Systems](https://onix-systems.com/blog/pitfalls-and-springboards-of-mobile-app-monetization)
- [Mobile App Monetization 2026 - Adjoe](https://adjoe.io/blog/app-monetization-strategies/)
- [Best Mobile App Monetization Strategies 2026 - Adapty](https://adapty.io/blog/mobile-app-monetization-strategies/)
- [Freemium vs Premium Mobile Apps - Choicely](https://www.choicely.com/blog/freemium-vs-premium-mobile-apps-comparing-monetization-models)

### Authentication & Technical Standards
- [Apple Sign-In Requirements - WorkOS](https://workos.com/blog/apple-app-store-authentication-sign-in-with-apple-2025)
- [App Trends 2026 - Mindster](https://mindster.com/mindster-blogs/app-trends-2026/)

### AI & Computer Vision
- [Computer Vision Trends 2026 - API4AI](https://medium.com/@API4AI/computer-vision-technologies-2026-what-to-expect-83414770348c)
- [AI Camera Technology - Samsung Semiconductor](https://semiconductor.samsung.com/applications/ai/ai-camera/)

### Image Fusion & Blending
- [AI Image Fusion: Combine Two Photos - Cyberlink](https://www.cyberlink.com/blog/photo-effects/3496/ai-image-fusion)
- [Image Combiner: Merge Photos - Photoleap](https://www.photoleapapp.com/features/combine-photos)
- [Multi-Image Fusion - Media.io](https://www.media.io/image-effects/multi-image-fusion.html)

---
*Feature research for: IrisVue - Iris Photography & AI Art Mobile App*
*Researched: 2026-02-01*
*Confidence: HIGH - Based on current market analysis, competitor research, and 2026 mobile app standards*
