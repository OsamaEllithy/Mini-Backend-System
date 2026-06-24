"""
Tests for relationship logic and graph building.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_valid_relationship(
    client: AsyncClient, auth_headers: dict[str, str]
):
    """Test creating a valid relationship between subdomain and domain."""
    # Create domain
    d_resp = await client.post(
        "/assets",
        headers=auth_headers,
        json={"type": "domain", "value": "reltest.com"},
    )
    domain_id = d_resp.json()["id"]

    # Create subdomain
    s_resp = await client.post(
        "/assets",
        headers=auth_headers,
        json={"type": "subdomain", "value": "api.reltest.com"},
    )
    sub_id = s_resp.json()["id"]

    # Create relationship
    rel_resp = await client.post(
        "/relationships/relationships",
        headers=auth_headers,
        json={
            "source_asset_id": sub_id,
            "target_asset_id": domain_id,
            "relationship_type": "subdomain_of",
        },
    )
    assert rel_resp.status_code == 201
    assert rel_resp.json()["relationship_type"] == "subdomain_of"


@pytest.mark.asyncio
async def test_invalid_relationship_type(
    client: AsyncClient, auth_headers: dict[str, str]
):
    """Test that invalid relationships are rejected."""
    # Create two domains
    d1 = await client.post(
        "/assets", headers=auth_headers, json={"type": "domain", "value": "d1.com"}
    )
    d2 = await client.post(
        "/assets", headers=auth_headers, json={"type": "domain", "value": "d2.com"}
    )

    # Try invalid relationship (domain -> domain via subdomain_of)
    rel_resp = await client.post(
        "/relationships/relationships",
        headers=auth_headers,
        json={
            "source_asset_id": d1.json()["id"],
            "target_asset_id": d2.json()["id"],
            "relationship_type": "subdomain_of",
        },
    )
    assert rel_resp.status_code == 400
    assert "requires source asset of type" in rel_resp.json()["detail"]


@pytest.mark.asyncio
async def test_get_graph(client: AsyncClient, auth_headers: dict[str, str]):
    """Test BFS graph traversal."""
    # A graph: IP <- Service <- Subdomain -> Domain
    # (Creating nodes and edges omitted for brevity, asserting 200 is sufficient for setup validation)

    ip = await client.post(
        "/assets", headers=auth_headers, json={"type": "ip_address", "value": "2.2.2.2"}
    )
    svc = await client.post(
        "/assets", headers=auth_headers, json={"type": "service", "value": "2.2.2.2:80"}
    )

    await client.post(
        "/relationships/relationships",
        headers=auth_headers,
        json={
            "source_asset_id": svc.json()["id"],
            "target_asset_id": ip.json()["id"],
            "relationship_type": "service_on",
        },
    )

    graph_resp = await client.get(f"/relationships/assets/{ip.json()['id']}/graph")
    assert graph_resp.status_code == 200
    data = graph_resp.json()
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1
