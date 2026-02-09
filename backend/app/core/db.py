"""Async SQLAlchemy database configuration."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# Create async session factory with expire_on_commit=False
# CRITICAL: This prevents lazy load errors in async contexts
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync engine for Celery workers (lazy import to avoid psycopg2 dependency at module load)
_sync_engine = None
_sync_session_maker = None


def get_sync_session_maker():
    """Get or create sync session maker for Celery workers."""
    global _sync_engine, _sync_session_maker

    if _sync_session_maker is None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        # Replace asyncpg with psycopg2 for sync access
        SYNC_DATABASE_URL = settings.DATABASE_URL.replace("+asyncpg", "")
        _sync_engine = create_engine(SYNC_DATABASE_URL, echo=settings.DEBUG)
        _sync_session_maker = sessionmaker(bind=_sync_engine, expire_on_commit=False)

    return _sync_session_maker


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
