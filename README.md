# IrisVue

Mobile app that turns iris photos into personalized art. Users capture their iris with AI-guided camera controls, apply artistic styles or generate unique AI compositions, and share creations in collaborative circles.

## Architecture

- **Mobile** (`mobile/`) -- React Native 0.83 bare workflow (iOS & Android)
- **Backend** (`backend/`) -- FastAPI, PostgreSQL, Redis, Celery, MinIO

## Prerequisites

- Node >= 20
- Docker & Docker Compose
- JDK 21 (Android builds)
- Android SDK (Android builds)

## Getting Started

### Backend

```bash
cd backend
docker compose up -d
```

This starts PostgreSQL, Redis, MinIO, the FastAPI server (port 8000), a Celery worker, and Flower (port 5555).

Run migrations:

```bash
docker compose exec web alembic upgrade head
```

### Mobile

```bash
cd mobile
npm install
npx react-native start
```

In a separate terminal, build and install the app:

```bash
# Android
npx react-native run-android

# iOS
npx react-native run-ios
```

## Running Tests

```bash
# Backend
cd backend
docker compose exec web pytest

# Mobile
cd mobile
npx jest
```

## Key Features

- AI-guided iris capture with real-time camera overlay
- Artistic style presets and AI-generated compositions
- HD export
- Shared circles with invite links and iris fusion
- Biometric consent flows (GDPR/BIPA/CCPA)
- RevenueCat-based freemium monetization

## License

Proprietary. All rights reserved.
