"""
Pagination utility for API endpoints.
"""

import math
from typing import Optional

from fastapi import Query


class PaginationParams:
    """
    Dependency class for pagination query parameters.

    Usage in router:
        async def list_items(pagination: PaginationParams = Depends()):
    """

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number (1-indexed)"),
        page_size: int = Query(
            50, ge=1, le=100, description="Items per page (max 100)"
        ),
    ):
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        """Calculate SQL OFFSET from page number."""
        return (self.page - 1) * self.page_size

    @staticmethod
    def compute_total_pages(total: int, page_size: int) -> int:
        """Compute total number of pages."""
        return max(1, math.ceil(total / page_size))
