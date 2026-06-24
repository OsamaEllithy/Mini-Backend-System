"""
Tag Repository - database operations for tags.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag


class TagRepository:
    """Encapsulates all database queries for tags."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, name: str) -> Tag:
        """
        Get an existing tag by name, or create it if it doesn't exist.
        Normalized: tag names are stored lowercase and stripped.
        """
        normalized_name = name.strip().lower()
        stmt = select(Tag).where(Tag.name == normalized_name)
        result = await self.db.execute(stmt)
        tag = result.scalar_one_or_none()

        if tag is None:
            tag = Tag(name=normalized_name)
            self.db.add(tag)
            await self.db.flush()

        return tag

    async def get_by_name(self, name: str) -> Optional[Tag]:
        """Get a tag by name."""
        stmt = select(Tag).where(Tag.name == name.strip().lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Tag]:
        """Get all tags."""
        stmt = select(Tag).order_by(Tag.name.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_multiple_or_create(self, names: list[str]) -> list[Tag]:
        """Get or create multiple tags by name."""
        tags = []
        for name in names:
            tag = await self.get_or_create(name)
            tags.append(tag)
        return tags
