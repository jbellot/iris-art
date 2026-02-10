# Phase 6: Payments and Freemium - Research

**Researched:** 2026-02-10
**Domain:** In-app purchases, payment processing, rate limiting, freemium monetization
**Confidence:** HIGH

## Summary

Phase 6 implements monetization through RevenueCat-powered in-app purchases, enabling users to purchase HD exports (4.99 EUR per image), unlock premium styles, and enforcing rate limits for free users (3 AI-processed images per month). RevenueCat is the industry-standard solution for cross-platform IAP management, abstracting iOS StoreKit and Android Play Billing complexities while providing server-side receipt validation and webhook notifications. The implementation requires careful coordination between mobile SDK integration, backend webhook handling, database-tracked usage limits, and thoughtful UI/UX for feature gates and limit messaging.

**Primary recommendation:** Use RevenueCat (react-native-purchases v9.7.6) for cross-platform IAP with server-side webhook validation, implement Redis-based rate limiting with database-persisted monthly quotas, and design non-intrusive feature gates that time upsell prompts at natural decision points (e.g., when user completes an AI generation and wants to export).

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react-native-purchases | 9.7.6 | RevenueCat React Native SDK | Official RevenueCat SDK, wraps StoreKit/Play Billing, handles receipt validation, 9.7k+ GitHub stars |
| RevenueCat Backend | REST API v1 | Server-side receipt validation and subscriber status | Industry standard for IAP backend, prevents fraud, webhook notifications |
| fastapi-limiter | 0.1.6 | Redis-based rate limiting for FastAPI | Lua-script rate limiting with FastAPI integration, per-user limits |
| redis | 4.5.4+ | Rate limit state storage | Already in project stack for Celery, reusable for rate limiting |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| slowapi | 0.1.9 | Alternative rate limiter (SlowAPI) | Simpler than fastapi-limiter, uses flask-limiter patterns |
| httpx | 0.24.0+ | RevenueCat REST API calls | Already in project (backend/requirements.txt), async HTTP client |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| RevenueCat | react-native-iap (direct) | More control but requires custom backend validation, fraud prevention, cross-platform receipt handling - massively more complex |
| fastapi-limiter | Custom Token Bucket | Full control but must handle Redis Lua scripts, race conditions, distributed locking - not worth reinventing |
| RevenueCat Webhooks | Polling REST API | Simpler but introduces lag in payment verification, increases API quota usage, misses real-time events |

**Installation:**

Backend:
```bash
# No new packages needed - httpx and redis already installed
```

Mobile:
```bash
cd mobile
npm install --save react-native-purchases@9.7.6
```

Platform-specific setup (iOS):
- Enable In-App Purchase capability in Xcode (Project Target → Signing & Capabilities)
- Add products to App Store Connect

Platform-specific setup (Android):
- Add BILLING permission to AndroidManifest.xml
- Set Activity launchMode to "standard" or "singleTop"
- Add products to Google Play Console

## Architecture Patterns

### Recommended Project Structure

Backend:
```
backend/app/
├── models/
│   ├── purchase.py           # Purchase model (transaction records)
│   └── user.py               # Add: premium_until, monthly_ai_count, last_reset_month
├── schemas/
│   └── purchases.py          # Purchase request/response schemas
├── services/
│   ├── purchases.py          # RevenueCat integration, payment verification
│   ├── rate_limiting.py      # Usage tracking, monthly quota checks
│   └── entitlements.py       # Premium feature access logic
├── api/
│   ├── routes/
│   │   ├── purchases.py      # Purchase endpoints (request HD export payment)
│   │   └── webhooks.py       # RevenueCat webhook receiver
│   └── dependencies/
│       └── rate_limit.py     # Rate limit dependency for routes
├── core/
│   └── config.py             # Add: REVENUECAT_API_KEY, REVENUECAT_WEBHOOK_SECRET
└── workers/
    └── tasks/
        └── hd_export.py      # Update: Check payment status before export
```

Mobile:
```
mobile/src/
├── services/
│   ├── purchases.ts          # RevenueCat SDK wrapper
│   └── api.ts                # Backend API (HD export payment requests)
├── hooks/
│   ├── usePurchases.ts       # Hook for purchase flows, entitlement checks
│   └── useRateLimit.ts       # Hook for rate limit status, messaging
├── screens/
│   └── Exports/
│       └── HDExportScreen.tsx # Update: Wire real payment flow
└── components/
    ├── PremiumGate.tsx       # Reusable premium feature gate UI
    └── RateLimitBanner.tsx   # Rate limit messaging component
```

### Pattern 1: RevenueCat Entitlements-Based Access Control

**What:** RevenueCat uses Entitlements (access levels) that are unlocked by purchasing Products. Check entitlement status client-side for UI, verify server-side before granting content.

**When to use:** All premium feature access decisions.

**Example:**
```typescript
// Mobile: Check entitlement for UI
import Purchases from 'react-native-purchases';

async function checkPremiumAccess(): Promise<boolean> {
  try {
    const customerInfo = await Purchases.getCustomerInfo();
    // Check if "pro" entitlement is active
    const hasProAccess = customerInfo.entitlements.active['pro'] !== undefined;
    return hasProAccess;
  } catch (e) {
    console.error('Failed to get customer info', e);
    return false;
  }
}

// Purchase HD export (consumable - one-time purchase)
async function purchaseHDExport() {
  try {
    const offerings = await Purchases.getOfferings();
    const hdExportPackage = offerings.current?.availablePackages.find(
      pkg => pkg.identifier === 'hd_export'
    );

    if (!hdExportPackage) {
      throw new Error('HD export package not found');
    }

    const purchaseResult = await Purchases.purchasePackage(hdExportPackage);

    // Notify backend of purchase for processing
    await api.post('/api/v1/purchases/hd-export', {
      transaction_id: purchaseResult.customerInfo.originalAppUserId,
      export_job_id: currentExportJobId,
    });

    return purchaseResult;
  } catch (e) {
    if ((e as any).userCancelled) {
      console.log('User cancelled purchase');
    } else {
      console.error('Purchase failed', e);
    }
    throw e;
  }
}
```

**Backend verification:**
```python
# Backend: Verify purchase via RevenueCat REST API
import httpx
from app.core.config import settings

async def verify_subscriber_status(revenuecat_user_id: str) -> dict:
    """Get subscriber status from RevenueCat REST API."""
    url = f"https://api.revenuecat.com/v1/subscribers/{revenuecat_user_id}"
    headers = {
        "Authorization": f"Bearer {settings.REVENUECAT_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

async def check_entitlement(user_id: str, entitlement_id: str) -> bool:
    """Check if user has active entitlement."""
    subscriber_data = await verify_subscriber_status(user_id)
    entitlements = subscriber_data.get("subscriber", {}).get("entitlements", {})

    entitlement = entitlements.get(entitlement_id, {})
    expires_date = entitlement.get("expires_date")

    # Check if entitlement exists and is not expired
    if expires_date:
        from datetime import datetime
        expiry = datetime.fromisoformat(expires_date.replace("Z", "+00:00"))
        return datetime.now(expiry.tzinfo) < expiry

    # Non-expiring entitlement (lifetime purchase)
    return entitlement.get("product_identifier") is not None
```

### Pattern 2: Webhook-Based Payment Verification

**What:** RevenueCat sends webhooks on purchase events. Verify webhook authenticity via Authorization header, then call GET /subscribers REST API to get normalized subscriber data.

**When to use:** Real-time payment verification and entitlement updates.

**Example:**
```python
# Backend: RevenueCat webhook handler
from fastapi import APIRouter, Header, HTTPException, Request
from app.services.purchases import handle_purchase_event
from app.core.config import settings

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/revenuecat")
async def revenuecat_webhook(
    request: Request,
    authorization: str = Header(None),
):
    """Handle RevenueCat webhook notifications.

    RevenueCat sends POST requests with event data.
    Verify Authorization header, then fetch subscriber data via REST API.
    """
    # Verify webhook authenticity
    if authorization != f"Bearer {settings.REVENUECAT_WEBHOOK_SECRET}":
        raise HTTPException(status_code=401, detail="Invalid webhook authorization")

    # Parse webhook body
    event = await request.json()
    event_type = event.get("type")
    app_user_id = event.get("app_user_id")

    # Fetch full subscriber data from REST API (recommended pattern)
    subscriber_data = await verify_subscriber_status(app_user_id)

    # Handle event (update database, mark exports as paid, etc.)
    await handle_purchase_event(event_type, subscriber_data)

    # Always return 200 to acknowledge receipt
    return {"status": "ok"}
```

**Important:** Set Authorization header in RevenueCat dashboard (Project Settings → Integrations → Webhooks → Authorization Header). This secret must match `REVENUECAT_WEBHOOK_SECRET` in backend config.

### Pattern 3: Redis-Based Rate Limiting with Monthly Quotas

**What:** Use Redis to track per-user API usage with monthly reset. Store quota state in database, enforce via FastAPI dependency.

**When to use:** Limiting AI generation requests for free users (3 per month).

**Example:**
```python
# Backend: Rate limiting service
from datetime import datetime
from typing import Optional
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

class RateLimitService:
    def __init__(self, redis_client: Redis, db: AsyncSession):
        self.redis = redis_client
        self.db = db

    def get_month_key(self, user_id: str) -> str:
        """Get Redis key for current month's usage."""
        month = datetime.now().strftime("%Y-%m")
        return f"rate_limit:ai_gen:{user_id}:{month}"

    async def check_rate_limit(self, user_id: str, limit: int = 3) -> tuple[bool, int, int]:
        """Check if user is within rate limit.

        Returns: (is_allowed, current_count, limit)
        """
        key = self.get_month_key(user_id)
        current = self.redis.get(key)
        count = int(current) if current else 0

        if count >= limit:
            return False, count, limit

        return True, count, limit

    async def increment_usage(self, user_id: str) -> int:
        """Increment usage counter for current month."""
        key = self.get_month_key(user_id)
        new_count = self.redis.incr(key)

        # Set expiry to end of next month (ensures cleanup)
        if new_count == 1:
            from calendar import monthrange
            now = datetime.now()
            next_month = now.month + 1 if now.month < 12 else 1
            next_year = now.year if now.month < 12 else now.year + 1
            days_in_month = monthrange(next_year, next_month)[1]
            ttl_seconds = days_in_month * 24 * 60 * 60
            self.redis.expire(key, ttl_seconds)

        return new_count

    async def get_reset_date(self) -> datetime:
        """Get date when rate limit resets (first day of next month)."""
        now = datetime.now()
        if now.month == 12:
            return datetime(now.year + 1, 1, 1)
        return datetime(now.year, now.month + 1, 1)

# FastAPI dependency
from fastapi import Depends, HTTPException
from app.core.redis_client import get_redis
from app.core.db import get_db
from app.api.dependencies.auth import get_current_user

async def check_ai_generation_limit(
    user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
):
    """Dependency to enforce AI generation rate limit for free users."""
    # Premium users have unlimited generations
    if user.is_premium:
        return

    rate_limit_service = RateLimitService(redis, db)
    is_allowed, current, limit = await rate_limit_service.check_rate_limit(str(user.id))

    if not is_allowed:
        reset_date = await rate_limit_service.get_reset_date()
        raise HTTPException(
            status_code=429,
            detail={
                "message": f"Monthly AI generation limit reached ({limit} per month for free users)",
                "current_usage": current,
                "limit": limit,
                "reset_date": reset_date.isoformat(),
                "upgrade_message": "Upgrade to Premium for unlimited AI generations"
            }
        )

# Use dependency in route
@router.post("/styles/generate", dependencies=[Depends(check_ai_generation_limit)])
async def generate_ai_art(...):
    # Increment counter after successful generation
    await rate_limit_service.increment_usage(str(user.id))
    ...
```

**Mobile rate limit messaging:**
```typescript
// Mobile: Handle 429 rate limit error
async function generateAIArt() {
  try {
    const result = await api.post('/api/v1/styles/generate', {...});
    return result;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 429) {
      const detail = error.response.data.detail;
      // Show user-friendly rate limit message
      Alert.alert(
        'Monthly Limit Reached',
        `You've used all ${detail.limit} free AI generations this month. Resets ${formatDate(detail.reset_date)}.\n\nUpgrade to Premium for unlimited generations!`,
        [
          { text: 'Maybe Later', style: 'cancel' },
          { text: 'Upgrade', onPress: () => navigation.navigate('Premium') }
        ]
      );
    } else {
      throw error;
    }
  }
}
```

### Pattern 4: Non-Intrusive Premium Feature Gates

**What:** Show premium features as locked but visible. Time upsell prompts at natural decision points (e.g., after AI generation completes). Use clear messaging about value, not pressure.

**When to use:** Gating premium styles, HD export, unlimited AI generations.

**Example:**
```typescript
// Mobile: Premium feature gate component
interface PremiumGateProps {
  feature: string;
  onUpgrade: () => void;
  children: React.ReactNode;
}

const PremiumGate: React.FC<PremiumGateProps> = ({ feature, onUpgrade, children }) => {
  const { isPremium } = usePurchases();

  if (isPremium) {
    return <>{children}</>;
  }

  return (
    <View style={styles.gateContainer}>
      <View style={styles.lockedOverlay}>
        <Icon name="lock" size={32} color="#FFD700" />
        <Text style={styles.featureTitle}>{feature}</Text>
        <Text style={styles.description}>
          Unlock {feature} with Premium
        </Text>
        <TouchableOpacity style={styles.upgradeButton} onPress={onUpgrade}>
          <Text style={styles.upgradeText}>See Premium Plans</Text>
        </TouchableOpacity>
      </View>
      <View style={[styles.previewContent, { opacity: 0.3 }]}>
        {children}
      </View>
    </View>
  );
};

// Usage in style picker
<PremiumGate
  feature="Premium Styles"
  onUpgrade={() => navigation.navigate('Premium')}
>
  <StylePreview style={premiumStyle} />
</PremiumGate>
```

**Timing upsell prompts strategically:**
```typescript
// Show upsell after user completes AI generation (natural decision point)
const AIGenerateScreen = () => {
  const { isPremium } = usePurchases();
  const { generate, activeJob } = useAIGeneration(...);

  useEffect(() => {
    if (activeJob?.status === 'completed' && !isPremium) {
      // User just generated art - prime moment to upsell HD export
      setTimeout(() => {
        Alert.alert(
          'Your Art is Ready!',
          'Export in HD (2048x2048) to preserve every detail. Premium users get watermark-free exports.',
          [
            { text: 'Free Export', onPress: () => startFreeExport() },
            { text: 'Upgrade & Export HD', onPress: () => navigation.navigate('Premium') }
          ]
        );
      }, 1000); // Brief delay for user to see result
    }
  }, [activeJob?.status]);

  ...
};
```

### Anti-Patterns to Avoid

- **Anti-pattern:** Hiding premium features entirely from free users
  - **Why bad:** Users can't see value, can't aspire to upgrade
  - **Do instead:** Show locked premium features with clear value proposition

- **Anti-pattern:** Consuming RevenueCat purchase events immediately without webhook verification
  - **Why bad:** Race condition between mobile purchase and backend verification, user might see "paid" before server confirms
  - **Do instead:** Mobile triggers purchase → RevenueCat webhook → Backend verifies → Set is_paid=true → Export proceeds

- **Anti-pattern:** Storing rate limit state only in Redis without database backup
  - **Why bad:** Redis flush = user quotas reset = unfair advantage
  - **Do instead:** Use Redis for fast lookups, periodically sync to database, restore from DB on Redis restart

- **Anti-pattern:** Aggressive upsell prompts on every action
  - **Why bad:** Frustrates users, feels like nagging, reduces engagement
  - **Do instead:** Time prompts at natural decision points (completed generation, hit limit), non-blocking banners

- **Anti-pattern:** Validating purchases only client-side
  - **Why bad:** Trivial to bypass with jailbreak/root, modified APK/IPA, replayed receipts
  - **Do instead:** Always verify server-side via RevenueCat webhooks and REST API

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Receipt validation | Custom Apple/Google receipt verification | RevenueCat webhooks + REST API | Receipt formats differ by platform, Apple deprecated verifyReceipt, Google Play validation requires server-to-server token flow, RevenueCat handles all edge cases |
| Cross-platform IAP | Separate iOS (StoreKit) and Android (Play Billing) code | react-native-purchases | Unified API, handles platform differences, auto-consumes purchases on Android, restores purchases correctly |
| Subscription state tracking | Custom database of subscription states | RevenueCat subscriber status | Handles grace periods, billing retries, family sharing, intro offers, all edge cases you'll miss |
| Fraud prevention | Client-side purchase checks | Server-side webhook verification | Client-side checks are trivially bypassed, must verify on trusted server |
| Rate limiting | In-memory counters or manual Redis Lua | fastapi-limiter or slowapi | Distributed race conditions, atomic increments, TTL management, sliding windows - libraries handle this correctly |

**Key insight:** Payment infrastructure has massive regulatory, security, and edge-case complexity. RevenueCat abstracts 95% of this. The 5% you implement (webhook handling, entitlement checks) is much simpler than the 95% you avoid (receipt parsing, subscription lifecycle, platform API changes, fraud vectors).

## Common Pitfalls

### Pitfall 1: Treating Consumable and Non-Consumable Purchases Identically

**What goes wrong:** App offers HD export as consumable (correct) but also adds it to a RevenueCat entitlement. RevenueCat marks entitlement as "unlocked forever" after first purchase, breaking per-image charging.

**Why it happens:** Confusion between RevenueCat entitlements (access levels for subscriptions/lifetime) and consumable purchases (one-time, no ongoing access).

**How to avoid:**
- Consumable purchases (HD export per image): Don't attach to entitlements, handle via webhook NON_RENEWING_PURCHASE event, verify on backend, mark specific ExportJob as paid
- Non-consumable purchases (premium styles unlock): Attach to entitlement, RevenueCat tracks automatically
- Subscriptions (future Premium tier): Attach to entitlement, RevenueCat tracks expiration

**Warning signs:** User buys one HD export, sees all future exports as "paid" without additional charges.

### Pitfall 2: Android Consumable Auto-Consumption Race Condition

**What goes wrong:** User purchases HD export on Android, RevenueCat auto-consumes it, webhook arrives, backend marks ExportJob as paid, but export task hasn't started yet. User closes app. Next launch, purchase is consumed but export never happened.

**Why it happens:** Google Play requires consumables to be consumed immediately. RevenueCat SDK does this automatically on Android. If export task fails or user quits before completion, purchase is lost.

**How to avoid:**
- Webhook handler: Record purchase to purchases table immediately (idempotent on transaction ID)
- Mark ExportJob.is_paid = true in webhook, not in export task
- Export task: Check is_paid flag from ExportJob, proceed if true
- If export fails: is_paid remains true, user can retry without repurchasing (purchase record proves payment)
- Support flow: If user claims missing purchase, query purchases table by user_id, manually retry export if payment confirmed but result missing

**Warning signs:** User reports "I paid but didn't get my HD export" - check purchases table for orphaned transactions.

### Pitfall 3: Rate Limit State Loss on Redis Restart

**What goes wrong:** User exhausts free quota (3/3 AI generations). Redis restarts. Quota resets to 0/3. User gets 3 more free generations in same month.

**Why it happens:** Redis is in-memory, volatile. Rate limit counters stored only in Redis disappear on restart.

**How to avoid:**
- Add User model fields: `monthly_ai_count` (int), `last_reset_month` (string, "YYYY-MM")
- On each AI generation: Increment Redis counter AND User.monthly_ai_count in database
- Check rate limit: Try Redis first (fast path), fall back to database if key missing, restore Redis from DB
- Monthly reset: Cron job at start of month sets User.monthly_ai_count = 0 for all users
- Database is source of truth, Redis is cache

**Warning signs:** Monitoring shows Redis restarts, user quotas unexpectedly reset mid-month.

### Pitfall 4: Webhook Replay Attacks

**What goes wrong:** Attacker captures legitimate webhook POST body, replays it repeatedly. Backend processes same purchase multiple times, grants multiple HD exports for one payment.

**Why it happens:** Webhook handler doesn't check for duplicate events.

**How to avoid:**
- Extract `event.id` from webhook body (RevenueCat includes unique event ID)
- Before processing, check database: `SELECT 1 FROM webhook_events WHERE event_id = ?`
- If exists: Return 200 immediately (idempotent, don't error on replays)
- If new: Insert event_id into webhook_events table, process event
- Use database transaction to ensure atomic check-and-insert

**Warning signs:** Same purchase transaction ID appears in logs multiple times with different event IDs.

### Pitfall 5: Client-Side Entitlement Check Without Server Verification

**What goes wrong:** Mobile checks `customerInfo.entitlements.active['pro']`, shows "Premium" badge, unlocks features. Jailbroken/rooted device modifies RevenueCat response to fake premium status. Backend trusts mobile's claim, grants HD export without payment.

**Why it happens:** Client-side checks control UI, but backend doesn't independently verify.

**How to avoid:**
- Mobile: Check entitlements for UI only (show/hide premium badge, enable/disable buttons)
- Backend: Always verify via RevenueCat REST API before granting paid content
- HD export flow: Mobile requests export → Backend calls `GET /subscribers/{user_id}` → Checks entitlement or purchase record → Sets is_paid=true only if verified
- Never trust mobile's claim of "I have premium" without server verification

**Warning signs:** Fraud reports, unusually high "premium" usage without corresponding revenue.

## Code Examples

Verified patterns from official sources:

### Initialize RevenueCat SDK (Mobile)

```typescript
// Mobile: App startup initialization
import Purchases from 'react-native-purchases';
import { Platform } from 'react-native';
import { REVENUECAT_PUBLIC_API_KEY_IOS, REVENUECAT_PUBLIC_API_KEY_ANDROID } from '@env';

export async function initializePurchases(userId: string) {
  try {
    // Configure with platform-specific API keys
    const apiKey = Platform.select({
      ios: REVENUECAT_PUBLIC_API_KEY_IOS,
      android: REVENUECAT_PUBLIC_API_KEY_ANDROID,
    });

    if (!apiKey) {
      throw new Error('RevenueCat API key not configured');
    }

    await Purchases.configure({ apiKey });

    // Identify user (important for cross-device purchases)
    await Purchases.logIn(userId);

    console.log('RevenueCat initialized');
  } catch (e) {
    console.error('Failed to initialize RevenueCat', e);
  }
}

// Call during app startup after user authentication
useEffect(() => {
  if (user) {
    initializePurchases(user.id);
  }
}, [user]);
```

### Check Entitlement Status (Mobile)

```typescript
// Mobile: Hook for checking premium access
import { useState, useEffect } from 'react';
import Purchases, { CustomerInfo } from 'react-native-purchases';

export function usePurchases() {
  const [customerInfo, setCustomerInfo] = useState<CustomerInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadCustomerInfo();

    // Listen for purchase updates
    Purchases.addCustomerInfoUpdateListener(setCustomerInfo);

    return () => {
      // Cleanup listener (SDK manages lifecycle)
    };
  }, []);

  const loadCustomerInfo = async () => {
    try {
      const info = await Purchases.getCustomerInfo();
      setCustomerInfo(info);
    } catch (e) {
      console.error('Failed to load customer info', e);
    } finally {
      setIsLoading(false);
    }
  };

  const isPremium = customerInfo?.entitlements.active['pro'] !== undefined;

  const purchasePackage = async (packageToPurchase: PurchasesPackage) => {
    try {
      const { customerInfo: updatedInfo } = await Purchases.purchasePackage(packageToPurchase);
      setCustomerInfo(updatedInfo);
      return updatedInfo;
    } catch (e: any) {
      if (e.userCancelled) {
        console.log('User cancelled purchase');
      } else {
        console.error('Purchase error', e);
      }
      throw e;
    }
  };

  const restorePurchases = async () => {
    try {
      const info = await Purchases.restorePurchases();
      setCustomerInfo(info);
      return info;
    } catch (e) {
      console.error('Restore failed', e);
      throw e;
    }
  };

  return {
    customerInfo,
    isLoading,
    isPremium,
    purchasePackage,
    restorePurchases,
    refresh: loadCustomerInfo,
  };
}
```

### Server-Side Webhook Handler

```python
# Backend: Complete webhook handler with idempotency
from fastapi import APIRouter, Header, HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_db
from app.models.webhook_event import WebhookEvent
from app.models.purchase import Purchase
from app.models.export_job import ExportJob
from app.services.purchases import verify_subscriber_status
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/revenuecat")
async def revenuecat_webhook(
    request: Request,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle RevenueCat webhook events.

    Implements idempotency via event_id tracking.
    Verifies authorization header.
    Processes purchase events (NON_RENEWING_PURCHASE for consumables).
    """
    # Verify webhook authenticity
    expected_auth = f"Bearer {settings.REVENUECAT_WEBHOOK_SECRET}"
    if authorization != expected_auth:
        logger.warning("Invalid webhook authorization attempt")
        raise HTTPException(status_code=401, detail="Invalid authorization")

    # Parse event
    event = await request.json()
    event_id = event.get("id")
    event_type = event.get("type")
    app_user_id = event.get("app_user_id")

    if not event_id or not event_type or not app_user_id:
        logger.error(f"Invalid webhook payload: {event}")
        raise HTTPException(status_code=400, detail="Invalid payload")

    # Check for duplicate event (idempotency)
    stmt = select(WebhookEvent).where(WebhookEvent.event_id == event_id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        logger.info(f"Duplicate webhook event {event_id}, returning 200")
        return {"status": "ok", "message": "Event already processed"}

    # Record event
    webhook_event = WebhookEvent(
        event_id=event_id,
        event_type=event_type,
        app_user_id=app_user_id,
        payload=event,
    )
    db.add(webhook_event)

    try:
        # Fetch full subscriber data (recommended pattern)
        subscriber_data = await verify_subscriber_status(app_user_id)

        # Handle event type
        if event_type == "NON_RENEWING_PURCHASE":
            # Consumable purchase (HD export)
            await handle_consumable_purchase(db, app_user_id, event, subscriber_data)
        elif event_type == "INITIAL_PURCHASE":
            # Subscription or non-consumable (premium unlock)
            await handle_subscription_purchase(db, app_user_id, event, subscriber_data)
        elif event_type == "RENEWAL":
            # Subscription renewal
            await handle_subscription_renewal(db, app_user_id, subscriber_data)
        elif event_type == "CANCELLATION":
            # Subscription cancelled (still active until expiry)
            logger.info(f"Subscription cancelled for {app_user_id}")
        elif event_type == "EXPIRATION":
            # Subscription expired
            await handle_subscription_expiration(db, app_user_id)

        await db.commit()
        logger.info(f"Processed webhook event {event_id} ({event_type})")

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to process webhook event {event_id}: {e}", exc_info=True)
        # Still return 200 to prevent retries on permanent errors
        # RevenueCat will retry 5xx errors but not 200
        return {"status": "error", "message": str(e)}

    return {"status": "ok"}


async def handle_consumable_purchase(
    db: AsyncSession,
    user_id: str,
    event: dict,
    subscriber_data: dict,
):
    """Handle consumable purchase (HD export per image)."""
    # Extract transaction details
    product_id = event.get("product_id")
    transaction_id = event.get("id")  # Use event ID as transaction ID

    # Check if purchase already recorded
    stmt = select(Purchase).where(Purchase.transaction_id == transaction_id)
    result = await db.execute(stmt)
    existing_purchase = result.scalar_one_or_none()

    if existing_purchase:
        logger.info(f"Purchase {transaction_id} already recorded")
        return

    # Record purchase
    purchase = Purchase(
        user_id=user_id,
        product_id=product_id,
        transaction_id=transaction_id,
        purchase_type="consumable",
        amount=4.99,  # HD export price
        currency="EUR",
    )
    db.add(purchase)

    # Mark most recent pending HD export as paid
    # (User flow: request export -> get product_id -> purchase -> webhook marks paid)
    stmt = (
        select(ExportJob)
        .where(
            ExportJob.user_id == user_id,
            ExportJob.is_paid == False,
            ExportJob.status.in_(["pending", "processing"]),
        )
        .order_by(ExportJob.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    export_job = result.scalar_one_or_none()

    if export_job:
        export_job.is_paid = True
        logger.info(f"Marked ExportJob {export_job.id} as paid (purchase {transaction_id})")
    else:
        logger.warning(f"No pending export found for user {user_id} after purchase {transaction_id}")
```

### Rate Limiting Dependency

```python
# Backend: Rate limit dependency for AI generation
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from redis import Redis
from datetime import datetime
from app.core.db import get_db
from app.core.redis_client import get_redis
from app.api.dependencies.auth import get_current_user
from app.models.user import User

class RateLimitExceeded(HTTPException):
    """Custom exception for rate limit exceeded."""
    def __init__(self, current: int, limit: int, reset_date: str):
        super().__init__(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Monthly limit of {limit} AI generations reached",
                "current_usage": current,
                "limit": limit,
                "reset_date": reset_date,
                "upgrade_available": True,
            }
        )


async def check_ai_generation_limit(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> User:
    """Check if user can generate AI art (rate limit for free users).

    Premium users: unlimited
    Free users: 3 per month

    Returns user if allowed, raises RateLimitExceeded if limit reached.
    """
    # Premium users bypass rate limit
    if user.is_premium:
        return user

    # Check monthly quota
    current_month = datetime.now().strftime("%Y-%m")

    # Reset counter if new month
    if user.last_reset_month != current_month:
        user.monthly_ai_count = 0
        user.last_reset_month = current_month
        await db.commit()

    # Check limit
    limit = 3  # Free tier limit
    if user.monthly_ai_count >= limit:
        # Calculate reset date
        now = datetime.now()
        if now.month == 12:
            reset_date = datetime(now.year + 1, 1, 1)
        else:
            reset_date = datetime(now.year, now.month + 1, 1)

        raise RateLimitExceeded(
            current=user.monthly_ai_count,
            limit=limit,
            reset_date=reset_date.isoformat(),
        )

    # Increment counter
    user.monthly_ai_count += 1
    await db.commit()

    return user


# Use in route
@router.post("/styles/generate")
async def generate_ai_art(
    request: AIGenerateRequest,
    user: User = Depends(check_ai_generation_limit),  # Rate limit check
    db: AsyncSession = Depends(get_db),
):
    """Generate AI art from iris (rate-limited for free users)."""
    # User passed rate limit check, proceed with generation
    ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Direct StoreKit/Play Billing integration | RevenueCat or similar IAP backend service | ~2019-2020 | Receipt validation, subscription tracking, cross-platform support centralized; reduces fraud, simplifies code |
| Apple verifyReceipt endpoint | App Store Server API with JWT | June 2023 (deprecated 2024) | More secure, modern REST API, better fraud detection, no more base64 receipt blobs |
| Per-second/per-minute rate limits | Monthly/usage-based quotas | ~2023 (freemium shift) | Better aligns with user value, reduces "burst then block" frustration, clearer pricing tiers |
| Hidden premium features | Visible but locked features | ~2022 (UX research) | Higher conversion, users understand value, aspirational design |
| Client-side purchase validation | Server-side webhook validation | Ongoing best practice | Prevents fraud, ensures audit trail, enables business logic (e.g., grant access) |

**Deprecated/outdated:**
- **Apple verifyReceipt endpoint**: Deprecated in favor of App Store Server API (2023+). Still works but not recommended for new implementations.
- **react-native-iap without backend**: Direct StoreKit/Play Billing without server validation was common pre-2020. Now considered insecure, fraud-prone.
- **Synchronous webhook processing**: Early implementations blocked webhook response until processing complete. RevenueCat recommends responding quickly (< 60s) and deferring heavy processing.
- **Global rate limits (all users same bucket)**: Outdated for freemium. Modern apps use per-user tiered limits with database persistence.

## Open Questions

1. **Should premium styles be sold individually or as a pack?**
   - What we know: Requirement says "per-export or style pack" (both options allowed)
   - What's unclear: Which monetization strategy better fits user behavior
   - Recommendation: Start with per-export consumable (simpler, lower commitment), add style pack later if data shows users want bulk purchase

2. **How to handle export payment timing (pre-pay vs post-pay)?**
   - What we know: User wants HD export → payment flow → export processing
   - What's unclear: Should payment happen before export starts or after preview?
   - Recommendation: Pre-pay before export (user sees low-res preview from Phase 4, decides to pay for HD, then HD export starts). Prevents "I don't like the HD version" refund requests.

3. **Should we persist rate limit state in PostgreSQL or separate rate_limits table?**
   - What we know: Need to survive Redis restarts, monthly resets
   - What's unclear: Add columns to User model or separate table
   - Recommendation: Add to User model (monthly_ai_count, last_reset_month) - simpler, no joins, already loading user on auth. Separate table only if multiple quota types (future phases).

4. **Android consumable handling: Should we delay consumption until export completes?**
   - What we know: RevenueCat auto-consumes on Android, race condition possible if export fails
   - What's unclear: Can we defer consumption safely
   - Recommendation: Accept auto-consumption, rely on Purchase record as proof of payment. If export fails, user can retry using purchase history (no repurchase needed). Add support flow to manually retry failed exports.

## Sources

### Primary (HIGH confidence)
- [RevenueCat React Native Installation Guide](https://www.revenuecat.com/docs/getting-started/installation/reactnative) - Official SDK setup and configuration
- [RevenueCat Webhooks Documentation](https://www.revenuecat.com/docs/integrations/webhooks) - Webhook event types, authentication, best practices
- [react-native-purchases NPM Package](https://www.npmjs.com/package/react-native-purchases) - v9.7.6 latest, API reference
- [RevenueCat Non-Subscription Purchases](https://www.revenuecat.com/docs/platform-resources/non-subscriptions) - Consumable vs non-consumable handling
- [RevenueCat Entitlements Guide](https://www.revenuecat.com/docs/getting-started/entitlements) - Entitlements vs products vs offerings
- [Getting Subscription Status](https://www.revenuecat.com/docs/customers/customer-info) - REST API subscriber status checks

### Secondary (MEDIUM confidence)
- [fastapi-limiter PyPI](https://pypi.org/project/fastapi-limiter/) - Redis-based rate limiting for FastAPI
- [SlowAPI Documentation](https://slowapi.readthedocs.io/) - Alternative rate limiter, flask-limiter patterns
- [Adapty: iOS In-App Purchase Server-Side Validation](https://adapty.io/blog/ios-in-app-purchase-server-side-validation/) - Receipt validation best practices
- [Adapty: Android In-App Purchases Server-Side Validation](https://adapty.io/blog/android-in-app-purchases-server-side-validation/) - Google Play validation patterns
- [Heroic Labs: In-app Purchase Validation](https://heroiclabs.com/docs/nakama/concepts/iap-validation/) - Fraud prevention, replay attack protection
- [Best Practices for API Rate Limits - Moesif](https://www.moesif.com/blog/technical/rate-limiting/Best-Practices-for-API-Rate-Limits-and-Quotas-With-Moesif-to-Avoid-Angry-Customers/) - User experience for rate limiting
- [UX in Freemium Products - Aguayo](https://aguayo.co/en/blog-aguayo-user-experience/ux-in-freemium-products/) - Balancing monetization and UX
- [4 UX Design Tips for Freemium - UpTop](https://uptopcorp.com/blog/capitalize-on-the-mobile-app-freemium-model-with-these-4-ux-tips/) - Feature gate best practices
- [How Freemium SaaS Products Convert Users - Appcues](https://www.appcues.com/blog/best-freemium-upgrade-prompts) - Strategic upgrade prompt timing

### Tertiary (LOW confidence)
- [Medium: Setting Up In-App Purchases with RevenueCat (React Native)](https://medium.com/@pranavmore/setting-up-in-app-purchases-with-revenuecat-in-ios-react-native-ad8c259ee779) - Community tutorial, specific to iOS
- [GeekyAnts: React Native Subscription with RevenueCat](https://geekyants.com/blog/react-native-subscription-monetization-made-easy-leveraging-revenuecat-for-seamless-in-app-purchases) - High-level integration overview

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - RevenueCat is industry standard, react-native-purchases v9.7.6 verified, fastapi-limiter widely used
- Architecture: HIGH - Official RevenueCat patterns (webhook → REST API call), rate limiting patterns verified across sources
- Pitfalls: MEDIUM-HIGH - Consumable handling and webhook idempotency well-documented, rate limit persistence inferred from Redis best practices

**Research date:** 2026-02-10
**Valid until:** 2026-04-10 (60 days - payment infrastructure stable, but platform policies change quarterly)
