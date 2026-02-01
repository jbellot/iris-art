# Phase 1: Foundation and Privacy Architecture - Research

**Researched:** 2026-02-01
**Domain:** FastAPI backend, async Python, authentication, privacy compliance
**Confidence:** HIGH

## Summary

Phase 1 establishes the complete backend foundation for IrisVue, combining async FastAPI with PostgreSQL, implementing secure authentication (email/password, Apple Sign In, Google Sign In), and ensuring biometric data privacy compliance across GDPR, BIPA, and CCPA jurisdictions. The research confirms that the Python/FastAPI ecosystem has mature, production-ready solutions for all phase requirements.

The standard approach uses FastAPI with SQLAlchemy 2.0 async, PostgreSQL, Celery for background jobs, Redis as message broker, and S3-compatible storage (MinIO for development). Authentication follows OAuth2 with JWT patterns using PyJWT and pwdlib (Argon2). Privacy compliance requires explicit biometric consent flows with jurisdiction detection, encrypted storage, and GDPR-compliant data export/deletion capabilities.

This phase is foundational—all subsequent phases depend on the authentication, database access patterns, and privacy infrastructure established here. The vertical build approach means each component (auth, storage, privacy) should be built end-to-end with tests before moving forward.

**Primary recommendation:** Use FastAPI official patterns with async SQLAlchemy 2.0, leverage fastapi-users for authentication scaffolding, implement jurisdiction-aware consent flows from day one, and ensure Docker Compose enables complete local development without external dependencies.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | >=0.115.0 | Async web framework | Official Python async API framework with OpenAPI, type validation, dependency injection |
| SQLAlchemy | >=2.0.0 | Async ORM | Industry standard ORM, full async support in 2.0+, robust migration story |
| asyncpg | >=0.29.0 | PostgreSQL driver | Fastest async PostgreSQL driver, required for SQLAlchemy async |
| PostgreSQL | 15+ | Primary database | Battle-tested RDBMS, excellent JSON support, GDPR compliance friendly |
| Celery | >=5.2.7 | Task queue | De facto standard for Python background jobs, reliable at scale |
| Redis | 7+ | Message broker & cache | Celery broker, session storage, high-performance caching |
| Alembic | >=1.13.0 | Schema migrations | SQLAlchemy's official migration tool, supports async |
| PyJWT | latest | JWT tokens | Lightweight, standards-compliant JWT implementation |
| pwdlib | latest | Password hashing | Modern replacement for passlib, uses Argon2 (recommended by FastAPI) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| fastapi-users | latest | Auth scaffolding | Email verification, password reset, OAuth providers—reduces boilerplate |
| boto3 | latest | S3 client | S3 operations (upload, encryption, presigned URLs) |
| MinIO | latest | S3-compatible storage | Local development, eliminates cloud dependency for testing |
| Authlib | >=1.6.6 | OAuth2 providers | Google/Apple Sign In server-side verification |
| python-jose | latest | JWT utilities | Additional JWT operations if needed beyond PyJWT |
| itsdangerous | latest | Token signing | Email verification tokens, password reset tokens |
| pydantic | >=2.0 | Data validation | Built into FastAPI, use for all request/response models |
| python-multipart | latest | Form data | Required for OAuth2PasswordRequestForm |
| uvicorn | latest | ASGI server | FastAPI's recommended production server |
| Flower | latest | Celery monitoring | Development monitoring of Celery tasks |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| fastapi-users | Custom auth | Custom gives more control but 10x more code; use fastapi-users unless specific needs |
| MinIO | LocalStack | LocalStack broader (all AWS), MinIO focused on S3 and faster for object storage |
| Authlib | python-social-auth | python-social-auth older, less FastAPI-native; Authlib maintained and FastAPI-focused |
| Celery | FastAPI BackgroundTasks | BackgroundTasks for light tasks, Celery for reliability and scale (AI processing needs Celery) |

**Installation:**
```bash
# Core backend
pip install "fastapi[standard]>=0.115.0"
pip install "sqlalchemy[asyncio]>=2.0.0"
pip install asyncpg>=0.29.0
pip install alembic>=1.13.0
pip install redis>=4.5.4
pip install celery>=5.2.7

# Authentication & security
pip install fastapi-users[sqlalchemy]
pip install pyjwt
pip install "pwdlib[argon2]"
pip install authlib>=1.6.6
pip install itsdangerous
pip install python-multipart

# Storage
pip install boto3

# Development
pip install uvicorn[standard]
pip install flower
```

## Architecture Patterns

### Recommended Project Structure
```
backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── core/
│   │   ├── config.py        # Settings (Pydantic BaseSettings)
│   │   ├── security.py      # JWT, password hashing, OAuth2 scheme
│   │   └── db.py            # Async engine, session factory
│   ├── models/              # SQLAlchemy models (async)
│   │   ├── user.py
│   │   ├── consent.py
│   │   └── iris_data.py
│   ├── schemas/             # Pydantic schemas for API
│   │   ├── user.py
│   │   ├── auth.py
│   │   └── privacy.py
│   ├── api/
│   │   ├── deps.py          # Shared dependencies (get_db, get_current_user)
│   │   └── routes/
│   │       ├── auth.py      # Login, register, OAuth callbacks
│   │       ├── users.py     # User management, account deletion
│   │       └── privacy.py   # Consent, data export, deletion
│   ├── services/            # Business logic layer
│   │   ├── auth.py
│   │   ├── user.py
│   │   └── privacy.py
│   ├── workers/
│   │   ├── celery_app.py    # Celery instance
│   │   └── tasks/
│   │       ├── email.py     # Email verification, password reset
│   │       └── exports.py   # GDPR data export generation
│   └── storage/
│       └── s3.py            # S3 operations with encryption
├── alembic/                 # Database migrations
├── tests/
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

### Pattern 1: Async Session Management with Dependency Injection
**What:** FastAPI dependency that yields AsyncSession per request, properly scoped and cleaned up
**When to use:** All database operations in routes
**Example:**
```python
# Source: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
# app/core/db.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False  # Critical: prevents lazy load after commit
)

async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

# app/api/routes/users.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

@app.get("/users/me")
async def get_current_user_profile(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Use db session here
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one()
    return user
```

### Pattern 2: JWT Authentication with OAuth2 Password Bearer
**What:** FastAPI's OAuth2PasswordBearer with JWT tokens for stateless authentication
**When to use:** All authenticated endpoints
**Example:**
```python
# Source: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
# app/core/security.py
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from pwdlib import PasswordHash

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
password_hash = PasswordHash.recommended()  # Uses Argon2

SECRET_KEY = "your-secret-key-from-env"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user
```

### Pattern 3: Refresh Token for Session Persistence
**What:** Long-lived refresh tokens stored in Redis for persistent sessions across app restarts
**When to use:** User sessions that persist beyond access token expiration (required by AUTH-06)
**Example:**
```python
# Source: https://medium.com/@bhagyarana80/fastapi-refresh-tokens-securely-manage-user-sessions-beyond-expiry-9f937cfb59c0
# app/core/security.py
import redis
from datetime import timedelta

REFRESH_TOKEN_EXPIRE_DAYS = 30
redis_client = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)

def create_refresh_token(user_id: str) -> str:
    token_data = {"sub": user_id, "type": "refresh"}
    refresh_token = create_access_token(
        token_data,
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    # Store in Redis for revocation capability
    redis_client.setex(
        f"refresh_token:{user_id}:{refresh_token}",
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "valid"
    )
    return refresh_token

async def refresh_access_token(refresh_token: str, db: AsyncSession):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        # Check if token exists in Redis (not revoked)
        if not redis_client.exists(f"refresh_token:{user_id}:{refresh_token}"):
            raise HTTPException(status_code=401, detail="Refresh token revoked")

        # Generate new access token
        access_token = create_access_token(data={"sub": user_id})
        return {"access_token": access_token, "token_type": "bearer"}
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
```

### Pattern 4: Apple Sign In Server-Side Verification
**What:** Verify Apple identity tokens server-side using Apple's public keys
**When to use:** Apple Sign In callback endpoint (required for iOS App Store)
**Example:**
```python
# Source: https://gist.github.com/davidhariri/b053787aabc9a8a9cc0893244e1549fe
# app/services/auth.py
import jwt
import requests
from cryptography.hazmat.primitives import serialization
from jwt.algorithms import RSAAlgorithm

APPLE_PUBLIC_KEYS_URL = "https://appleid.apple.com/auth/keys"

def get_apple_public_key(token: str):
    # Fetch Apple's public keys (cache for 24 hours in production)
    response = requests.get(APPLE_PUBLIC_KEYS_URL)
    keys = response.json()["keys"]

    # Extract kid from token header
    header = jwt.get_unverified_header(token)
    kid = header["kid"]

    # Find matching key
    apple_key = next((key for key in keys if key["kid"] == kid), None)
    if not apple_key:
        raise ValueError("Public key not found")

    # Convert JWK to PEM
    public_key = RSAAlgorithm.from_jwk(apple_key)
    pem_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem_key

async def verify_apple_token(identity_token: str, app_id: str):
    public_key = get_apple_public_key(identity_token)

    # Decode and verify
    payload = jwt.decode(
        identity_token,
        public_key,
        algorithms=["RS256"],
        audience=app_id
    )

    # Extract user info (email only returned on first auth)
    user_id = payload["sub"]
    email = payload.get("email")

    return {"user_id": user_id, "email": email}
```

### Pattern 5: Jurisdiction-Aware Consent Flow
**What:** Detect user jurisdiction and present appropriate biometric consent based on GDPR/BIPA/CCPA
**When to use:** Before any biometric data capture (required by PRIV-01, PRIV-05)
**Example:**
```python
# Source: https://secureprivacy.ai/blog/privacy-laws-2026
# app/services/privacy.py
from enum import Enum
from geoip2 import database

class Jurisdiction(str, Enum):
    GDPR = "gdpr"        # EU
    BIPA = "bipa"        # Illinois
    CCPA = "ccpa"        # California
    GENERIC = "generic"  # Other US states

def detect_jurisdiction(ip_address: str, state: str = None) -> Jurisdiction:
    """Detect user jurisdiction from IP and optionally state"""
    # Use GeoIP or similar for IP-based detection
    reader = database.Reader('GeoLite2-Country.mmdb')
    try:
        response = reader.country(ip_address)
        country = response.country.iso_code

        if country in ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI",
                       "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU",
                       "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"]:
            return Jurisdiction.GDPR

        if country == "US":
            if state == "IL":
                return Jurisdiction.BIPA
            elif state == "CA":
                return Jurisdiction.CCPA

        return Jurisdiction.GENERIC
    finally:
        reader.close()

async def get_consent_requirements(jurisdiction: Jurisdiction) -> dict:
    """Return jurisdiction-specific consent requirements"""
    requirements = {
        Jurisdiction.GDPR: {
            "explicit_consent": True,
            "purpose_disclosure": True,
            "retention_policy": True,
            "right_to_withdraw": True,
            "data_minimization": True,
            "text": "We collect biometric data (iris images) for artwork generation. Data is stored encrypted and deleted after 30 days. You can withdraw consent and request deletion at any time."
        },
        Jurisdiction.BIPA: {
            "written_consent": True,  # Electronic signature valid
            "purpose_disclosure": True,
            "retention_schedule": True,
            "no_profit_from_data": True,
            "text": "We will collect and store your biometric identifiers (iris images) to generate personalized artwork. Your data will be retained for 30 days and permanently deleted thereafter. We will not sell, lease, or trade your biometric data."
        },
        Jurisdiction.CCPA: {
            "notice_at_collection": True,
            "opt_out_right": True,
            "deletion_right": True,
            "text": "We collect biometric information (iris patterns) for art generation. You have the right to request deletion of your data at any time. We do not sell your biometric information."
        },
        Jurisdiction.GENERIC: {
            "basic_consent": True,
            "text": "We collect iris images to generate artwork. Data is encrypted and can be deleted upon request."
        }
    }
    return requirements[jurisdiction]
```

### Pattern 6: GDPR-Compliant Account Deletion
**What:** Complete user data erasure across all systems (database, S3, Redis) within required timeframe
**When to use:** User account deletion request (AUTH-07, PRIV-04)
**Example:**
```python
# Source: https://gdpr-info.eu/art-17-gdpr/
# app/services/user.py
from app.workers.tasks.exports import export_user_data
from app.storage.s3 import delete_user_files

async def delete_user_account(user_id: str, db: AsyncSession):
    """
    GDPR Article 17: Right to erasure
    Must complete "without undue delay" (< 30 days)
    """
    # 1. Generate final data export (GDPR portability before erasure)
    export_task = export_user_data.delay(user_id)
    await export_task.get(timeout=300)  # Wait for export

    # 2. Delete S3 objects (iris images, generated art)
    await delete_user_files(user_id)

    # 3. Delete Redis sessions/refresh tokens
    redis_client.delete(f"refresh_token:{user_id}:*")
    redis_client.delete(f"session:{user_id}:*")

    # 4. Delete database records
    # Note: Some audit logs may be retained for legal compliance
    await db.execute(delete(ConsentRecord).where(ConsentRecord.user_id == user_id))
    await db.execute(delete(IrisData).where(IrisData.user_id == user_id))
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()

    # 5. Log deletion for compliance audit trail
    logger.info(f"User {user_id} account deleted per GDPR Article 17")
```

### Pattern 7: Celery Task for Background Jobs
**What:** Async Celery tasks for long-running operations (email, exports, AI processing)
**When to use:** Operations taking >2 seconds, operations that can retry, operations that must complete even if API request fails
**Example:**
```python
# Source: https://testdriven.io/blog/fastapi-and-celery/
# app/workers/celery_app.py
from celery import Celery

celery_app = Celery(
    "iris_art",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
)

celery_app.conf.task_routes = {
    "app.workers.tasks.email.*": {"queue": "email"},
    "app.workers.tasks.exports.*": {"queue": "exports"},
}

# app/workers/tasks/email.py
from app.workers.celery_app import celery_app

@celery_app.task(name="send_verification_email", max_retries=3)
def send_verification_email(user_email: str, token: str):
    # Email sending logic
    verification_link = f"https://app.irisvue.com/verify?token={token}"
    # Send email with verification_link
    return True
```

### Pattern 8: Docker Compose for Local Development
**What:** Complete local dev stack with FastAPI, PostgreSQL, Redis, Celery, MinIO
**When to use:** Local development, integration testing (INFR-04)
**Example:**
```yaml
# Source: https://testdriven.io/blog/fastapi-docker-traefik/
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    command: fastapi run app/main.py --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./app:/code/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/iris_art
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - S3_ENDPOINT=http://minio:9000
      - S3_ACCESS_KEY=minioadmin
      - S3_SECRET_KEY=minioadmin
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=iris_art
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery_worker:
    build: .
    command: celery -A app.workers.celery_app worker --loglevel=info --logfile=logs/celery.log
    volumes:
      - ./app:/code/app
      - ./logs:/code/logs
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/iris_art
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - db
      - redis

  flower:
    build: .
    command: celery -A app.workers.celery_app flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
      - celery_worker

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  minio_data:
```

### Anti-Patterns to Avoid

- **Shared AsyncSession across concurrent tasks**: Never pass same session to `asyncio.gather()` or concurrent operations—create separate sessions per task
- **Lazy loading relationships in async**: Always use `selectinload()` or `joinedload()` for relationships; lazy loading triggers implicit I/O that fails in async
- **Mixing sync and async SQLAlchemy**: Don't use old `session.query()` API; use `select()` statements with `await db.execute()`
- **Plain text password storage**: Always hash with Argon2 via pwdlib; never store passwords unhashed
- **Security through obscurity**: Don't roll custom crypto, JWT implementations, or OAuth flows—use established libraries
- **CORS promiscuity**: Don't use `allow_origins=["*"]` in production; whitelist specific frontend domains
- **Missing `expire_on_commit=False`**: Async sessions must set this to prevent lazy load errors after commit
- **Token storage in localStorage**: Mobile apps should use secure storage (Keychain/Keystore), not AsyncStorage
- **Ignoring jurisdiction**: Don't use one-size-fits-all consent; BIPA has strict requirements and private right of action
- **Consent after capture**: Must obtain consent BEFORE any biometric data collection, not after

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Email verification flow | Custom token generation, expiry logic, email templates | fastapi-users verify router + itsdangerous | Token expiry, replay attacks, email deliverability—battle-tested solution handles edge cases |
| Password reset | Time-limited tokens, rate limiting, email workflow | fastapi-users reset router | Security-critical: needs rate limiting, token single-use, secure token generation |
| OAuth2 provider integration | Manual OAuth flow, token exchange, state management | Authlib FastAPI client | OAuth state management, PKCE, token refresh, provider quirks already handled |
| JWT token management | Custom JWT encode/decode, expiry, refresh logic | PyJWT + FastAPI OAuth2PasswordBearer | Token expiry, algorithm selection, key rotation—use standard implementation |
| Password hashing | bcrypt or custom hash | pwdlib with Argon2 | Argon2 recommended by OWASP, resistant to GPU attacks; pwdlib is FastAPI's official recommendation |
| Session persistence | Custom session store | Redis with refresh tokens | Built-in expiry, atomic operations, high performance—reinventing wastes time |
| S3 operations | Custom multipart upload, presigned URLs | boto3 | Complex: multipart upload, retry logic, error handling—boto3 is AWS-maintained |
| Database migrations | Manual SQL scripts | Alembic | Schema versioning, rollbacks, autogeneration—manual migrations error-prone at scale |
| API input validation | Manual validation, type checking | Pydantic (built into FastAPI) | Type coercion, nested validation, OpenAPI generation—FastAPI core feature |
| Background job queue | Threading or multiprocessing | Celery + Redis | Reliable task delivery, retry logic, distributed workers—production-proven |
| Biometric consent tracking | Custom consent records | Audit-logged consent model with timestamp, IP, jurisdiction | Legal compliance needs immutable audit trail, jurisdiction metadata, withdrawal tracking |

**Key insight:** Authentication, OAuth, and privacy compliance are security-critical domains where custom implementations introduce vulnerabilities. Use mature libraries that have been audited and battle-tested in production. The development time saved is secondary to the security guarantees these libraries provide.

## Common Pitfalls

### Pitfall 1: AsyncSession Shared Across Concurrent Tasks
**What goes wrong:** `asyncio.gather()` or concurrent FastAPI background tasks share single AsyncSession, causing "Task attached to different loop" or concurrent access errors
**Why it happens:** AsyncSession is not thread-safe or concurrency-safe; each concurrent operation needs its own session
**How to avoid:** Use `async_sessionmaker` to create separate session per concurrent task, or use dependency injection per request
**Warning signs:** `RuntimeError: Task <Task> got Future attached to a different loop`, intermittent database errors under load

### Pitfall 2: Lazy Loading Relationships in Async Context
**What goes wrong:** Accessing user.posts raises `MissingGreenlet` error because relationship wasn't eagerly loaded
**Why it happens:** SQLAlchemy async doesn't support implicit I/O on attribute access (lazy loading requires sync context)
**How to avoid:** Always use `selectinload()` or `joinedload()` in your queries for relationships you'll access
**Warning signs:** `sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called`, errors when accessing relationship attributes

### Pitfall 3: Not Setting expire_on_commit=False
**What goes wrong:** After `await session.commit()`, accessing model attributes triggers new database queries or errors
**Why it happens:** By default, SQLAlchemy expires all attributes after commit to ensure fresh data on next access
**How to avoid:** Set `expire_on_commit=False` when creating `async_sessionmaker`, or explicitly refresh objects you need
**Warning signs:** Unexpected SELECT queries after commit, `MissingGreenlet` errors when accessing committed objects

### Pitfall 4: Weak JWT Secret Keys
**What goes wrong:** JWT tokens can be brute-forced or predicted, allowing authentication bypass
**Why it happens:** Using short secrets (e.g., "secret123") or hardcoded values instead of cryptographically random keys
**How to avoid:** Generate 256-bit random key with `openssl rand -hex 32`, store in environment variables, rotate periodically
**Warning signs:** Security audit flags weak secrets, tokens decoded without proper secret

### Pitfall 5: Storing Refresh Tokens Without Revocation
**What goes wrong:** User logs out but refresh token still works, or compromised refresh token can't be invalidated
**Why it happens:** Stateless JWTs can't be revoked; need external storage (Redis) to track valid refresh tokens
**How to avoid:** Store refresh tokens in Redis with user ID key, delete on logout, check existence on token refresh
**Warning signs:** Logged-out users can still refresh tokens, no way to force logout, security incident can't invalidate tokens

### Pitfall 6: Missing CORS Configuration for Mobile
**What goes wrong:** React Native app fails to authenticate because cookies aren't sent, or OPTIONS preflight fails
**Why it happens:** Mobile apps aren't same-origin; need explicit CORS config and token-based (not cookie-based) auth
**How to avoid:** Use Authorization header with Bearer tokens (not cookies), configure CORS middleware for mobile app origin
**Warning signs:** CORS errors in mobile app, authentication works in web but fails in mobile

### Pitfall 7: Capturing Biometric Data Before Consent
**What goes wrong:** BIPA lawsuit risk—Illinois law requires written consent BEFORE collection, with statutory damages up to $5,000 per violation
**Why it happens:** UI flow captures iris image first, then shows consent screen (assuming user will consent)
**How to avoid:** Implement consent screen BEFORE camera permission request, store consent record with timestamp/IP before any capture
**Warning signs:** Camera opens before consent screen, consent record created after image upload

### Pitfall 8: One-Size-Fits-All Consent Text
**What goes wrong:** GDPR audit finds missing retention policy disclosure, or BIPA compliance review finds missing written consent
**Why it happens:** Using generic consent text that doesn't meet specific requirements of GDPR/BIPA/CCPA
**How to avoid:** Implement jurisdiction detection, store consent with jurisdiction context, use jurisdiction-specific text
**Warning signs:** Consent text doesn't mention retention period (GDPR), no written consent mechanism (BIPA), missing opt-out language (CCPA)

### Pitfall 9: Incomplete Account Deletion
**What goes wrong:** User requests account deletion, but iris images remain in S3, or refresh tokens still work
**Why it happens:** Deletion logic only clears database records, not associated data in other systems (S3, Redis, Celery tasks)
**How to avoid:** Implement comprehensive deletion: database, S3 objects, Redis keys, cancel pending Celery tasks, log deletion for audit
**Warning signs:** GDPR complaint about incomplete deletion, deleted users can still authenticate with old refresh tokens

### Pitfall 10: Apple Sign In Email Availability Assumption
**What goes wrong:** App crashes or fails to create user because email is None (user chose "Hide My Email" on first login, then removed app from Apple ID settings)
**Why it happens:** Apple only returns email on first authorization; if user removes app from Apple ID and re-authenticates, email is not provided again
**How to avoid:** Store email on first authentication, handle None email gracefully (use Apple user ID as unique identifier), prompt user to provide email if needed
**Warning signs:** User reports can't sign in with Apple after deleting and reinstalling app, email field unexpectedly null

### Pitfall 11: Missing Docker Health Checks
**What goes wrong:** FastAPI container starts before PostgreSQL is ready, causing connection errors or startup failures
**Why it happens:** `depends_on` in Docker Compose only waits for container start, not service readiness
**How to avoid:** Add healthcheck to PostgreSQL service, use `depends_on` with `condition: service_healthy`
**Warning signs:** Intermittent startup failures, "connection refused" errors when starting containers, need to restart web service

### Pitfall 12: Alembic Autogenerate Doesn't Detect Everything
**What goes wrong:** Migration runs successfully but some schema changes are missing (indexes, constraints, renamed columns)
**Why it happens:** Alembic's autogenerate has known limitations—can't detect table renames, column renames, some constraint changes
**How to avoid:** Always manually review generated migrations, test migration up/down on dev database, maintain naming conventions for autogenerate
**Warning signs:** Schema drift between models and database, "column not found" errors after migration, manual schema fixes needed

## Code Examples

Verified patterns from official sources:

### Complete Authentication Endpoint with JWT
```python
# Source: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
from datetime import datetime, timedelta, timezone
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt
from pwdlib import PasswordHash

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
password_hash = PasswordHash.recommended()

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str

@app.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session)
) -> Token:
    # Authenticate user
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not password_hash.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

### Async Database Query with Eager Loading
```python
# Source: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_with_consents(user_id: str, db: AsyncSession):
    """
    Correct async pattern: eager load relationships to avoid lazy loading
    """
    stmt = select(User).where(User.id == user_id).options(
        selectinload(User.consent_records),
        selectinload(User.iris_data)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # Now safe to access relationships without additional queries
    if user:
        consents = user.consent_records  # No lazy load, already fetched

    return user
```

### S3 Upload with Server-Side Encryption
```python
# Source: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/object/server_side_encryption.html
import boto3
from botocore.config import Config

s3_client = boto3.client(
    's3',
    endpoint_url=os.getenv('S3_ENDPOINT'),
    aws_access_key_id=os.getenv('S3_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('S3_SECRET_KEY'),
    config=Config(signature_version='s3v4')
)

async def upload_iris_image(user_id: str, image_data: bytes) -> str:
    """
    Upload iris image with AES256 server-side encryption
    """
    key = f"iris/{user_id}/{uuid.uuid4()}.jpg"

    s3_client.put_object(
        Bucket='iris-art',
        Key=key,
        Body=image_data,
        ServerSideEncryption='AES256',  # PRIV-02: Encrypted at rest
        ContentType='image/jpeg',
        Metadata={
            'user_id': user_id,
            'uploaded_at': datetime.now(timezone.utc).isoformat()
        }
    )

    return key
```

### Email Verification Token Generation
```python
# Source: https://fastapi-users.github.io/fastapi-users/latest/configuration/routers/verify/
from itsdangerous import URLSafeTimedSerializer

serializer = URLSafeTimedSerializer(SECRET_KEY, salt="email-verification")

def generate_verification_token(email: str) -> str:
    """Generate time-limited verification token"""
    return serializer.dumps(email, salt="email-verification")

def verify_verification_token(token: str, max_age: int = 3600) -> str:
    """Verify token and extract email (max_age in seconds)"""
    try:
        email = serializer.loads(
            token,
            salt="email-verification",
            max_age=max_age  # 1 hour expiry
        )
        return email
    except:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SQLAlchemy 1.4 with sync | SQLAlchemy 2.0 with async/await | SQLAlchemy 2.0 released Jan 2023 | Full async I/O, better performance with asyncpg, new select() API required |
| passlib for password hashing | pwdlib with Argon2 | FastAPI docs updated 2024-2025 | Argon2 more resistant to GPU attacks, pwdlib actively maintained |
| OAuth2PasswordBearer with cookies | OAuth2PasswordBearer with tokens | Mobile-first apps 2023+ | Mobile apps can't use cookies reliably; token-based auth required |
| GDPR-only compliance | Multi-jurisdiction (GDPR/BIPA/CCPA) | 2024-2026 US state laws | 20 US states now have privacy laws; must detect jurisdiction and adapt consent |
| Manual OAuth implementation | Authlib FastAPI integration | Authlib 1.0+ 2023 | Handles OAuth state, PKCE, token refresh automatically |
| LocalStack for S3 | MinIO for S3-compatible | 2024+ | MinIO faster, lighter, focused on S3; LocalStack broader but heavier |
| Docker base images (tiangolo/uvicorn-gunicorn-fastapi) | Custom Dockerfile from python:3.9 | FastAPI docs deprecated base image 2024 | Better control, faster builds, Kubernetes-native single-process containers |
| session.query() API | select() statements | SQLAlchemy 2.0 | query() deprecated, select() required for async, better type hints |
| Single token auth | Access + refresh token pattern | 2023+ security best practices | Short-lived access tokens limit breach impact, refresh tokens enable revocation |

**Deprecated/outdated:**
- **tiangolo/uvicorn-gunicorn-fastapi Docker image**: Deprecated by FastAPI maintainer; build from python:3.9 instead
- **session.query() API**: SQLAlchemy 1.x API; use select() statements for 2.0 async
- **passlib**: Superseded by pwdlib; FastAPI docs now recommend pwdlib with Argon2
- **python-jose[cryptography]**: Many guides use this, but PyJWT is lighter and sufficient for FastAPI JWT needs
- **Cookie-based sessions for mobile**: Doesn't work reliably in React Native; use Authorization header with Bearer tokens

## Open Questions

Things that couldn't be fully resolved:

1. **GeoIP Library Choice**
   - What we know: Need to detect EU/US state for jurisdiction-aware consent (PRIV-05)
   - What's unclear: Best Python library for IP geolocation (geoip2, maxminddb, ipinfo)—licensing and accuracy tradeoffs
   - Recommendation: Start with geoip2 and MaxMind GeoLite2 database (free, reasonable accuracy), evaluate paid solutions if accuracy critical

2. **Apple Sign In Team ID and Key Management**
   - What we know: Need to generate client secret from private key for Apple token verification
   - What's unclear: Best practices for storing Apple Developer Team ID, Key ID, private key in production (environment variables, secrets manager, HSM)
   - Recommendation: Use environment variables for development, evaluate AWS Secrets Manager or similar for production rotation

3. **Email Service Provider**
   - What we know: Need to send verification emails, password reset emails (AUTH-04, AUTH-05)
   - What's unclear: Which ESP to use (SendGrid, AWS SES, Mailgun, Postmark)—deliverability vs cost tradeoffs
   - Recommendation: Start with AWS SES (lowest cost, good deliverability), abstract email sending behind interface for easy switching

4. **Data Export Format for GDPR Portability**
   - What we know: Must provide "structured, commonly used and machine-readable format" (JSON, CSV, XML)
   - What's unclear: What format users actually want for iris images + metadata—JSON with S3 URLs, ZIP with images + JSON manifest, CSV with base64
   - Recommendation: JSON manifest with presigned S3 URLs (portable, doesn't duplicate storage), include images in ZIP for "download all" option

5. **Biometric Data Retention Policy**
   - What we know: GDPR and BIPA require disclosure of retention period, data should be deleted when no longer needed
   - What's unclear: Business requirement for retention (30 days? 90 days? User-configurable? Delete after art generation?)
   - Recommendation: Research with product team—suggest 30 days default with automatic deletion, user can request early deletion

6. **Celery Task Monitoring in Production**
   - What we know: Flower works for development monitoring (included in Docker Compose)
   - What's unclear: Production-grade monitoring solution (Flower with auth, Datadog, custom Prometheus metrics, CloudWatch)
   - Recommendation: Use Flower with basic auth for MVP, migrate to Datadog or Prometheus + Grafana for production observability

## Sources

### Primary (HIGH confidence)
- FastAPI Official Documentation (https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) - JWT authentication patterns, Docker deployment
- SQLAlchemy 2.0 Official Documentation (https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) - Async patterns, session management, pitfalls
- TestDriven.io FastAPI + SQLAlchemy Tutorial (https://testdriven.io/blog/fastapi-sqlmodel/) - Async SQLAlchemy 2.0 best practices
- TestDriven.io FastAPI + Celery Tutorial (https://testdriven.io/blog/fastapi-and-celery/) - Celery setup with Redis, project structure
- Authlib Official Documentation (https://docs.authlib.org/en/latest/client/fastapi.html) - OAuth2 provider integration
- boto3 Documentation (https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/object/server_side_encryption.html) - S3 server-side encryption
- David Hariri GitHub Gist (https://gist.github.com/davidhariri/b053787aabc9a8a9cc0893244e1549fe) - Apple Sign In verification code
- FastAPI Users Documentation (https://fastapi-users.github.io/fastapi-users/latest/configuration/routers/verify/) - Email verification router

### Secondary (MEDIUM confidence)
- Multiple 2025-2026 Medium articles on FastAPI authentication (Better Stack, TestDriven.io, Think Loop)
- Recent 2026 blog post on Celery + FastAPI (https://blog.greeden.me/en/2026/01/27/the-complete-guide-to-background-processing-with-fastapi-x-celery-redishow-to-separate-heavy-work-from-your-api-to-keep-services-stable/)
- Multiple GitHub repositories showing async SQLAlchemy 2.0 patterns (rhoboro/async-fastapi-sqlalchemy, benavlabs/FastAPI-boilerplate)
- 2026 GDPR/BIPA/CCPA compliance guides (Secure Privacy, Keyless, various legal blogs)
- Docker Hub MinIO documentation (https://hub.docker.com/r/minio/minio)
- FastAPI security pitfalls article (https://medium.com/@ThinkingLoop/fastapi-security-pitfalls-that-almost-leaked-my-user-data-c9903bc13fd7)

### Tertiary (LOW confidence - marked for validation)
- WebSearch results for jurisdiction detection implementation patterns—need to validate with legal counsel
- Community discussions about Apple Sign In email handling—need to test with actual Apple Sign In flow
- Some Alembic async migration workarounds from GitHub discussions—official support status unclear

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - FastAPI, SQLAlchemy 2.0, Celery, Redis verified from official docs and multiple production examples
- Architecture: HIGH - Patterns verified from official FastAPI and SQLAlchemy documentation, TestDriven.io tutorials
- Pitfalls: HIGH - Async session issues documented in official SQLAlchemy docs, security pitfalls from FastAPI security guide
- Privacy compliance: MEDIUM - Legal requirements verified from official GDPR/BIPA sources, implementation patterns from compliance blogs (not legal advice)
- OAuth providers: MEDIUM - Authlib official docs exist, Apple Sign In verified from gist and community patterns, Google similar
- Email verification: HIGH - fastapi-users provides production-ready solution, verified from official docs

**Research date:** 2026-02-01
**Valid until:** 2026-03-01 (30 days—FastAPI ecosystem stable, privacy laws evolve slowly)

**Notes for planner:**
- All core libraries (FastAPI, SQLAlchemy, Celery) are mature and stable—safe to use without version concerns
- Privacy compliance requires ongoing legal review—research provides technical implementation, not legal advice
- Docker Compose setup verified and production-ready for local development
- Mobile auth (Apple/Google Sign In) requires additional testing in actual mobile app context
- Consider creating spike task for jurisdiction detection library evaluation before implementation
