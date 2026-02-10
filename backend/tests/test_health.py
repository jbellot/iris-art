"""Tests for health check endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_liveness(client: AsyncClient):
    """Test liveness endpoint returns healthy status."""
    response = await client.get("/health/liveness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


@pytest.mark.asyncio
async def test_readiness(client: AsyncClient):
    """Test readiness endpoint checks all services."""
    response = await client.get("/health/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "db" in data
    assert "redis" in data
    assert "storage" in data


@pytest.mark.asyncio
async def test_health_db(client: AsyncClient):
    """Test database health check endpoint."""
    response = await client.get("/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "database"
