"""
Relationship API routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.relationship import (
    AssetGraphResponse,
    RelationshipCreate,
    RelationshipResponse,
)
from app.services.relationship_service import RelationshipService
from app.utils.pagination import PaginationParams

router = APIRouter(tags=["Relationships"])


@router.post(
    "/relationships",
    response_model=RelationshipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create relationship",
)
async def create_relationship(
    data: RelationshipCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Create a relationship between two assets (Requires Auth).
    Validates relationship types against asset types.
    """
    service = RelationshipService(db)
    return await service.create_relationship(data)


@router.get(
    "/relationships",
    response_model=list[RelationshipResponse],
    summary="List relationships",
)
async def list_relationships(
    db: DbSession,
    relationship_type: Optional[str] = Query(None, description="Filter by type"),
    pagination: PaginationParams = Depends(),
):
    """
    List all relationships, optionally filtered by type.
    Publicly accessible.
    """
    service = RelationshipService(db)
    rels, _ = await service.list_relationships(
        relationship_type=relationship_type,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    return rels


@router.delete(
    "/relationships/{rel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete relationship",
)
async def delete_relationship(
    rel_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Delete a relationship by ID (Requires Auth).
    """
    service = RelationshipService(db)
    await service.delete_relationship(rel_id)


@router.get(
    "/assets/{asset_id}/graph",
    response_model=AssetGraphResponse,
    summary="Get asset relationship graph",
)
async def get_asset_graph(
    asset_id: UUID,
    db: DbSession,
    depth: int = Query(2, ge=1, le=5, description="BFS traversal depth"),
):
    """
    Retrieve the relationship graph starting from a specific asset.
    Returns nodes and edges up to the specified depth.
    Publicly accessible.
    """
    service = RelationshipService(db)
    return await service.get_asset_graph(asset_id, depth=depth)
