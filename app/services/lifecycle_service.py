"""
Lifecycle Service - logic for managing asset staleness and states.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.asset import Asset


class LifecycleService:
    """Business logic for asset lifecycle state transitions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def mark_stale_assets(self) -> int:
        """
        Find assets whose 'last_seen' is older than STALE_THRESHOLD_DAYS,
        and update their status to 'stale'.

        Returns:
            Number of assets marked as stale.
        """
        threshold_date = datetime.now(timezone.utc) - timedelta(
            days=settings.STALE_THRESHOLD_DAYS
        )

        # Update statement
        stmt = (
            update(Asset)
            .where(
                Asset.status == "active",
                Asset.last_seen < threshold_date,
            )
            .values(
                status="stale",
                updated_at=datetime.now(timezone.utc),
            )
        )

        result = await self.db.execute(stmt)
        await self.db.flush()

        return result.rowcount

    async def reactivate_asset(self, asset: Asset) -> Asset:
        """Reactivate a single stale/inactive asset."""
        now = datetime.now(timezone.utc)
        asset.status = "active"
        asset.last_seen = now
        asset.updated_at = now
        await self.db.flush()
        return asset
