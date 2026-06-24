"""
Deduplication utilities for bulk asset import.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.repositories.asset_repository import AssetRepository
from app.repositories.tag_repository import TagRepository
from app.utils.metadata_merge import deep_merge_metadata


async def check_duplicate(
    db: AsyncSession,
    asset_type: str,
    value: str,
) -> Asset | None:
    """
    Check if an asset with the given type and value already exists.

    Args:
        db: Database session.
        asset_type: The asset type (e.g., 'domain', 'ip_address').
        value: The asset value (e.g., 'example.com').

    Returns:
        The existing Asset if found, else None.
    """
    repo = AssetRepository(db)
    return await repo.get_by_type_and_value(asset_type, value)


async def merge_asset(
    db: AsyncSession,
    existing: Asset,
    incoming_tags: list[str],
    incoming_metadata: dict[str, Any] | None,
    incoming_source: str | None = None,
) -> Asset:
    """
    Merge incoming data into an existing asset during deduplication.

    Rules:
    - Update last_seen to now.
    - Merge tags without duplicates.
    - Deep-merge metadata.
    - Reactivate if status was 'stale' or 'inactive'.
    - Update source if provided.

    Args:
        db: Database session.
        existing: The existing asset from the database.
        incoming_tags: List of tag names from the import item.
        incoming_metadata: Metadata dict from the import item.
        incoming_source: Source string from the import item.

    Returns:
        The updated Asset.
    """
    now = datetime.now(timezone.utc)

    # Update last_seen
    existing.last_seen = now
    existing.updated_at = now

    # Reactivate stale/inactive assets
    if existing.status in ("stale", "inactive"):
        existing.status = "active"

    # Update source if provided
    if incoming_source:
        existing.source = incoming_source

    # Merge metadata
    existing.metadata_ = deep_merge_metadata(
        existing.metadata_, incoming_metadata
    )

    # Merge tags (union, no duplicates)
    if incoming_tags:
        tag_repo = TagRepository(db)
        existing_tag_names = {tag.name for tag in existing.tags}
        for tag_name in incoming_tags:
            normalized = tag_name.strip().lower()
            if normalized not in existing_tag_names:
                tag = await tag_repo.get_or_create(normalized)
                existing.tags.append(tag)
                existing_tag_names.add(normalized)

    await db.flush()
    return existing
