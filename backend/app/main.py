"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import __version__
from app.api.routes import auth, health, photos, privacy, processing, users, websocket
from app.core.config import settings
from app.core.db import engine


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
app.include_router(websocket.router)
