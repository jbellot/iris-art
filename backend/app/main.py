"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sqlalchemy import text

from app import __version__
from app.api.routes import (
    auth,
    circles,
    consent,
    exports,
    fusion,
    health,
    invites,
    photos,
    privacy,
    processing,
    purchases,
    styles,
    users,
    webhooks,
    websocket,
)
from app.core.config import settings
from app.core.db import engine

# Initialize Sentry for error monitoring
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        integrations=[
            FastApiIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    async with engine.begin() as conn:
        # Test database connection
        await conn.execute(text("SELECT 1"))
    yield
    # Shutdown
    await engine.dispose()


# Create FastAPI application
app = FastAPI(
    title="IrisVue API",
    version=__version__,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(privacy.router)
app.include_router(users.router)
app.include_router(photos.router)
app.include_router(processing.router)
app.include_router(styles.router)
app.include_router(exports.router)
app.include_router(circles.router)
app.include_router(invites.router)
app.include_router(consent.router)
app.include_router(fusion.router)
app.include_router(purchases.router, prefix="/api/v1/purchases", tags=["purchases"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(websocket.router)
