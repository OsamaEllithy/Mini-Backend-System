"""
Tests for user authentication and authorization.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    response = await client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    """Test registering existing username fails."""
    payload = {
        "username": "dupuser",
        "email": "dup@example.com",
        "password": "password123",
    }
    await client.post("/auth/register", json=payload)
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login returns JWT."""
    # Register
    await client.post(
        "/auth/register",
        json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "loginpass",
        },
    )

    # Login
    response = await client.post(
        "/auth/login",
        json={
            "username": "loginuser",
            "password": "loginpass",
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_failure(client: AsyncClient):
    """Test login with wrong password fails."""
    response = await client.post(
        "/auth/login",
        json={
            "username": "nonexistent",
            "password": "wrong",
        },
    )
    assert response.status_code == 401
