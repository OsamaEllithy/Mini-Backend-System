"""
Unit tests for deduplication utilities (metadata deep merge, tag union).
"""

from app.utils.metadata_merge import deep_merge_metadata


def test_deep_merge_metadata_basic():
    """Test merging basic scalar values."""
    existing = {"a": 1, "b": 2}
    incoming = {"b": 3, "c": 4}
    merged = deep_merge_metadata(existing, incoming)
    assert merged == {"a": 1, "b": 3, "c": 4}


def test_deep_merge_metadata_nested_dicts():
    """Test recursive merging of nested dictionaries."""
    existing = {
        "ports": {"80": "open"},
        "ssl": {"valid": True},
    }
    incoming = {
        "ports": {"443": "open", "80": "closed"},
        "tags": ["web"],
    }
    merged = deep_merge_metadata(existing, incoming)
    assert merged["ports"] == {"80": "closed", "443": "open"}
    assert merged["ssl"] == {"valid": True}
    assert merged["tags"] == ["web"]


def test_deep_merge_metadata_lists():
    """Test union merging of lists."""
    existing = {"ips": ["1.1.1.1", "2.2.2.2"]}
    incoming = {"ips": ["2.2.2.2", "3.3.3.3"]}
    merged = deep_merge_metadata(existing, incoming)
    assert set(merged["ips"]) == {"1.1.1.1", "2.2.2.2", "3.3.3.3"}


def test_deep_merge_metadata_none():
    """Test merging with None values."""
    assert deep_merge_metadata(None, {"a": 1}) == {"a": 1}
    assert deep_merge_metadata({"a": 1}, None) == {"a": 1}
    assert deep_merge_metadata(None, None) == {}
