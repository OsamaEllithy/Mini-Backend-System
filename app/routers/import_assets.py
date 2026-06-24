"""
Import API routes.
"""

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.asset import BulkImportRequest, BulkImportResponse
from app.services.import_service import ImportService

router = APIRouter(prefix="/import", tags=["Import"])


@router.post(
    "",
    response_model=BulkImportResponse,
    status_code=status.HTTP_200_OK,
    summary="Bulk import assets",
)
async def import_assets(
    data: BulkImportRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Bulk import a list of assets (Requires Auth).

    Performs intelligent deduplication:
    - Matches existing assets by (type, value).
    - If match: updates last_seen, merges tags, merges JSON metadata.
    - If new: creates the asset.
    - Reactivates stale/inactive assets upon re-discovery.
    """
    service = ImportService(db)
    return await service.bulk_import(data)
