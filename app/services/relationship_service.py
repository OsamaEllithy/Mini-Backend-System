"""
Relationship Service - business logic for asset relationship management.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.relationship import Relationship
from app.repositories.asset_repository import AssetRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.schemas.relationship import (
    AssetGraphResponse,
    GraphEdge,
    GraphNode,
    RelationshipCreate,
    VALID_RELATIONSHIP_RULES,
)


class RelationshipService:
    """Business logic for relationship operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.rel_repo = RelationshipRepository(db)
        self.asset_repo = AssetRepository(db)

    async def create_relationship(self, data: RelationshipCreate) -> Relationship:
        """
        Create a new relationship between two assets.

        Validates:
        - Both assets exist.
        - Source != Target.
        - Relationship type is valid for the given asset types.
        - No duplicate relationship exists.

        Raises:
            HTTPException 404: If either asset not found.
            HTTPException 400: If relationship type is invalid for asset types.
            HTTPException 409: If relationship already exists.
        """
        # Verify source and target are different
        if data.source_asset_id == data.target_asset_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source and target assets must be different",
            )

        # Verify both assets exist
        source_asset = await self.asset_repo.get_by_id(data.source_asset_id)
        if source_asset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source asset '{data.source_asset_id}' not found",
            )

        target_asset = await self.asset_repo.get_by_id(data.target_asset_id)
        if target_asset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target asset '{data.target_asset_id}' not found",
            )

        # Validate relationship type against asset types
        rel_type = data.relationship_type.value
        if rel_type not in VALID_RELATIONSHIP_RULES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown relationship type: '{rel_type}'",
            )

        valid_source_types, valid_target_types = VALID_RELATIONSHIP_RULES[rel_type]

        if source_asset.type not in valid_source_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Relationship '{rel_type}' requires source asset of type "
                    f"{valid_source_types}, but got '{source_asset.type}'"
                ),
            )

        if target_asset.type not in valid_target_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Relationship '{rel_type}' requires target asset of type "
                    f"{valid_target_types}, but got '{target_asset.type}'"
                ),
            )

        # Check for duplicate relationship
        existing = await self.rel_repo.get_existing(
            data.source_asset_id, data.target_asset_id, rel_type
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This relationship already exists",
            )

        # Create the relationship
        relationship = Relationship(
            source_asset_id=data.source_asset_id,
            target_asset_id=data.target_asset_id,
            relationship_type=rel_type,
        )
        return await self.rel_repo.create(relationship)

    async def list_relationships(
        self,
        relationship_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Relationship], int]:
        """List relationships with optional type filter."""
        return await self.rel_repo.get_all(
            relationship_type=relationship_type,
            page=page,
            page_size=page_size,
        )

    async def delete_relationship(self, rel_id: UUID) -> None:
        """
        Delete a relationship by ID.

        Raises:
            HTTPException 404: If relationship not found.
        """
        rel = await self.rel_repo.get_by_id(rel_id)
        if rel is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Relationship '{rel_id}' not found",
            )
        await self.rel_repo.delete(rel)

    async def get_asset_graph(
        self, asset_id: UUID, depth: int = 2
    ) -> AssetGraphResponse:
        """
        Build the relationship graph for an asset.

        Uses BFS traversal to discover connected nodes and edges.

        Raises:
            HTTPException 404: If root asset not found.
        """
        # Verify root asset exists
        root_asset = await self.asset_repo.get_by_id(asset_id)
        if root_asset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset '{asset_id}' not found",
            )

        # Traverse graph
        node_ids, edges = await self.rel_repo.get_graph(asset_id, depth=depth)

        # Fetch all node assets
        nodes = []
        for nid in node_ids:
            asset = await self.asset_repo.get_by_id(nid)
            if asset:
                nodes.append(
                    GraphNode(
                        id=asset.id,
                        type=asset.type,
                        value=asset.value,
                        status=asset.status,
                    )
                )

        # Deduplicate edges
        seen_edge_ids = set()
        unique_edges = []
        for edge in edges:
            if edge.id not in seen_edge_ids:
                seen_edge_ids.add(edge.id)
                unique_edges.append(
                    GraphEdge(
                        id=edge.id,
                        source_id=edge.source_asset_id,
                        target_id=edge.target_asset_id,
                        relationship_type=edge.relationship_type,
                    )
                )

        return AssetGraphResponse(
            root_asset=GraphNode(
                id=root_asset.id,
                type=root_asset.type,
                value=root_asset.value,
                status=root_asset.status,
            ),
            nodes=nodes,
            edges=unique_edges,
        )
