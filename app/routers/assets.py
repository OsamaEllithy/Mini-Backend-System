"""
Asset API routes.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.asset import (
    AssetCreate,
    AssetDetailResponse,
    AssetListResponse,
    AssetResponse,
    AssetUpdate,
    LifecycleUpdateRequest,
)
from app.services.asset_service import AssetService
from app.services.lifecycle_service import LifecycleService
from app.utils.filters import AssetFilterParams
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.post(
    "",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new asset",
)
async def create_asset(
    data: AssetCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Create a new asset (Requires Auth).
    Duplicate assets (same type and value) will result in a 409 Conflict.
    """
    service = AssetService(db)
    return await service.create_asset(data)


@router.get(
    "",
    response_model=AssetListResponse,
    summary="List assets",
)
async def list_assets(
    db: DbSession,
    pagination: PaginationParams = Depends(),
    filters: AssetFilterParams = Depends(),
):
    """
    Get a paginated list of assets with advanced filtering, sorting, and search.
    Publicly accessible.
    """
    service = AssetService(db)
    return await service.list_assets(
        page=pagination.page,
        page_size=pagination.page_size,
        asset_type=filters.type,
        status_filter=filters.status,
        source=filters.source,
        tag=filters.tag,
        search=filters.search,
        first_seen_after=filters.first_seen_after,
        first_seen_before=filters.first_seen_before,
        last_seen_after=filters.last_seen_after,
        last_seen_before=filters.last_seen_before,
        sort_by=filters.sort_by,
        sort_order=filters.sort_order,
    )


@router.get(
    "/{asset_id}",
    response_model=AssetDetailResponse,
    summary="Get asset by ID",
)
async def get_asset(asset_id: UUID, db: DbSession):
    """
    Retrieve a single asset by its UUID.
    Includes tags and relationship summaries.
    Publicly accessible.
    """
    service = AssetService(db)
    return await service.get_asset(asset_id)


@router.put(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Update asset",
)
async def update_asset(
    asset_id: UUID,
    data: AssetUpdate,
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Update an existing asset (Requires Auth).
    All fields are optional.
    """
    service = AssetService(db)
    return await service.update_asset(asset_id, data)


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete asset",
)
async def delete_asset(
    asset_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Soft delete an asset by setting its status to 'removed' (Requires Auth).
    """
    service = AssetService(db)
    await service.delete_asset(asset_id)


@router.post(
    "/{asset_id}/lifecycle",
    response_model=AssetResponse,
    summary="Update asset lifecycle status",
)
async def update_lifecycle(
    asset_id: UUID,
    data: LifecycleUpdateRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Explicitly update the lifecycle status of an asset (Requires Auth).
    """
    service = AssetService(db)
    update_data = AssetUpdate(status=data.status)
    return await service.update_asset(asset_id, update_data)
