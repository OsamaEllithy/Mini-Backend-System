"""
Tests for deduplication logic and bulk import.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_bulk_import_new_assets(client: AsyncClient, auth_headers: dict[str, str]):
    """Test importing new assets creates them."""
    payload = {
        "assets": [
            {
                "type": "domain",
                "value": "new1.com",
                "tags": ["t1"],
                "metadata": {"k1": "v1"},
            },
            {
                "type": "domain",
                "value": "new2.com",
            },
        ]
    }
    response = await client.post("/import", headers=auth_headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["created_count"] == 2
    assert data["updated_count"] == 0
    assert data["error_count"] == 0


@pytest.mark.asyncio
async def test_bulk_import_deduplication(
    client: AsyncClient, auth_headers: dict[str, str]
):
    """Test importing existing assets performs a deep merge."""
    # 1. Create initial asset
    await client.post(
        "/import",
        headers=auth_headers,
        json={
            "assets": [
                {
                    "type": "domain",
                    "value": "merge.com",
                    "tags": ["old_tag"],
                    "metadata": {"key1": "val1", "nested": {"a": 1}},
                }
            ]
        },
    )

    # 2. Re-import with new data
    resp2 = await client.post(
        "/import",
        headers=auth_headers,
        json={
            "assets": [
                {
                    "type": "domain",
                    "value": "merge.com",
                    "tags": ["new_tag", "old_tag"],  # Testing tag union
                    "metadata": {"key1": "new_val", "key2": "val2", "nested": {"b": 2}},
                }
            ]
        },
    )
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["created_count"] == 0
    assert data["updated_count"] == 1  # Successfully merged

    # 3. Fetch and verify merge
    get_resp = await client.get("/assets?search=merge.com")
    asset = get_resp.json()["items"][0]

    # Verify tags
    tags = [t["name"] for t in asset["tags"]]
    assert len(tags) == 2
    assert "old_tag" in tags
    assert "new_tag" in tags

    # Verify metadata
    meta = asset["metadata_"]
    assert meta["key1"] == "new_val"  # Overwritten
    assert meta["key2"] == "val2"  # Added
    assert meta["nested"] == {"a": 1, "b": 2}  # Deep merged
