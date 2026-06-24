"""
Tests for asset endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_asset_unauthorized(client: AsyncClient):
    """Test creating an asset without auth token fails."""
    response = await client.post(
        "/assets",
        json={
            "type": "domain",
            "value": "example.com",
            "tags": ["test"],
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_asset_success(client: AsyncClient, auth_headers: dict[str, str]):
    """Test creating an asset successfully with auth token."""
    response = await client.post(
        "/assets",
        headers=auth_headers,
        json={
            "type": "domain",
            "value": "example.com",
            "status": "active",
            "source": "manual",
            "tags": ["prod", "web"],
            "metadata": {"registrar": "Test"},
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "domain"
    assert data["value"] == "example.com"
    assert len(data["tags"]) == 2
    assert "id" in data


@pytest.mark.asyncio
async def test_create_duplicate_asset(client: AsyncClient, auth_headers: dict[str, str]):
    """Test creating a duplicate asset returns 409 Conflict."""
    payload = {
        "type": "domain",
        "value": "example.com",
    }
    # Create first
    resp1 = await client.post("/assets", headers=auth_headers, json=payload)
    assert resp1.status_code == 201

    # Create duplicate
    resp2 = await client.post("/assets", headers=auth_headers, json=payload)
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_list_assets_pagination(client: AsyncClient, auth_headers: dict[str, str]):
    """Test listing assets with pagination (public access)."""
    # Create multiple
    for i in range(5):
        await client.post(
            "/assets",
            headers=auth_headers,
            json={"type": "domain", "value": f"test{i}.com"},
        )

    response = await client.get("/assets?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["total_pages"] == 3


@pytest.mark.asyncio
async def test_get_single_asset(client: AsyncClient, auth_headers: dict[str, str]):
    """Test fetching a single asset."""
    # Create
    create_resp = await client.post(
        "/assets",
        headers=auth_headers,
        json={"type": "ip_address", "value": "1.1.1.1"},
    )
    asset_id = create_resp.json()["id"]

    # Fetch
    get_resp = await client.get(f"/assets/{asset_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["value"] == "1.1.1.1"


@pytest.mark.asyncio
async def test_soft_delete_asset(client: AsyncClient, auth_headers: dict[str, str]):
    """Test soft deleting an asset updates status to removed."""
    # Create
    create_resp = await client.post(
        "/assets",
        headers=auth_headers,
        json={"type": "domain", "value": "delete.me"},
    )
    asset_id = create_resp.json()["id"]

    # Delete
    del_resp = await client.delete(f"/assets/{asset_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    # Fetch and check status
    get_resp = await client.get(f"/assets/{asset_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "removed"
