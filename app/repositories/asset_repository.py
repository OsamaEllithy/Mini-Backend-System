"""
Asset Repository - all database operations for the Asset model.
"""

import math
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.asset import Asset
from app.models.tag import Tag, asset_tags


class AssetRepository:
    """Encapsulates all database queries for assets."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, asset: Asset) -> Asset:
        """Insert a new asset into the database."""
        self.db.add(asset)
        await self.db.flush()
        await self.db.refresh(asset, attribute_names=["tags"])
        return asset

    async def get_by_id(self, asset_id: UUID) -> Optional[Asset]:
        """Fetch a single asset by ID with eager-loaded tags."""
        stmt = (
            select(Asset)
            .options(selectinload(Asset.tags))
            .where(Asset.id == asset_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_type_and_value(
        self, asset_type: str, value: str
    ) -> Optional[Asset]:
        """
        Lookup asset by its deduplication key (type + value).
        Used during bulk import to detect duplicates.
        """
        stmt = (
            select(Asset)
            .options(selectinload(Asset.tags))
            .where(and_(Asset.type == asset_type, Asset.value == value))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 50,
        asset_type: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        first_seen_after: Optional[datetime] = None,
        first_seen_before: Optional[datetime] = None,
        last_seen_after: Optional[datetime] = None,
        last_seen_before: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Asset], int]:
        """
        Retrieve assets with filtering, searching, sorting, and pagination.

        Returns:
            Tuple of (assets list, total count).
        """
        stmt = select(Asset).options(selectinload(Asset.tags))
        count_stmt = select(func.count(Asset.id))

        # Apply filters
        filters = self._build_filters(
            asset_type=asset_type,
            status=status,
            source=source,
            search=search,
            first_seen_after=first_seen_after,
            first_seen_before=first_seen_before,
            last_seen_after=last_seen_after,
            last_seen_before=last_seen_before,
        )

        if filters:
            stmt = stmt.where(and_(*filters))
            count_stmt = count_stmt.where(and_(*filters))

        # Tag filter (join required)
        if tag:
            stmt = stmt.join(Asset.tags).where(Tag.name == tag)
            count_stmt = (
                select(func.count(Asset.id.distinct()))
                .select_from(Asset)
                .join(asset_tags, Asset.id == asset_tags.c.asset_id)
                .join(Tag, asset_tags.c.tag_id == Tag.id)
                .where(Tag.name == tag)
            )
            if filters:
                count_stmt = count_stmt.where(and_(*filters))

        # Get total count
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply sorting
        stmt = self._apply_sorting(stmt, sort_by, sort_order)

        # Apply pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.db.execute(stmt)
        assets = list(result.scalars().unique().all())

        return assets, total

    async def update(self, asset: Asset) -> Asset:
        """Update an existing asset (flush changes to DB)."""
        await self.db.flush()
        await self.db.refresh(asset, attribute_names=["tags"])
        return asset

    async def delete(self, asset: Asset) -> None:
        """Hard delete an asset from the database."""
        await self.db.delete(asset)
        await self.db.flush()

    async def soft_delete(self, asset: Asset) -> Asset:
        """Soft delete by setting status to 'removed'."""
        asset.status = "removed"
        asset.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return asset

    async def count_all(self) -> int:
        """Get total count of all assets."""
        result = await self.db.execute(select(func.count(Asset.id)))
        return result.scalar() or 0

    # ─── Private Helpers ─────────────────────────────────────────────────────

    def _build_filters(
        self,
        asset_type: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
        search: Optional[str] = None,
        first_seen_after: Optional[datetime] = None,
        first_seen_before: Optional[datetime] = None,
        last_seen_after: Optional[datetime] = None,
        last_seen_before: Optional[datetime] = None,
    ) -> list:
        """Build a list of SQLAlchemy filter clauses."""
        filters = []

        if asset_type:
            filters.append(Asset.type == asset_type)
        if status:
            filters.append(Asset.status == status)
        if source:
            filters.append(Asset.source.ilike(f"%{source}%"))
        if search:
            filters.append(
                or_(
                    Asset.value.ilike(f"%{search}%"),
                    Asset.source.ilike(f"%{search}%"),
                )
            )
        if first_seen_after:
            filters.append(Asset.first_seen >= first_seen_after)
        if first_seen_before:
            filters.append(Asset.first_seen <= first_seen_before)
        if last_seen_after:
            filters.append(Asset.last_seen >= last_seen_after)
        if last_seen_before:
            filters.append(Asset.last_seen <= last_seen_before)

        return filters

    def _apply_sorting(
        self, stmt: Select, sort_by: str, sort_order: str
    ) -> Select:
        """Apply sorting to a query statement."""
        # Whitelist sortable columns
        sortable_columns = {
            "created_at": Asset.created_at,
            "updated_at": Asset.updated_at,
            "first_seen": Asset.first_seen,
            "last_seen": Asset.last_seen,
            "value": Asset.value,
            "type": Asset.type,
            "status": Asset.status,
            "source": Asset.source,
        }

        column = sortable_columns.get(sort_by, Asset.created_at)

        if sort_order.lower() == "asc":
            stmt = stmt.order_by(column.asc())
        else:
            stmt = stmt.order_by(column.desc())

        return stmt
