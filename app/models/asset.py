"""
Asset ORM model - central entity of the ASM system.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Asset(Base):
    """
    Represents a discovered internet-facing asset.

    Assets are uniquely identified by their (type, value) pair.
    Types: domain, subdomain, ip_address, service, certificate, technology.
    """

    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    value: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        index=True,
    )
    source: Mapped[str] = mapped_column(
        String(200),
        nullable=True,
        index=True,
    )
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    tags = relationship(
        "Tag",
        secondary="asset_tags",
        back_populates="assets",
        lazy="selectin",
    )
    source_relationships = relationship(
        "Relationship",
        foreign_keys="Relationship.source_asset_id",
        back_populates="source_asset",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    target_relationships = relationship(
        "Relationship",
        foreign_keys="Relationship.target_asset_id",
        back_populates="target_asset",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_asset_type_value", "type", "value", unique=True),
        Index("ix_asset_metadata", "metadata", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, type={self.type}, value={self.value})>"
