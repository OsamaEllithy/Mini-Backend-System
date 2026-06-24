"""
Relationship Repository - database operations for asset relationships.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.asset import Asset
from app.models.relationship import Relationship


class RelationshipRepository:
    """Encapsulates all database queries for relationships."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, relationship: Relationship) -> Relationship:
        """Insert a new relationship."""
        self.db.add(relationship)
        await self.db.flush()
        await self.db.refresh(relationship)
        return relationship

    async def get_by_id(self, rel_id: UUID) -> Optional[Relationship]:
        """Fetch a relationship by ID."""
        stmt = select(Relationship).where(Relationship.id == rel_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        relationship_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Relationship], int]:
        """List all relationships with optional type filter and pagination."""
        from sqlalchemy import func

        stmt = select(Relationship)
        count_stmt = select(func.count(Relationship.id))

        if relationship_type:
            stmt = stmt.where(Relationship.relationship_type == relationship_type)
            count_stmt = count_stmt.where(
                Relationship.relationship_type == relationship_type
            )

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        offset = (page - 1) * page_size
        stmt = stmt.order_by(Relationship.created_at.desc()).offset(offset).limit(page_size)

        result = await self.db.execute(stmt)
        relationships = list(result.scalars().all())

        return relationships, total

    async def get_by_asset_id(self, asset_id: UUID) -> list[Relationship]:
        """Get all relationships where the asset is source or target."""
        stmt = select(Relationship).where(
            or_(
                Relationship.source_asset_id == asset_id,
                Relationship.target_asset_id == asset_id,
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_existing(
        self,
        source_asset_id: UUID,
        target_asset_id: UUID,
        relationship_type: str,
    ) -> Optional[Relationship]:
        """Check if an identical relationship already exists."""
        stmt = select(Relationship).where(
            and_(
                Relationship.source_asset_id == source_asset_id,
                Relationship.target_asset_id == target_asset_id,
                Relationship.relationship_type == relationship_type,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, relationship: Relationship) -> None:
        """Delete a relationship."""
        await self.db.delete(relationship)
        await self.db.flush()

    async def get_graph(self, asset_id: UUID, depth: int = 2) -> tuple[set, list]:
        """
        Traverse the relationship graph starting from the given asset.
        Returns all discovered nodes (asset IDs) and edges (relationships).

        Uses BFS with configurable depth.
        """
        visited_ids: set[UUID] = set()
        all_edges: list[Relationship] = []
        queue: list[tuple[UUID, int]] = [(asset_id, 0)]

        while queue:
            current_id, current_depth = queue.pop(0)

            if current_id in visited_ids:
                continue
            visited_ids.add(current_id)

            if current_depth >= depth:
                continue

            # Get all relationships for this node
            relationships = await self.get_by_asset_id(current_id)

            for rel in relationships:
                all_edges.append(rel)
                neighbor_id = (
                    rel.target_asset_id
                    if rel.source_asset_id == current_id
                    else rel.source_asset_id
                )
                if neighbor_id not in visited_ids:
                    queue.append((neighbor_id, current_depth + 1))

        return visited_ids, all_edges
