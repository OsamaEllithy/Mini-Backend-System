"""
Import Service - bulk asset import with deduplication.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.repositories.asset_repository import AssetRepository
from app.repositories.tag_repository import TagRepository
from app.schemas.asset import BulkImportRequest, BulkImportResponse
from app.utils.deduplication import check_duplicate, merge_asset


class ImportService:
    """Handles bulk asset import with intelligent deduplication."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.asset_repo = AssetRepository(db)
        self.tag_repo = TagRepository(db)

    async def bulk_import(self, request: BulkImportRequest) -> BulkImportResponse:
        """
        Process a bulk import of assets.

        For each asset in the batch:
        1. Check for existing asset by (type, value).
        2. If exists: update last_seen, merge tags (no duplicates),
           merge metadata (deep merge), reactivate stale assets.
        3. If new: create with first_seen = last_seen = now().

        Returns:
            Import summary with created/updated/error counts.
        """
        created_count = 0
        updated_count = 0
        error_count = 0
        errors: list[str] = []

        for idx, item in enumerate(request.assets):
            try:
                existing = await check_duplicate(
                    self.db, item.type.value, item.value
                )

                if existing:
                    # ── Update existing asset ──
                    await merge_asset(
                        db=self.db,
                        existing=existing,
                        incoming_tags=item.tags,
                        incoming_metadata=item.metadata,
                        incoming_source=item.source,
                    )
                    updated_count += 1
                else:
                    # ── Create new asset ──
                    now = datetime.now(timezone.utc)
                    asset = Asset(
                        type=item.type.value,
                        value=item.value,
                        status="active",
                        source=item.source,
                        first_seen=now,
                        last_seen=now,
                        metadata_=item.metadata or {},
                    )
                    asset = await self.asset_repo.create(asset)

                    # Associate tags
                    if item.tags:
                        tags = await self.tag_repo.get_multiple_or_create(item.tags)
                        asset.tags = tags
                        await self.db.flush()

                    created_count += 1

            except Exception as e:
                error_count += 1
                errors.append(
                    f"Item {idx} ({item.type.value}:{item.value}): {str(e)}"
                )

        return BulkImportResponse(
            created_count=created_count,
            updated_count=updated_count,
            error_count=error_count,
            errors=errors,
            total_processed=len(request.assets),
        )
