# Phase 5: Social Features (Circles and Fusion) - Research

**Researched:** 2026-02-09
**Domain:** Multi-user social features, invite systems, shared galleries, image composition, consent management
**Confidence:** HIGH

## Summary

Phase 5 implements comprehensive social features enabling users to form named circles (couple, family, friends), share iris art in group galleries, and create fusion artworks by blending multiple irises together. The phase introduces multi-tenancy patterns, relationship-based access control, consent workflows, and advanced image composition techniques while maintaining the biometric privacy compliance established in Phase 1.

The research confirms that the existing stack (FastAPI + PostgreSQL + SQLAlchemy async + React Native) is well-suited for this phase with strategic additions. The critical technical decisions are: (1) using multi-tenancy patterns with circle membership as the organizing principle, (2) implementing shareable invite tokens with expiration and single-use constraints, (3) using relationship-based access control (ReBAC) for gallery permissions and consent tracking, (4) applying Poisson image blending for seamless iris fusion and OpenCV hconcat/vconcat for side-by-side compositions, (5) implementing explicit consent flows with per-artwork permissions, and (6) using soft delete for user departures with hard delete for GDPR compliance.

The primary challenges are: (1) designing a circle membership model that supports multi-user galleries with clear ownership and permissions, (2) generating secure, time-limited invite links with deep linking on mobile, (3) implementing granular consent tracking (who can use whose art for fusion), (4) ensuring content visibility rules when users leave circles (remove from shared gallery but preserve in personal gallery), (5) optimizing Poisson blending for high-resolution iris images (computationally expensive), and (6) handling edge cases like circular consent dependencies and race conditions in concurrent fusion requests.

**Primary recommendation:** Build circles as first-class multi-tenant entities with explicit membership and role management, use itsdangerous for tamper-proof invite tokens with 7-day expiration, implement ReBAC consent system where users explicitly approve artwork usage per composition, use OpenCV Poisson blending (cv2.seamlessClone) for fusion with fallback to simple alpha blending, apply soft delete to circle memberships (for audit trail) with hard delete on GDPR requests, and leverage React Native deep linking with Branch.io for universal invite links that work across platforms.

## Standard Stack

### Core - Backend (Circles and Permissions)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **FastAPI** | >=0.115.0 | Already in stack | Native async, dependency injection perfect for multi-tenancy scoping |
| **SQLAlchemy 2.0** | >=2.0.0 | Already in stack | Async ORM with relationship mapping, cascade deletes for cleanup |
| **PostgreSQL** | 15+ | Already in stack | Robust foreign keys, cascade policies, JSON columns for metadata |
| **itsdangerous** | latest | Secure token generation | Already in Phase 1, generates tamper-proof time-limited invite tokens |
| **Redis** | 7+ | Already in stack | Cache circle memberships, track used invite tokens, rate limiting |

### Core - Backend (Image Composition)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **OpenCV (cv2)** | 4.10.x | Already in stack (Phase 3-4) | Poisson blending (seamlessClone), hconcat/vconcat for layouts, proven performance |
| **Pillow** | 11.x | Already in stack | Image I/O, resizing for composition alignment, metadata handling |
| **numpy** | 2.x | Already in stack | Array operations for blending masks, alpha channel manipulation |
| **Celery** | 5.6.x | Already in stack | Async fusion tasks (Poisson blending is CPU-intensive, 5-15s per fusion) |

### Core - Mobile (Invites and Consent)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **React Navigation** | 7.x | Already in stack | Deep linking configuration for invite URLs, nested navigation for circles |
| **react-native-branch** | 6.x | Deep linking and attribution | Industry standard for invite systems, handles universal links, deferred deep links, attribution |
| **@react-native-async-storage/async-storage** | 1.x | Already in stack | Cache circle memberships locally for offline gallery browsing |
| **axios** | 1.x | Already in stack | API calls for circle CRUD, consent management, fusion requests |

### Supporting - Backend

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **Pydantic** | 2.x | Already in stack | Validation for invite token payloads, circle membership schemas |
| **boto3** | latest | Already in stack | S3 operations for fusion artwork storage |

### Supporting - Mobile

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **react-native-share** | latest | Social sharing | Share invite links via SMS, WhatsApp, email |
| **@react-native-clipboard/clipboard** | latest | Clipboard operations | Copy invite link for manual sharing |
| **react-native-modal** | latest | Modal dialogs | Consent approval dialogs, circle creation forms |

### Architecture Patterns by Feature

| Feature | Pattern | Backend Implementation | Mobile Implementation | Confidence |
|---------|---------|------------------------|----------------------|------------|
| **Circle Membership** | Multi-tenancy with explicit join table | Circle, CircleMembership, role-based access | Circle list, member list, role badges | HIGH |
| **Invite System** | Time-limited signed tokens with deep links | itsdangerous token + expiration + single-use tracking | Branch.io universal links, navigation to join screen | HIGH |
| **Shared Gallery** | Union query across circle members with visibility rules | SELECT photos WHERE user_id IN (circle members) AND visible=true | Gallery screen with "circle mode" filter | HIGH |
| **Consent Tracking** | Explicit per-artwork permissions with ReBAC | ArtworkConsent model: (artwork_id, grantor, grantee, purpose) | Consent request modal, approval/deny buttons | HIGH |
| **Iris Fusion** | Poisson blending with mask generation | cv2.seamlessClone with iris mask, Celery task for async processing | Fusion preview, select members' art, submit for processing | MEDIUM |
| **Side-by-Side Composition** | Grid layout with OpenCV hconcat/vconcat | cv2.hconcat/vconcat with resize to match dimensions | Collage builder UI, drag-to-reorder | HIGH |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Branch.io for deep linking | React Navigation Linking only | Branch.io adds attribution, deferred deep links, easier universal link setup vs manual config |
| ReBAC consent model | Simple boolean "shareable" flag | ReBAC enables per-user, per-artwork, per-purpose consent vs all-or-nothing sharing |
| Poisson blending | Simple alpha blending | Poisson creates seamless fusion (gradient-based) vs alpha blending (visible seams) |
| Soft delete memberships | Hard delete only | Soft delete preserves audit trail for "who was in circle when fusion was created" vs clean erasure |
| Circle ownership | Flat membership only | Owner role enables admin actions (remove members, delete circle) vs democratic chaos |
| itsdangerous tokens | UUID in database | itsdangerous tokens are stateless (no DB lookup), tamper-proof, time-limited vs DB overhead |

**Installation:**
```bash
# Backend (Python) - add to requirements.txt
# All core libraries already in stack from Phases 1-4
# No new dependencies needed

# Mobile (React Native)
npm install react-native-branch
npm install react-native-share
npm install @react-native-clipboard/clipboard
npm install react-native-modal

# iOS specific
cd ios && pod install && cd ..
```

## Architecture Patterns

### Recommended Project Structure

```
backend/
├── app/
│   ├── models/
│   │   ├── circle.py                  # NEW: Circle model
│   │   ├── circle_membership.py       # NEW: Membership join table
│   │   ├── artwork_consent.py         # NEW: Per-artwork consent tracking
│   │   ├── fusion_artwork.py          # NEW: Fusion composition metadata
│   │   └── invite_token.py            # NEW: Used token tracking (optional)
│   ├── api/
│   │   └── routes/
│   │       ├── circles.py             # NEW: Circle CRUD, member management
│   │       ├── invites.py             # NEW: Generate/accept invites
│   │       ├── consent.py             # NEW: Request/grant/revoke consent
│   │       └── fusion.py              # NEW: Create fusion, composition
│   ├── services/
│   │   ├── circle_service.py          # NEW: Circle business logic
│   │   ├── invite_service.py          # NEW: Token generation/validation
│   │   ├── consent_service.py         # NEW: Consent workflows
│   │   └── fusion_service.py          # NEW: Composition logic
│   └── workers/
│       └── tasks/
│           ├── fusion_blending.py     # NEW: Poisson blending task
│           └── composition.py         # NEW: Side-by-side layout task

mobile/
├── src/
│   ├── screens/
│   │   └── Circles/
│   │       ├── CirclesListScreen.tsx           # NEW: Browse circles
│   │       ├── CreateCircleScreen.tsx          # NEW: Create circle form
│   │       ├── CircleDetailScreen.tsx          # NEW: Members, shared gallery
│   │       ├── InviteScreen.tsx                # NEW: Generate/share invite
│   │       ├── JoinCircleScreen.tsx            # NEW: Accept invite (deep link)
│   │       ├── SharedGalleryScreen.tsx         # NEW: Circle's combined gallery
│   │       ├── FusionBuilderScreen.tsx         # NEW: Select art, fusion settings
│   │       └── ConsentRequestScreen.tsx        # NEW: Approve/deny consent
│   ├── components/
│   │   └── Circles/
│   │       ├── CircleCard.tsx                  # NEW: Circle thumbnail
│   │       ├── MemberList.tsx                  # NEW: Member avatars
│   │       ├── ConsentModal.tsx                # NEW: Consent approval UI
│   │       └── ArtworkSelector.tsx             # NEW: Multi-select for fusion
│   ├── services/
│   │   ├── circles.ts                          # NEW: Circle API calls
│   │   ├── invites.ts                          # NEW: Invite API calls
│   │   └── fusion.ts                           # NEW: Fusion API calls
│   └── navigation/
│       └── CirclesNavigator.tsx                # NEW: Circle stack navigator
```

### Pattern 1: Circle Membership with Role-Based Access

**What:** Multi-tenancy pattern where Circle is the tenant, CircleMembership is the join table with roles (owner, member), access control checks membership before showing shared gallery.

**When to use:** All circle-related operations — only members can view shared gallery, only owner can remove members or delete circle.

**Example:**
```python
# backend/app/models/circle.py
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base
import uuid

class Circle(Base):
    """Named group for sharing iris art (couple, family, friends)."""
    __tablename__ = "circles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)  # "My Family", "Couple Art"
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    memberships: Mapped[List["CircleMembership"]] = relationship(
        "CircleMembership", back_populates="circle", cascade="all, delete-orphan"
    )
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])

# backend/app/models/circle_membership.py
class CircleMembership(Base):
    """Join table for Circle membership with roles."""
    __tablename__ = "circle_memberships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    circle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("circles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped[str] = mapped_column(String, default="member", nullable=False)  # "owner", "member"
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    left_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # Soft delete

    # Relationships
    circle: Mapped["Circle"] = relationship("Circle", back_populates="memberships")
    user: Mapped["User"] = relationship("User")

    # Composite unique constraint: user can only be in circle once
    __table_args__ = (
        UniqueConstraint("circle_id", "user_id", name="uq_circle_user"),
    )

# backend/app/services/circle_service.py
async def get_shared_gallery(circle_id: uuid.UUID, current_user_id: uuid.UUID, db: AsyncSession):
    """Get all photos from active circle members."""
    # Check if current user is active member
    membership = await db.execute(
        select(CircleMembership)
        .where(
            CircleMembership.circle_id == circle_id,
            CircleMembership.user_id == current_user_id,
            CircleMembership.left_at.is_(None)  # Only active members
        )
    )
    if not membership.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this circle")

    # Get all active members
    members = await db.execute(
        select(CircleMembership.user_id)
        .where(
            CircleMembership.circle_id == circle_id,
            CircleMembership.left_at.is_(None)
        )
    )
    member_ids = [m[0] for m in members.all()]

    # Get all photos from members (only processed photos, not raw captures)
    photos = await db.execute(
        select(Photo)
        .where(
            Photo.user_id.in_(member_ids),
            Photo.upload_status == "processed"  # Only show finished art
        )
        .order_by(Photo.created_at.desc())
    )
    return photos.scalars().all()
```

**Source:** [FastAPI Multi Tenancy | Class Based Solution](https://sayanc20002.medium.com/fastapi-multi-tenancy-bf7c387d07b0), [Building a Multi-Tenant App with FastAPI](https://www.propelauth.com/post/multi-tenant-fastapi-propelauth)

### Pattern 2: Invite Token with Deep Linking

**What:** Generate tamper-proof time-limited invite token using itsdangerous, encode circle_id and inviter_id, create deep link that opens app to join screen, track used tokens in Redis to prevent reuse.

**When to use:** User taps "Invite" button in circle, generates shareable link, recipient opens link and joins circle.

**Example:**
```python
# backend/app/services/invite_service.py
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from app.core.config import settings
import redis

serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt="circle-invite")
redis_client = redis.Redis(host=settings.REDIS_HOST, decode_responses=True)

def generate_invite_token(circle_id: uuid.UUID, inviter_id: uuid.UUID) -> str:
    """Generate secure time-limited invite token."""
    payload = {
        "circle_id": str(circle_id),
        "inviter_id": str(inviter_id),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    token = serializer.dumps(payload)
    return token

def validate_invite_token(token: str, max_age: int = 604800) -> dict:
    """Validate token and extract payload. Max age: 7 days (604800 seconds)."""
    try:
        payload = serializer.loads(token, max_age=max_age)

        # Check if token already used (prevent replay attacks)
        if redis_client.exists(f"used_invite:{token}"):
            raise ValueError("Invite link already used")

        return payload

    except SignatureExpired:
        raise ValueError("Invite link expired (valid for 7 days)")
    except BadSignature:
        raise ValueError("Invalid invite link")

def mark_token_used(token: str):
    """Mark token as used with 30-day TTL."""
    redis_client.setex(f"used_invite:{token}", 2592000, "1")  # 30 days

# backend/app/api/routes/invites.py
@router.post("/circles/{circle_id}/invite")
async def create_invite_link(
    circle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate shareable invite link for circle."""
    # Verify user is member of circle
    membership = await verify_circle_membership(circle_id, current_user.id, db)

    # Generate token
    token = generate_invite_token(circle_id, current_user.id)

    # Create deep link URL (Branch.io format or custom domain)
    invite_url = f"https://irisvue.app.link/invite/{token}"

    return {
        "invite_url": invite_url,
        "token": token,
        "expires_in_days": 7
    }

@router.post("/invites/{token}/accept")
async def accept_invite(
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Accept invite and join circle."""
    # Validate token
    payload = validate_invite_token(token)
    circle_id = uuid.UUID(payload["circle_id"])

    # Check if already member
    existing = await db.execute(
        select(CircleMembership)
        .where(
            CircleMembership.circle_id == circle_id,
            CircleMembership.user_id == current_user.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already a member of this circle")

    # Create membership
    membership = CircleMembership(
        circle_id=circle_id,
        user_id=current_user.id,
        role="member"
    )
    db.add(membership)
    await db.commit()

    # Mark token as used
    mark_token_used(token)

    return {"message": "Successfully joined circle", "circle_id": str(circle_id)}
```

**Mobile deep linking:**
```typescript
// mobile/src/App.tsx
import branch from 'react-native-branch';

export default function App() {
  useEffect(() => {
    // Listen for deep link events
    const unsubscribe = branch.subscribe(({ error, params, uri }) => {
      if (error) {
        console.error('Branch error:', error);
        return;
      }

      // Check if this is an invite link
      if (params['+clicked_branch_link'] && params.token) {
        const inviteToken = params.token;

        // Navigate to join screen
        navigation.navigate('JoinCircle', { token: inviteToken });
      }
    });

    return () => unsubscribe();
  }, []);
}

// mobile/src/screens/Circles/InviteScreen.tsx
async function shareInviteLink(inviteUrl: string) {
  try {
    await Share.open({
      title: 'Join my IrisArt circle',
      message: `I'd like to share my iris art with you! Join my circle: ${inviteUrl}`,
      url: inviteUrl,
    });
  } catch (error) {
    // User cancelled or error
  }
}
```

**Sources:** [JWT in FastAPI, the Secure Way](https://medium.com/@jagan_reddy/jwt-in-fastapi-the-secure-way-refresh-tokens-explained-f7d2d17b1d17), [React Native Branch.io Deep Linking Integration](https://blog.stackademic.com/branch-io-deep-linking-integration-react-native-42de54b98fb4), [React Native Deep Linking That Actually Works](https://medium.com/@nikhithsomasani/react-native-deep-linking-that-actually-works-universal-links-cold-starts-oauth-aced7bffaa56)

### Pattern 3: Relationship-Based Access Control (ReBAC) for Consent

**What:** Per-artwork consent system where users explicitly approve usage of their art in fusion/compositions. ArtworkConsent model tracks (artwork_id, grantor_user_id, grantee_user_id, purpose, granted_at). Before creating fusion, check all source artworks have consent.

**When to use:** User A wants to create fusion using User B's and User C's iris art. System requests consent from B and C, they approve via push notification or in-app modal, fusion proceeds.

**Example:**
```python
# backend/app/models/artwork_consent.py
class ArtworkConsent(Base):
    """Explicit consent for using artwork in fusion/composition."""
    __tablename__ = "artwork_consents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # What artwork is being consented for use
    artwork_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("photos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Who owns the artwork (grantor)
    grantor_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Who is requesting to use it (grantee)
    grantee_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # What circle is this for (optional: consent can be circle-scoped)
    circle_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("circles.id", ondelete="CASCADE"),
        nullable=True
    )

    # Purpose: "fusion", "composition"
    purpose: Mapped[str] = mapped_column(String, nullable=False)

    # Approval status
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)  # pending, granted, denied

    # Timestamps
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    artwork: Mapped["Photo"] = relationship("Photo")
    grantor: Mapped["User"] = relationship("User", foreign_keys=[grantor_user_id])
    grantee: Mapped["User"] = relationship("User", foreign_keys=[grantee_user_id])

# backend/app/services/consent_service.py
async def request_consent(
    artwork_ids: List[uuid.UUID],
    requester_id: uuid.UUID,
    purpose: str,
    circle_id: Optional[uuid.UUID],
    db: AsyncSession
) -> List[ArtworkConsent]:
    """Request consent from artwork owners."""
    consents = []

    for artwork_id in artwork_ids:
        # Get artwork owner
        photo = await db.execute(select(Photo).where(Photo.id == artwork_id))
        photo = photo.scalar_one_or_none()
        if not photo:
            continue

        # Skip if requester owns the artwork (implicit self-consent)
        if photo.user_id == requester_id:
            continue

        # Check if consent already exists
        existing = await db.execute(
            select(ArtworkConsent)
            .where(
                ArtworkConsent.artwork_id == artwork_id,
                ArtworkConsent.grantor_user_id == photo.user_id,
                ArtworkConsent.grantee_user_id == requester_id,
                ArtworkConsent.purpose == purpose,
                ArtworkConsent.status == "granted"
            )
        )
        if existing.scalar_one_or_none():
            continue  # Already have consent

        # Create consent request
        consent = ArtworkConsent(
            artwork_id=artwork_id,
            grantor_user_id=photo.user_id,
            grantee_user_id=requester_id,
            circle_id=circle_id,
            purpose=purpose,
            status="pending"
        )
        db.add(consent)
        consents.append(consent)

    await db.commit()

    # TODO: Send push notifications to grantors

    return consents

async def check_fusion_consent(artwork_ids: List[uuid.UUID], requester_id: uuid.UUID, db: AsyncSession) -> bool:
    """Check if requester has consent for all artworks."""
    for artwork_id in artwork_ids:
        photo = await db.execute(select(Photo).where(Photo.id == artwork_id))
        photo = photo.scalar_one_or_none()

        if photo.user_id == requester_id:
            continue  # Self-owned, implicit consent

        # Check for granted consent
        consent = await db.execute(
            select(ArtworkConsent)
            .where(
                ArtworkConsent.artwork_id == artwork_id,
                ArtworkConsent.grantee_user_id == requester_id,
                ArtworkConsent.purpose == "fusion",
                ArtworkConsent.status == "granted"
            )
        )
        if not consent.scalar_one_or_none():
            return False

    return True
```

**Sources:** [Beyond RBAC: Modern Permission Management for Complex Apps](https://www.osohq.com/learn/beyond-rbac-modern-permission-management-for-complex-apps), [Implementing Role-Based Access Control (RBAC)](https://stenzr.medium.com/implementing-role-based-access-control-rbac-in-a-large-application-5f5cc055cf19)

### Pattern 4: Poisson Image Blending for Seamless Fusion

**What:** Use OpenCV's cv2.seamlessClone to blend multiple iris images using Poisson image editing. Extract iris masks from Phase 3 segmentation, resize to match dimensions, blend using gradient-domain technique for seamless fusion.

**When to use:** User selects 2-3 iris artworks from circle members, requests fusion. Backend Celery task performs Poisson blending, returns fused artwork.

**Example:**
```python
# backend/app/workers/tasks/fusion_blending.py
import cv2
import numpy as np
from PIL import Image
from app.workers.celery_app import celery_app
from app.storage.s3 import load_image_from_s3, upload_to_s3

@celery_app.task(bind=True, queue='high_priority')
def create_fusion_artwork(self, artwork_ids: List[str], fusion_id: str, blend_mode: str = "poisson"):
    """
    Blend multiple iris artworks into seamless fusion using Poisson blending.

    Args:
        artwork_ids: List of Photo IDs to blend
        fusion_id: FusionArtwork ID for result storage
        blend_mode: "poisson" or "alpha" (fallback)
    """
    self.update_state(state='PROGRESS', meta={'step': 'loading', 'progress': 10})

    # Load all source images
    images = []
    masks = []
    for artwork_id in artwork_ids:
        img = load_image_from_s3(artwork_id)
        mask = load_mask_from_s3(artwork_id)  # From Phase 3 segmentation
        images.append(img)
        masks.append(mask)

    self.update_state(state='PROGRESS', meta={'step': 'preparing', 'progress': 30})

    # Resize all to same dimensions (use largest as target)
    max_h = max(img.shape[0] for img in images)
    max_w = max(img.shape[1] for img in images)

    images = [cv2.resize(img, (max_w, max_h)) for img in images]
    masks = [cv2.resize(mask, (max_w, max_h)) for mask in masks]

    # Start with first image as base
    result = images[0].copy()

    self.update_state(state='PROGRESS', meta={'step': 'blending', 'progress': 50})

    # Blend remaining images using Poisson
    for i in range(1, len(images)):
        try:
            # Calculate center for seamless clone
            center = (max_w // 2, max_h // 2)

            # Poisson blending (cv2.NORMAL_CLONE or cv2.MIXED_CLONE)
            result = cv2.seamlessClone(
                images[i],
                result,
                masks[i],
                center,
                cv2.MIXED_CLONE  # MIXED_CLONE blends texture + structure
            )

            progress = 50 + (i / len(images)) * 40
            self.update_state(state='PROGRESS', meta={'step': 'blending', 'progress': progress})

        except cv2.error as e:
            # Fall back to alpha blending if Poisson fails
            self.update_state(state='PROGRESS', meta={'step': 'blending_fallback', 'progress': 70})
            result = alpha_blend_fallback(result, images[i], masks[i])

    self.update_state(state='PROGRESS', meta={'step': 'saving', 'progress': 90})

    # Upload result
    result_url = upload_to_s3(result, f"fusion/{fusion_id}.jpg")

    return {
        'progress': 100,
        'result_url': result_url,
        'blend_mode': 'poisson',
        'source_count': len(artwork_ids)
    }

def alpha_blend_fallback(base: np.ndarray, overlay: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Simple alpha blending fallback if Poisson fails."""
    # Normalize mask to 0-1
    alpha = mask.astype(float) / 255.0
    if len(alpha.shape) == 2:
        alpha = np.stack([alpha] * 3, axis=2)

    # Blend: result = base * (1 - alpha) + overlay * alpha
    blended = (base * (1 - alpha) + overlay * alpha).astype(np.uint8)
    return blended
```

**Sources:** [Poisson Image Blending on OpenCV](https://gist.github.com/iKrishneel/509116cb3b88c69e242a68a17bad8e3a), [Seamless Cloning using OpenCV](https://learnopencv.com/seamless-cloning-using-opencv-python-cpp/), [OpenCV: Seamless Cloning](https://docs.opencv.org/4.x/df/da0/group__photo__clone.html)

### Pattern 5: Side-by-Side Composition with Grid Layout

**What:** Use OpenCV hconcat/vconcat to create grid layouts (2x1, 2x2, 3x1) of iris artworks. Resize to match dimensions, pad if needed, concatenate horizontally then vertically.

**When to use:** User selects 2-4 artworks for side-by-side composition. Simpler than fusion, instant preview on mobile, no consent needed (visual arrangement, not blending).

**Example:**
```python
# backend/app/workers/tasks/composition.py
import cv2
import numpy as np

def create_side_by_side_composition(
    artwork_ids: List[str],
    layout: str = "horizontal"  # "horizontal", "vertical", "grid_2x2"
) -> np.ndarray:
    """Create side-by-side composition of artworks."""
    # Load images
    images = [load_image_from_s3(aid) for aid in artwork_ids]

    # Determine target dimensions (match to smallest to avoid quality loss)
    min_h = min(img.shape[0] for img in images)
    min_w = min(img.shape[1] for img in images)

    # Resize all to same dimensions
    images = [cv2.resize(img, (min_w, min_h)) for img in images]

    if layout == "horizontal":
        # Side by side: [img1 | img2 | img3]
        result = cv2.hconcat(images)

    elif layout == "vertical":
        # Stacked: [img1]
        #          [img2]
        #          [img3]
        result = cv2.vconcat(images)

    elif layout == "grid_2x2":
        # Grid:  [img1 | img2]
        #        [img3 | img4]
        if len(images) < 4:
            # Pad with black images
            while len(images) < 4:
                images.append(np.zeros_like(images[0]))

        # Create rows
        row1 = cv2.hconcat(images[:2])
        row2 = cv2.hconcat(images[2:4])

        # Stack rows
        result = cv2.vconcat([row1, row2])

    return result
```

**Sources:** [Concatenate images with Python, OpenCV (hconcat, vconcat)](https://note.nkmk.me/en/python-opencv-hconcat-vconcat-np-tile/), [Create a Collage of Images with NumPy and OpenCV](https://www.includehelp.com/python/create-a-collage-of-images-with-the-help-of-numpy-and-python-opencv-cv2.aspx)

### Pattern 6: Soft Delete with Hard Delete Compliance

**What:** Soft delete circle memberships by setting `left_at` timestamp, preserving audit trail for "who was in circle when fusion X was created". Hard delete user records on GDPR erasure request, cascading to all memberships, consents, and artworks.

**When to use:** User leaves circle (soft delete membership), User requests account deletion (hard delete all data).

**Example:**
```python
# backend/app/services/circle_service.py
async def leave_circle(circle_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession):
    """Soft delete membership: user leaves circle."""
    membership = await db.execute(
        select(CircleMembership)
        .where(
            CircleMembership.circle_id == circle_id,
            CircleMembership.user_id == user_id,
            CircleMembership.left_at.is_(None)
        )
    )
    membership = membership.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=404, detail="Not a member of this circle")

    # Soft delete: set left_at timestamp
    membership.left_at = datetime.now(timezone.utc)
    await db.commit()

    # User's artworks no longer visible in shared gallery (query filters left_at IS NULL)
    # But fusion artworks created before leaving remain (audit trail preserved)

# backend/app/services/user_service.py (from Phase 1, extended)
async def delete_user_account_gdpr(user_id: uuid.UUID, db: AsyncSession):
    """
    Hard delete user and all associated data per GDPR Article 17.
    CASCADE deletes will remove:
    - CircleMemberships (user removed from all circles)
    - ArtworkConsents (both as grantor and grantee)
    - Photos (all iris images)
    - FusionArtworks (owned fusions deleted)
    - ProcessingJobs, StyleJobs, ExportJobs
    """
    # 1. Delete S3 objects first (before DB cascade)
    photos = await db.execute(select(Photo).where(Photo.user_id == user_id))
    for photo in photos.scalars().all():
        delete_from_s3(photo.s3_key)
        if photo.thumbnail_s3_key:
            delete_from_s3(photo.thumbnail_s3_key)

    # 2. Delete fusion artworks from S3
    fusions = await db.execute(select(FusionArtwork).where(FusionArtwork.creator_id == user_id))
    for fusion in fusions.scalars().all():
        delete_from_s3(fusion.s3_key)

    # 3. Hard delete user (CASCADE handles all foreign keys)
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()

    # Note: If fusion artwork included this user's art (but was created by someone else),
    # that fusion artwork remains (GDPR allows keeping "sufficiently anonymized" derivatives)
```

**Sources:** [Soft deletion with PostgreSQL](https://evilmartians.com/chronicles/soft-deletion-with-postgresql-but-with-logic-on-the-database), [The Delete Button Dilemma: When to Soft Delete vs Hard Delete](https://dev.to/akarshan/the-delete-button-dilemma-when-to-soft-delete-vs-hard-delete-3a0i), [SQLAlchemy Cascading Deletes](https://dev.to/zchtodd/sqlalchemy-cascading-deletes-8hk)

### Anti-Patterns to Avoid

- **Global "shareable" flag instead of ReBAC**: Simple boolean doesn't allow per-user, per-artwork, per-purpose consent
- **Storing invite tokens in database**: Stateless signed tokens (itsdangerous) avoid DB lookup overhead and are tamper-proof
- **Hard delete only**: Loses audit trail for "who was in circle when", makes debugging impossible, breaks fusion metadata
- **No expiration on invite links**: Permanent links can be shared indefinitely, security risk if member later removed
- **Client-side only consent**: User could bypass consent checks via API manipulation, enforce server-side
- **Synchronous Poisson blending in API**: Takes 5-15 seconds, blocks request, use Celery async task
- **No permission check on shared gallery**: Any user could query circle gallery by guessing circle_id, must verify membership
- **Blending without masks**: Blending full rectangular images creates ugly borders, use iris masks from Phase 3
- **Not handling consent withdrawal**: User consents, fusion created, user later revokes consent — fusion should be marked "consent withdrawn" and hidden

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Secure time-limited tokens | Custom JWT or UUID expiration | itsdangerous URLSafeTimedSerializer | Built-in expiration, tamper-proof signing, no DB lookup, already in Phase 1 stack |
| Deep linking with attribution | Manual URL scheme + universal links config | Branch.io React Native SDK | Deferred deep links, attribution, analytics, simpler setup than manual universal links |
| Poisson image blending | Custom gradient-domain solver | cv2.seamlessClone (OpenCV) | Optimized C++ implementation, handles edge cases, multiple blend modes (NORMAL_CLONE, MIXED_CLONE) |
| Multi-user permissions | Custom role checks in every route | Dependency injection with permission decorators | Centralized logic, reusable, type-safe, FastAPI-native pattern |
| Invite link sharing | Custom share UI | react-native-share | Cross-platform share sheet, SMS, WhatsApp, email, clipboard fallback |
| Circle membership queries | Manual LEFT JOIN with NULL checks | SQLAlchemy relationship with soft delete filter | Handles cascade deletes, query optimization, prevents N+1 queries |
| Consent notifications | Custom push implementation | Firebase Cloud Messaging (FCM) | Cross-platform, delivery guarantees, background notifications, already in Phase 3 |
| Image composition grids | Manual pixel copying and padding | cv2.hconcat/vconcat with numpy | Vectorized operations, handles dimension mismatch, optimized |

**Key insight:** Social features introduce complex multi-user interactions with race conditions, permission edge cases, and data consistency challenges. Use battle-tested libraries for authentication, permissions, and image processing to avoid weeks debugging concurrency issues and edge cases.

## Common Pitfalls

### Pitfall 1: Race Condition in Concurrent Consent Requests

**What goes wrong:** User A requests fusion using User B's art. User B denies consent. Simultaneously, User C approves fusion using same art. Fusion proceeds even though B denied. Consent state is inconsistent.

**Why it happens:** Consent checks are not atomic. Between checking "all consents granted" and creating fusion, consent status can change.

**How to avoid:**
1. Use database transactions with SELECT FOR UPDATE to lock consent records during check
2. Check consent status again after acquiring fusion creation lock
3. Store snapshot of consent states with fusion metadata for audit trail
4. Use optimistic locking with version fields on consent records

**Warning signs:** Fusion artworks created with "pending" or "denied" consents in database. User complaints about art being used without permission. Consent table shows inconsistent timestamps.

### Pitfall 2: Memory Exhaustion from Large Fusion Tasks

**What goes wrong:** User requests fusion of 3x high-res artworks (12MP each). Poisson blending loads all images into memory (3 * 12MP * 3 channels * 4 bytes = 432MB), OOM on worker, task fails.

**Why it happens:** Poisson blending is memory-intensive, scales with image dimensions squared. Concurrent fusion tasks on same worker exhaust RAM.

**How to avoid:**
1. Resize images to 2048x2048 max before fusion (HD but not full-res)
2. Use Celery worker with exclusive queue for fusion tasks (prevent concurrent OOM)
3. Set memory limit on fusion workers (4GB RAM minimum)
4. Implement fallback to alpha blending if Poisson fails with OOM

**Warning signs:** Worker crashes with MemoryError or OOM killed by system. Fusion tasks fail intermittently under load. System swap usage spikes during fusion.

### Pitfall 3: Invite Link Leakage After Member Removal

**What goes wrong:** User A invites User B via link. User B joins, then gets removed by circle owner. Invite link still works, User B re-joins using same link. Removal ineffective.

**Why it happens:** Invite tokens are time-limited (7 days) but not tied to membership state. Removing member doesn't invalidate their invite token.

**How to avoid:**
1. Mark invite token as used when user joins (prevents reuse)
2. Check if user was previously removed from circle before allowing re-join
3. Store removal reason in soft-deleted membership (blocked, left voluntarily)
4. Require new invite if user was removed by owner (not self-leave)

**Warning signs:** Users report re-joining circles after removal. Membership logs show same user joining multiple times. Invite token tracking shows low "used" percentage.

### Pitfall 4: Orphaned Fusion Artworks After User Leaves

**What goes wrong:** User A creates fusion using Users B, C, D's art. User B leaves circle. Fusion artwork still visible in circle gallery, but User B's art is no longer available. Metadata inconsistent.

**Why it happens:** Fusion artwork is owned by creator, not tied to circle membership. Leaving circle doesn't cascade to fusion artworks.

**How to avoid:**
1. Store source artwork IDs with fusion metadata
2. Query source artwork availability when displaying fusion
3. Show "partial fusion" badge if some source art unavailable
4. Option 1: Hide fusion if any source art unavailable
5. Option 2: Show fusion with disclaimer "includes unavailable artwork"

**Warning signs:** Fusion artworks show in gallery but source art missing. User complaints about seeing fusion of ex-member's art. Database foreign key violations when querying fusion sources.

### Pitfall 5: No Rate Limiting on Invite Generation

**What goes wrong:** User spams invite link generation, creates 100+ tokens in 1 minute. Redis fills with unused tokens, DDoS vector if attacker automates requests.

**Why it happens:** No rate limit on invite generation endpoint. Tokens are cheap to generate, expensive to store and track.

**How to avoid:**
1. Rate limit invite generation: 5 invites per circle per hour
2. Invalidate old unused tokens after 24 hours
3. Track invite token generation in Redis with expiry
4. Show existing invite link instead of generating new one if recent invite exists

**Warning signs:** High memory usage in Redis for invite token storage. User complaints about "invite link already used" errors. API logs show burst of invite generation from single user.

### Pitfall 6: Poisson Blending Artifacts on Low-Quality Masks

**What goes wrong:** Phase 3 segmentation produced imperfect mask (jagged edges, holes). Poisson blending uses this mask, creates visible seams and artifacts in fusion. Result looks worse than alpha blending.

**Why it happens:** Poisson blending assumes clean mask boundaries. Garbage in, garbage out. Low-quality input from Phase 3 propagates to Phase 5.

**How to avoid:**
1. Smooth mask edges with Gaussian blur before Poisson blending
2. Apply morphological operations (erosion, dilation) to clean mask
3. Validate mask quality before fusion (check coverage, edge smoothness)
4. Fall back to alpha blending if mask quality below threshold
5. Show preview to user, allow "try again" if artifacts visible

**Warning signs:** Fusion artworks have visible seams, color bleeding, or jagged edges. User complaints about low-quality fusion. Poisson blending fails more often than succeeds.

### Pitfall 7: Deep Link Not Working on Cold Start

**What goes wrong:** User taps invite link on iOS. App not installed, redirects to App Store, user installs app, opens app, but invite link data is lost. User must re-tap link after install.

**Why it happens:** Standard deep links don't support deferred deep linking (storing invite data through app install). Universal Links (iOS) and App Links (Android) require server setup.

**How to avoid:**
1. Use Branch.io for deferred deep linking (stores invite token through install)
2. Configure Branch.io with Apple App Site Association (AASA) and Android App Links
3. Test full flow: link tap → store visit → install → open → invite accepted
4. Fallback: show "paste invite link" screen if deep link data missing

**Warning signs:** Users report "invite link didn't work" after fresh install. Analytics show high deep link failure rate. iOS users complain more than Android (universal links are finicky).

### Pitfall 8: Consent Modal Spam on Gallery Browse

**What goes wrong:** User browses circle gallery, taps on artwork owned by another member. App shows consent modal "Allow User A to view your artwork?". Modal appears for every artwork tap. User frustrated.

**Why it happens:** Overzealous consent checking. Viewing in shared gallery should be implicitly consented by circle membership. Consent only needed for fusion/composition creation.

**How to avoid:**
1. Implicit consent: circle membership = view all members' art in shared gallery
2. Explicit consent only for: (1) using art in fusion, (2) using art in composition, (3) sharing outside circle
3. Show consent request when user taps "Create Fusion" or "Add to Composition", not on view
4. Store consent grants, reuse for future fusions with same members

**Warning signs:** User complaints about too many consent dialogs. High consent denial rate. Users leave circles due to annoying UX. Analytics show modal shown >10 times per user session.

### Pitfall 9: Circle Owner Can't Remove Themselves

**What goes wrong:** Circle owner (creator) wants to leave circle, but "Leave Circle" button is disabled. No one else has owner role. Circle becomes orphaned, no one can delete it.

**Why it happens:** UI logic prevents owner from leaving (assumption: owner must always exist). No transfer ownership flow.

**How to avoid:**
1. Allow owner to leave if (a) other members exist and (b) ownership transferred to another member
2. Show "Transfer Ownership" modal before allowing owner to leave
3. If owner is last member, delete circle entirely (no orphaned circles)
4. Alternative: promote oldest remaining member to owner on owner departure

**Warning signs:** Orphaned circles in database with zero active members. Owner complaints about being "stuck" in circle. Database foreign key violations on circle queries.

### Pitfall 10: Fusion Task Never Completes Under Load

**What goes wrong:** User submits fusion request, task status shows "pending" for 20+ minutes, eventually times out. Server logs show Celery worker stuck on previous fusion task.

**Why it happens:** Poisson blending is CPU-intensive, single-threaded. Worker processes one fusion at a time. Queue backs up under load. No timeout on individual tasks.

**How to avoid:**
1. Set task timeout: `@celery_app.task(time_limit=180)` (3 minutes max)
2. Use dedicated fusion worker pool with multiple workers (4-8 workers for parallelism)
3. Show estimated wait time to user based on queue depth
4. Fall back to alpha blending if queue depth >10 (faster, lower quality)
5. Monitor queue depth, auto-scale workers if queue grows

**Warning signs:** Fusion tasks timeout frequently. Queue depth grows to 50+ tasks. Worker CPU usage at 100% for extended periods. User complaints about "processing forever".

## Code Examples

Verified patterns from official sources and prior phases:

### Complete Circle Creation and Invitation Flow

```python
# backend/app/api/routes/circles.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.circle import Circle, CircleMembership
from app.services.invite_service import generate_invite_token

router = APIRouter()

@router.post("/circles")
async def create_circle(
    name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new circle with current user as owner."""
    # Create circle
    circle = Circle(
        name=name,
        created_by=current_user.id
    )
    db.add(circle)
    await db.flush()  # Get circle.id before creating membership

    # Add creator as owner member
    membership = CircleMembership(
        circle_id=circle.id,
        user_id=current_user.id,
        role="owner"
    )
    db.add(membership)
    await db.commit()
    await db.refresh(circle)

    return {
        "id": str(circle.id),
        "name": circle.name,
        "role": "owner",
        "created_at": circle.created_at.isoformat()
    }

@router.get("/circles/{circle_id}/members")
async def get_circle_members(
    circle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all active members of circle."""
    # Verify current user is member
    membership = await db.execute(
        select(CircleMembership)
        .where(
            CircleMembership.circle_id == circle_id,
            CircleMembership.user_id == current_user.id,
            CircleMembership.left_at.is_(None)
        )
    )
    if not membership.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this circle")

    # Get all active members
    members = await db.execute(
        select(CircleMembership, User)
        .join(User, CircleMembership.user_id == User.id)
        .where(
            CircleMembership.circle_id == circle_id,
            CircleMembership.left_at.is_(None)
        )
        .order_by(CircleMembership.joined_at)
    )

    return [
        {
            "user_id": str(member.user_id),
            "email": user.email,
            "role": member.role,
            "joined_at": member.joined_at.isoformat()
        }
        for member, user in members.all()
    ]
```

### Fusion Creation with Consent Verification

```python
# backend/app/api/routes/fusion.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.fusion_artwork import FusionArtwork
from app.services.consent_service import check_fusion_consent
from app.workers.tasks.fusion_blending import create_fusion_artwork

router = APIRouter()

@router.post("/fusion")
async def create_fusion(
    artwork_ids: List[uuid.UUID],
    circle_id: Optional[uuid.UUID],
    blend_mode: str = "poisson",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create fusion artwork from multiple iris images."""
    # Validate inputs
    if len(artwork_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 artworks for fusion")
    if len(artwork_ids) > 4:
        raise HTTPException(status_code=400, detail="Maximum 4 artworks per fusion")

    # Check consent for all artworks
    has_consent = await check_fusion_consent(artwork_ids, current_user.id, db)
    if not has_consent:
        # Return list of artworks needing consent
        pending_consents = await get_pending_consents(artwork_ids, current_user.id, db)
        return {
            "status": "consent_required",
            "pending_consents": pending_consents,
            "message": "Consent required from artwork owners"
        }

    # Create fusion record
    fusion = FusionArtwork(
        creator_id=current_user.id,
        circle_id=circle_id,
        source_artwork_ids=artwork_ids,  # JSON column
        blend_mode=blend_mode,
        status="pending"
    )
    db.add(fusion)
    await db.commit()
    await db.refresh(fusion)

    # Submit Celery task
    task = create_fusion_artwork.apply_async(
        args=[
            [str(aid) for aid in artwork_ids],
            str(fusion.id),
            blend_mode
        ],
        task_id=str(fusion.id),
        priority=9
    )

    return {
        "fusion_id": str(fusion.id),
        "status": "pending",
        "websocket_url": f"/ws/jobs/{fusion.id}"
    }
```

### React Native Circle Gallery with Consent Flow

```typescript
// mobile/src/screens/Circles/SharedGalleryScreen.tsx
import React, { useEffect, useState } from 'react';
import { View, FlatList, ActivityIndicator } from 'react-native';
import { useCircleGallery } from '@/hooks/useCircleGallery';
import { useNavigation } from '@react-navigation/native';
import ArtworkCard from '@/components/Artworks/ArtworkCard';

export default function SharedGalleryScreen({ route }) {
  const { circleId } = route.params;
  const navigation = useNavigation();
  const { artworks, loading, error } = useCircleGallery(circleId);
  const [selectedArtworks, setSelectedArtworks] = useState<string[]>([]);

  const toggleSelection = (artworkId: string) => {
    setSelectedArtworks(prev =>
      prev.includes(artworkId)
        ? prev.filter(id => id !== artworkId)
        : [...prev, artworkId]
    );
  };

  const handleCreateFusion = async () => {
    if (selectedArtworks.length < 2) {
      Alert.alert('Selection Required', 'Select at least 2 artworks for fusion');
      return;
    }

    // Navigate to fusion builder (will check consent there)
    navigation.navigate('FusionBuilder', {
      circleId,
      artworkIds: selectedArtworks
    });
  };

  if (loading) return <ActivityIndicator />;
  if (error) return <Text>Error: {error}</Text>;

  return (
    <View style={styles.container}>
      <FlatList
        data={artworks}
        numColumns={2}
        renderItem={({ item }) => (
          <ArtworkCard
            artwork={item}
            isSelected={selectedArtworks.includes(item.id)}
            onPress={() => toggleSelection(item.id)}
            showOwner={true}  // Show which circle member owns this art
          />
        )}
        keyExtractor={item => item.id}
      />

      {selectedArtworks.length >= 2 && (
        <Button title="Create Fusion" onPress={handleCreateFusion} />
      )}
    </View>
  );
}

// mobile/src/screens/Circles/FusionBuilderScreen.tsx
export default function FusionBuilderScreen({ route }) {
  const { circleId, artworkIds } = route.params;
  const [consentStatus, setConsentStatus] = useState<'checking' | 'granted' | 'pending'>('checking');
  const [pendingConsents, setPendingConsents] = useState<any[]>([]);

  useEffect(() => {
    checkAndRequestConsent();
  }, []);

  const checkAndRequestConsent = async () => {
    try {
      const response = await api.post('/fusion', {
        artwork_ids: artworkIds,
        circle_id: circleId,
        blend_mode: 'poisson'
      });

      if (response.data.status === 'consent_required') {
        setConsentStatus('pending');
        setPendingConsents(response.data.pending_consents);
      } else {
        // Fusion task submitted
        setConsentStatus('granted');
        navigation.navigate('FusionProgress', { fusionId: response.data.fusion_id });
      }
    } catch (error) {
      Alert.alert('Error', error.message);
    }
  };

  if (consentStatus === 'checking') {
    return <ActivityIndicator />;
  }

  if (consentStatus === 'pending') {
    return (
      <View>
        <Text>Waiting for consent approval...</Text>
        <FlatList
          data={pendingConsents}
          renderItem={({ item }) => (
            <View>
              <Text>{item.owner_email} - Pending</Text>
            </View>
          )}
        />
      </View>
    );
  }

  return null;
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Global user permissions | Relationship-based access (ReBAC) | 2024-2025 | Social apps need granular per-user, per-resource permissions vs role-based |
| Manual deep link config | Branch.io SDK for attribution | 2023+ | Deferred deep links, universal link setup, attribution analytics vs manual config |
| Alpha blending only | Poisson blending for seamless fusion | 2010+ (mature) | Gradient-domain blending eliminates seams vs simple alpha transparency |
| Stateful invite tokens in DB | Stateless signed tokens (itsdangerous) | 2023+ | No DB lookup, tamper-proof, time-limited vs UUID in database |
| Hard delete only | Soft delete with audit trail | 2024+ | Preserve "who was member when" for legal/debugging vs clean erasure |
| Manual share implementation | react-native-share library | 2020+ | Cross-platform share sheet, SMS/WhatsApp integration vs custom UI |
| RBAC only | RBAC + ReBAC hybrid | 2025-2026 | Social features need relationship-based permissions (friend-of-friend) vs flat roles |

**Deprecated/outdated:**
- **react-native-social-share**: Deprecated, use react-native-share (actively maintained)
- **Manual universal links setup**: Brittle, use Branch.io or similar service
- **Global "public" flag for all artworks**: Too coarse, use per-user consent grants
- **Synchronous image blending in API**: Blocks request for 10-30s, use async Celery tasks

## Open Questions

### 1. Fusion Artwork Ownership After Circle Dissolution

**What we know:** User A creates fusion using Users B, C, D's art in Circle X. Later, Circle X is deleted by owner.

**What's unclear:** Who owns the fusion artwork? Does it remain in A's personal gallery? Can it be re-shared in new circles? Does deletion cascade to fusion artworks?

**Recommendation:** Fusion artwork ownership stays with creator (User A) even if circle deleted. Fusion remains in creator's personal gallery. Source consent records preserved (audit trail). Re-sharing in new circle requires fresh consent from source artwork owners.

**Confidence:** MEDIUM - Depends on product decision about fusion portability vs circle-scoped content.

### 2. Consent Granularity for Compositions

**What we know:** User A wants to create side-by-side composition (not fusion/blending). Uses Users B, C's art.

**What's unclear:** Does side-by-side composition need same consent as fusion? Less consent (just visual arrangement)? No consent (circle membership implies permission)?

**Recommendation:** Start with same consent requirement as fusion (explicit approval). If user feedback indicates too many consent requests, relax to implicit consent for side-by-side (circle membership = view + arrange). Fusion still requires explicit consent (actual blending/modification).

**Confidence:** LOW - Depends on user expectations and legal review of "derivative work" vs "arrangement".

### 3. Maximum Circle Size

**What we know:** Circles are for couples, families, friend groups.

**What's unclear:** What's the practical upper limit? 5 members? 10? 50? At what size does shared gallery become unmanageable?

**Recommendation:** Start with 10-member limit per circle. Monitor usage analytics (average circle size, active member count). If users request larger circles, increase limit to 25 with warning "large circles may have slower galleries". Optimize shared gallery queries for 10-25 members.

**Confidence:** MEDIUM - Social graph research shows 5-15 is typical "close circle" size.

### 4. Invite Link Expiration Duration

**What we know:** Invite tokens have time-limited expiration (7 days recommended).

**What's unclear:** Is 7 days right balance between security and usability? Too short (user doesn't check phone for 8 days)? Too long (removed member re-joins after 6 days)?

**Recommendation:** Use 7 days as default, make configurable by circle owner (options: 1 day, 7 days, 30 days, never expire). Track invite acceptance time metrics to find optimal default.

**Confidence:** MEDIUM - Industry standard for invite links is 7-30 days, depends on use case urgency.

### 5. Fusion Quality vs Processing Time Tradeoff

**What we know:** Poisson blending is slow (5-15s) but high quality. Alpha blending is fast (<1s) but lower quality.

**What's unclear:** Should app always use Poisson? Offer user choice? Auto-select based on device/network?

**Recommendation:** Default to Poisson blending for all fusions (quality matters for iris art). Show estimated wait time (5-15 seconds). Offer "Quick Blend (Preview)" option with alpha blending for instant preview, then user can upgrade to Poisson if satisfied with layout.

**Confidence:** MEDIUM - User tolerance for wait time varies, A/B test needed.

### 6. Circle Naming Constraints

**What we know:** Users name circles ("My Family", "Couple Art", "Friends").

**What's unclear:** Any restrictions on names? Max length? Profanity filter? Uniqueness (per user or global)?

**Recommendation:** Max length 50 characters, no uniqueness constraint (users can have multiple "Family" circles), basic profanity filter (reject offensive words), allow emoji. Store normalized name for search (lowercase, trim whitespace).

**Confidence:** HIGH - Standard social app naming patterns.

## Sources

### Primary (HIGH confidence)

- [FastAPI Multi Tenancy | Class Based Solution](https://sayanc20002.medium.com/fastapi-multi-tenancy-bf7c387d07b0) - Multi-tenancy patterns with SQLAlchemy
- [Building a Multi-Tenant App with FastAPI](https://www.propelauth.com/post/multi-tenant-fastapi-propelauth) - Circle-as-tenant model
- [SQLAlchemy Cascading Deletes](https://dev.to/zchtodd/sqlalchemy-cascading-deletes-8hk) - CASCADE policies for cleanup
- [Cascades — SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/orm/cascades.html) - Official cascade documentation
- [Soft deletion with PostgreSQL](https://evilmartians.com/chronicles/soft-deletion-with-postgresql-but-with-logic-on-the-database) - Soft delete patterns with database logic
- [The Delete Button Dilemma: When to Soft Delete vs Hard Delete](https://dev.to/akarshan/the-delete-button-dilemma-when-to-soft-delete-vs-hard-delete-3a0i) - GDPR compliance considerations
- [JWT in FastAPI, the Secure Way (Refresh Tokens Explained)](https://medium.com/@jagan_reddy/jwt-in-fastapi-the-secure-way-refresh-tokens-explained-f7d2d17b1d17) - Secure token patterns
- [FastAPI Refresh Tokens: Securely Manage User Sessions Beyond Expiry](https://medium.com/@bhagyarana80/fastapi-refresh-tokens-securely-manage-user-sessions-beyond-expiry-9f937cfb59c0) - Token expiration
- [OpenCV: Seamless Cloning](https://docs.opencv.org/4.x/df/da0/group__photo__clone.html) - Official Poisson blending documentation
- [Seamless Cloning using OpenCV](https://learnopencv.com/seamless-cloning-using-opencv-python-cpp/) - Practical Poisson blending tutorial
- [Poisson Image Blending on OpenCV](https://gist.github.com/iKrishneel/509116cb3b88c69e242a68a17bad8e3a) - Implementation example
- [Concatenate images with Python, OpenCV (hconcat, vconcat)](https://note.nkmk.me/en/python-opencv-hconcat-vconcat-np-tile/) - Grid layout patterns
- [React Native Branch.io Deep Linking Integration](https://blog.stackademic.com/branch-io-deep-linking-integration-react-native-42de54b98fb4) - Branch.io setup guide
- [React Native Deep Linking That Actually Works](https://medium.com/@nikhithsomasani/react-native-deep-linking-that-actually-works-universal-links-cold-starts-oauth-aced7bffaa56) - Universal links and deferred deep links
- [React Native Overview - Branch Help Center](https://help.branch.io/developers-hub/docs/react-native) - Official Branch.io documentation
- [Beyond RBAC: Modern Permission Management for Complex Apps](https://www.osohq.com/learn/beyond-rbac-modern-permission-management-for-complex-apps) - ReBAC patterns
- [Implementing Role-Based Access Control (RBAC)](https://stenzr.medium.com/implementing-role-based-access-control-rbac-in-a-large-application-5f5cc055cf19) - RBAC + ReBAC hybrid

### Secondary (MEDIUM confidence)

- [React Native Google Mobile Ads European User Consent](https://docs.page/invertase/react-native-google-mobile-ads/european-user-consent) - Consent UI patterns
- [ConsentManager SDK React Native Integration](https://help.consentmanager.net/books/cmp/page/reactnative-1-consentmanager-sdk-integration-9b0) - Consent management
- [How to Build WebSocket Servers with FastAPI and Redis](https://oneuptime.com/blog/post/2026-01-25-websocket-servers-fastapi-redis/view) - Real-time updates for consent notifications
- [FastAPI WebSockets + React: Real-Time Features](https://medium.com/@suganthi2496/fastapi-websockets-react-real-time-features-for-your-modern-apps-b8042a10fd90) - WebSocket patterns
- [Financial Data Consent Trends: Biometric Data and Dynamic Permissions in 2025](https://secureprivacy.ai/blog/financial-data-consent-trends-biometric-data-dynamic-permisions-2025) - Consent compliance trends
- [Privacy Laws 2026: Global Updates & Compliance Guide](https://secureprivacy.ai/blog/privacy-laws-2026) - GDPR/BIPA/CCPA updates
- [Alpha Blending Using OpenCV](https://learnopencv.com/alpha-blending-using-opencv-cpp-python/) - Fallback blending technique
- [Create a Collage of Images with NumPy and OpenCV](https://www.includehelp.com/python/create-a-collage-of-images-with-the-help-of-numpy-and-python-opencv-cv2.aspx) - Composition grids

### Tertiary (LOW confidence - marked for validation)

- [React Native reward referrals](https://www.educative.io/answers/react-native-reward-referrals) - Invite attribution patterns (not industry-standard, needs validation)
- [Universal & Deep Links: 2026 Complete Guide](https://prototyp.digital/blog/universal-links-deep-linking-2026) - Deep linking trends (blog post, not official)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All core libraries (FastAPI, SQLAlchemy, OpenCV, React Native) proven in prior phases
- Architecture: HIGH - Multi-tenancy, ReBAC, soft delete are well-documented patterns with production examples
- Pitfalls: HIGH - Race conditions, memory issues, consent flows are common social feature challenges
- Poisson blending: HIGH - OpenCV seamlessClone is mature (2010+), widely used, performance characteristics known
- Branch.io integration: MEDIUM - Industry standard but setup complexity varies, needs testing
- Consent granularity: LOW - Product decision needed (explicit vs implicit consent for compositions)

**Research date:** 2026-02-09
**Valid until:** 2026-03-09 (30 days — social feature patterns stable, privacy laws evolving slowly)

**Notes for planner:**
- All core libraries (FastAPI, SQLAlchemy, OpenCV, React Native) already in stack from Phases 1-4
- Branch.io is only new significant dependency (deep linking with attribution)
- Multi-tenancy (circles) and ReBAC (consent) are complex but well-documented patterns
- Poisson blending is CPU-intensive (5-15s) but mature, fall back to alpha blending if needed
- Soft delete for memberships, hard delete for GDPR compliance — both needed for audit trail + privacy
- Consent UX is critical — too many prompts will frustrate users, too few will violate expectations
- Test deep linking thoroughly on iOS (universal links finicky) and Android (app links more reliable)
- Consider push notifications for consent requests (not researched here, may need FCM integration)
