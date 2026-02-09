---
phase: 05-social-features-circles-and-fusion
plan: 01
subsystem: social/circles
tags: [backend, models, api, redis, invites]
dependency_graph:
  requires: [phase-01-foundation, redis]
  provides: [circle-model, circle-api, invite-tokens]
  affects: [user-model]
tech_stack:
  added: [itsdangerous]
  patterns: [soft-delete, ownership-transfer, token-serialization, rate-limiting]
key_files:
  created:
    - backend/app/models/circle.py
    - backend/app/models/circle_membership.py
    - backend/app/schemas/circles.py
    - backend/app/services/circle_service.py
    - backend/app/services/invite_service.py
    - backend/app/api/routes/circles.py
    - backend/app/api/routes/invites.py
    - backend/alembic/versions/d4e5f6a7b8c9_add_circles_and_circle_memberships.py
  modified:
    - backend/app/models/__init__.py
    - backend/app/models/user.py
    - backend/app/main.py
decisions:
  - title: "Soft delete for memberships with ownership transfer"
    rationale: "Allows users to rejoin circles while preserving audit trail. Ownership automatically transfers to oldest remaining member when owner leaves."
  - title: "Redis for invite token single-use tracking"
    rationale: "Used tokens stored with 30-day TTL (longer than 7-day validity) to prevent replay attacks without database overhead."
  - title: "Rate limiting via Redis counters"
    rationale: "5 invites per circle per hour enforced via Redis counters with 1-hour TTL to prevent spam."
  - title: "10-member circle limit and 20-circle-per-user limit"
    rationale: "Reasonable constraints for MVP social features. Prevents performance issues with large groups."
metrics:
  duration: 5
  tasks_completed: 2
  files_modified: 11
  completed_at: "2026-02-09T20:27:17Z"
---

# Phase 05 Plan 01: Circles Backend Summary

**One-liner:** Circle and CircleMembership models with invite token system using itsdangerous, Redis-based single-use tracking, and 9 REST endpoints for circle management.

## What Was Built

### Models & Database
- **Circle model**: UUID PK, name (max 50 chars), created_by FK to users, created_at timestamp
- **CircleMembership model**: UUID PK, circle_id/user_id FKs with CASCADE delete, role (owner/member), joined_at, left_at (soft delete)
- **Unique constraint**: (circle_id, user_id) to prevent duplicate memberships
- **Indexes**: circle_id and user_id for efficient queries
- **User model relationship**: Added circle_memberships back_populates
- **Alembic migration**: Creates both tables with proper constraints

### Services
- **CircleService** (`backend/app/services/circle_service.py`):
  - `create_circle`: Creates circle + adds creator as owner, validates 20-circle limit
  - `get_user_circles`: Lists circles with role and member count
  - `get_circle_detail`: Returns circle info + members list
  - `get_circle_members`: Lists active members (requires membership)
  - `leave_circle`: Soft deletes membership, transfers ownership to oldest member if owner leaves, hard deletes circle if last member
  - `remove_member`: Owner-only, soft deletes target membership
  - `verify_active_membership`: Helper to check membership (raises 403 if not active)

- **InviteService** (`backend/app/services/invite_service.py`):
  - `generate_invite_token`: Uses URLSafeTimedSerializer with "circle-invite" salt
  - `validate_invite_token`: Checks 7-day expiry and Redis used_invite:{token} key
  - `mark_token_used`: Sets Redis key with 30-day TTL
  - `accept_invite`: Validates token, checks circle exists, verifies not duplicate member, enforces 10-member limit, creates membership, marks token used
  - `get_invite_info`: Returns circle name and inviter email without joining (preview)

### API Routes
- **Circle routes** (`/api/v1/circles`):
  - `POST /circles` - Create circle (201 Created)
  - `GET /circles` - List user's circles
  - `GET /circles/{id}` - Circle detail with members
  - `GET /circles/{id}/members` - List active members
  - `POST /circles/{id}/leave` - Leave circle (204 No Content)
  - `DELETE /circles/{id}/members/{user_id}` - Remove member (owner only, 204)

- **Invite routes** (`/api/v1/circles`):
  - `POST /circles/{id}/invite` - Generate invite with rate limiting (201 Created)
  - `GET /invites/{token}/info` - Preview invite without accepting
  - `POST /invites/accept` - Accept invite and join circle

### Schemas
- **CircleCreateRequest**: name validation (1-50 chars)
- **CircleResponse**: id, name, role, member_count, created_at
- **CircleMemberResponse**: user_id, email, role, joined_at
- **CircleDetailResponse**: Extends CircleResponse with members list
- **InviteCreateResponse**: invite_url, token, expires_in_days
- **InviteAcceptRequest**: token string
- **InviteInfoResponse**: circle_id, circle_name, inviter_email

## Deviations from Plan

None - plan executed exactly as written.

## Technical Decisions

### Token System
- **itsdangerous URLSafeTimedSerializer** with SECRET_KEY and salt "circle-invite"
- Payload: {circle_id, inviter_id} serialized
- 7-day max age (604800 seconds)
- Redis tracking: `used_invite:{token}` with 30-day TTL (longer than validity for safety)

### Ownership Transfer Logic
When owner leaves a circle:
1. Check for other active members (left_at IS NULL)
2. If found: Transfer ownership to oldest member (earliest joined_at), soft delete owner membership
3. If not found: Hard delete circle and all memberships (cascade handles memberships)

### Rejoining Circles
- Users can rejoin circles after self-leaving (left_at reset to NULL, joined_at updated)
- Current implementation allows rejoining regardless of leave reason (self vs removed by owner)
- For stricter enforcement, would need to track who set left_at

### Rate Limiting
- Redis counter: `invite_rate:{circle_id}:{user_id}`
- Limit: 5 invites per hour
- TTL: 3600 seconds (1 hour)
- Returns 429 Too Many Requests if exceeded

### Limits Enforced
- **10 members per circle**: Checked in accept_invite
- **20 circles per user**: Checked in create_circle and accept_invite
- Both use COUNT queries on active memberships (left_at IS NULL)

## Verification Results

### Syntax Validation
All files passed Python AST syntax validation:
- circle.py: OK
- circle_membership.py: OK
- circles.py (schemas): OK
- circle_service.py: OK
- invite_service.py: OK
- circles.py (routes): OK
- invites.py (routes): OK
- main.py: OK

### Files Verified
- Migration file created: `d4e5f6a7b8c9_add_circles_and_circle_memberships.py`
- All models, schemas, services, and routes syntactically valid
- Routers registered in main.py

## Next Steps

**Plan 05-02** will build on this foundation to:
- Add mobile screens for circle creation and management
- Implement deep linking for invite URLs
- Add UI for member lists and ownership transfer indicators

## Implementation Notes

### Import Patterns
- Used existing Redis client from `app.core.security`
- Followed existing model patterns (UUID PKs, timezone-aware DateTime)
- Used existing auth pattern (`get_current_user` from `app.api.deps`)

### Relationship Patterns
- All FKs use CASCADE delete for referential integrity
- back_populates ensures bidirectional relationships
- TYPE_CHECKING imports prevent circular dependencies

### API Response Patterns
- CircleResponse computed from multiple sources (circle info + member count query)
- All routes follow existing HTTP status code conventions (201 Created, 204 No Content, 403 Forbidden)

## Self-Check: PASSED

### Created Files Verification
```
✓ backend/app/models/circle.py
✓ backend/app/models/circle_membership.py
✓ backend/app/schemas/circles.py
✓ backend/app/services/circle_service.py
✓ backend/app/services/invite_service.py
✓ backend/app/api/routes/circles.py
✓ backend/app/api/routes/invites.py
✓ backend/alembic/versions/d4e5f6a7b8c9_add_circles_and_circle_memberships.py
```

### Modified Files Verification
```
✓ backend/app/models/__init__.py (imports Circle, CircleMembership)
✓ backend/app/models/user.py (circle_memberships relationship)
✓ backend/app/main.py (routers registered)
```

### Commits Verification
```
✓ 8e20408: feat(05-01): add Circle and CircleMembership models with schemas and migration
✓ 55b9a7f: feat(05-01): add circle and invite services with API routes
```

All files exist, commits present, syntax valid.
