"""
Filter utilities for asset queries.
"""

from datetime import datetime
from typing import Optional

from fastapi import Query


class AssetFilterParams:
    """
    Dependency class for asset filter query parameters.

    Usage in router:
        async def list_assets(filters: AssetFilterParams = Depends()):
    """

    def __init__(
        self,
        type: Optional[str] = Query(
            None,
            description="Filter by asset type (domain, subdomain, ip_address, service, certificate, technology)",
        ),
        status: Optional[str] = Query(
            None,
            description="Filter by status (active, inactive, stale, removed)",
        ),
        source: Optional[str] = Query(
            None, description="Filter by discovery source (partial match)"
        ),
        tag: Optional[str] = Query(
            None, description="Filter by tag name"
        ),
        search: Optional[str] = Query(
            None, description="Search in asset value and source (partial match)"
        ),
        first_seen_after: Optional[datetime] = Query(
            None, description="Filter assets first seen after this datetime"
        ),
        first_seen_before: Optional[datetime] = Query(
            None, description="Filter assets first seen before this datetime"
        ),
        last_seen_after: Optional[datetime] = Query(
            None, description="Filter assets last seen after this datetime"
        ),
        last_seen_before: Optional[datetime] = Query(
            None, description="Filter assets last seen before this datetime"
        ),
        sort_by: str = Query(
            "created_at",
            description="Sort field (created_at, updated_at, first_seen, last_seen, value, type, status, source)",
        ),
        sort_order: str = Query(
            "desc", description="Sort order (asc or desc)"
        ),
    ):
        self.type = type
        self.status = status
        self.source = source
        self.tag = tag
        self.search = search
        self.first_seen_after = first_seen_after
        self.first_seen_before = first_seen_before
        self.last_seen_after = last_seen_after
        self.last_seen_before = last_seen_before
        self.sort_by = sort_by
        self.sort_order = sort_order
