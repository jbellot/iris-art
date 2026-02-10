"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Test successful user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "SecurePassword123!"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registration with duplicate email fails."""
    # Register first user
    await client.post(
        "/api/v1/auth/register",
        json={"email": "duplicate@example.com", "password": "Password123!"},
    )

    # Try to register with same email
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "duplicate@example.com", "password": "DifferentPass123!"},
    )
    assert response.status_code in [400, 409]  # Bad request or conflict


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login after registration."""
    # Register user
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "Password123!"},
    )

    # Login
    response = await client.post(
        "/api/v1/auth/login/json",
        json={"email": "login@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Test login with wrong password fails."""
    # Register user
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wrongpass@example.com", "password": "CorrectPassword123!"},
    )

    # Login with wrong password
    response = await client.post(
        "/api/v1/auth/login/json",
        json={"email": "wrongpass@example.com", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401
