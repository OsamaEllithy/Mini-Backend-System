"""
Relationship ORM model - links between assets in the ASM graph.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Relationship(Base):
    """
    Represents a directed relationship between two assets.

    Valid relationship types:
    - subdomain_of: subdomain → domain
    - service_on: service → ip_address
    - cert_for: certificate → domain | subdomain
    - tech_on: technology → service | subdomain
    """

    __tablename__ = "relationships"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
    )
    relationship_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ORM relationships
    source_asset = relationship(
        "Asset",
        foreign_keys=[source_asset_id],
        back_populates="source_relationships",
    )
    target_asset = relationship(
        "Asset",
        foreign_keys=[target_asset_id],
        back_populates="target_relationships",
    )

    __table_args__ = (
        Index(
            "ix_relationship_unique",
            "source_asset_id",
            "target_asset_id",
            "relationship_type",
            unique=True,
        ),
        Index("ix_relationship_source", "source_asset_id"),
        Index("ix_relationship_target", "target_asset_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Relationship(id={self.id}, "
            f"type={self.relationship_type}, "
            f"source={self.source_asset_id} → target={self.target_asset_id})>"
        )
