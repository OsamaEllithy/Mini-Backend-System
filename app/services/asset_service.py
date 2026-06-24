"""
Asset Service - business logic for asset CRUD operations.
"""

import math
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.repositories.asset_repository import AssetRepository
from app.repositories.tag_repository import TagRepository
from app.schemas.asset import (
    AssetCreate,
    AssetDetailResponse,
    AssetListResponse,
    AssetResponse,
    AssetUpdate,
)
from app.utils.pagination import PaginationParams


class AssetService:
    """Business logic for asset operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.asset_repo = AssetRepository(db)
        self.tag_repo = TagRepository(db)

    async def create_asset(self, data: AssetCreate) -> Asset:
        """
        Create a new asset with tags.

        Raises:
            HTTPException 409: If an asset with the same type+value already exists.
        """
        # Check for duplicate
        existing = await self.asset_repo.get_by_type_and_value(
            data.type.value, data.value
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Asset with type '{data.type.value}' and value '{data.value}' already exists",
            )

        now = datetime.now(timezone.utc)
        asset = Asset(
            type=data.type.value,
            value=data.value,
            status=data.status.value,
            source=data.source,
            first_seen=now,
            last_seen=now,
            metadata_=data.metadata or {},
        )

        # Create asset first
        asset = await self.asset_repo.create(asset)

        # Associate tags
        if data.tags:
            tags = await self.tag_repo.get_multiple_or_create(data.tags)
            asset.tags = tags
            await self.db.flush()

        return asset

    async def get_asset(self, asset_id: UUID) -> Asset:
        """
        Get a single asset by ID.

        Raises:
            HTTPException 404: If asset not found.
        """
        asset = await self.asset_repo.get_by_id(asset_id)
        if asset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset with ID '{asset_id}' not found",
            )
        return asset

    async def list_assets(
        self,
        page: int = 1,
        page_size: int = 50,
        asset_type: Optional[str] = None,
        status_filter: Optional[str] = None,
        source: Optional[str] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        first_seen_after: Optional[datetime] = None,
        first_seen_before: Optional[datetime] = None,
        last_seen_after: Optional[datetime] = None,
        last_seen_before: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> AssetListResponse:
        """List assets with filtering, sorting, and pagination."""
        assets, total = await self.asset_repo.get_all(
            page=page,
            page_size=page_size,
            asset_type=asset_type,
            status=status_filter,
            source=source,
            tag=tag,
            search=search,
            first_seen_after=first_seen_after,
            first_seen_before=first_seen_before,
            last_seen_after=last_seen_after,
            last_seen_before=last_seen_before,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        total_pages = PaginationParams.compute_total_pages(total, page_size)

        return AssetListResponse(
            items=[AssetResponse.model_validate(a) for a in assets],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_asset(self, asset_id: UUID, data: AssetUpdate) -> Asset:
        """
        Update an existing asset.

        Raises:
            HTTPException 404: If asset not found.
            HTTPException 409: If type+value change conflicts with existing asset.
        """
        asset = await self.get_asset(asset_id)

        # Check for duplicate if type or value is changing
        new_type = data.type.value if data.type else asset.type
        new_value = data.value if data.value else asset.value

        if new_type != asset.type or new_value != asset.value:
            existing = await self.asset_repo.get_by_type_and_value(new_type, new_value)
            if existing and existing.id != asset.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Asset with type '{new_type}' and value '{new_value}' already exists",
                )

        # Apply updates
        if data.type is not None:
            asset.type = data.type.value
        if data.value is not None:
            asset.value = data.value
        if data.status is not None:
            asset.status = data.status.value
        if data.source is not None:
            asset.source = data.source
        if data.metadata is not None:
            asset.metadata_ = data.metadata

        asset.updated_at = datetime.now(timezone.utc)

        # Update tags if provided
        if data.tags is not None:
            tags = await self.tag_repo.get_multiple_or_create(data.tags)
            asset.tags = tags

        return await self.asset_repo.update(asset)

    async def delete_asset(self, asset_id: UUID) -> Asset:
        """
        Soft-delete an asset (set status to 'removed').

        Raises:
            HTTPException 404: If asset not found.
        """
        asset = await self.get_asset(asset_id)
        return await self.asset_repo.soft_delete(asset)
