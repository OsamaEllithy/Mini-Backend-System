"""
Pydantic schemas for Asset CRUD, filtering, and bulk import.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ─── Enums ──────────────────────────────────────────────────────────────────────

class AssetType(str, Enum):
    """Valid asset types in the ASM system."""
    DOMAIN = "domain"
    SUBDOMAIN = "subdomain"
    IP_ADDRESS = "ip_address"
    SERVICE = "service"
    CERTIFICATE = "certificate"
    TECHNOLOGY = "technology"


class AssetStatus(str, Enum):
    """Lifecycle status of an asset."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    STALE = "stale"
    REMOVED = "removed"


# ─── Tag (inline for asset responses) ───────────────────────────────────────────

class TagInline(BaseModel):
    """Minimal tag representation embedded in asset responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


# ─── Relationship (inline for asset responses) ──────────────────────────────────

class RelationshipInline(BaseModel):
    """Minimal relationship representation for asset detail views."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_asset_id: UUID
    target_asset_id: UUID
    relationship_type: str
    created_at: datetime


# ─── Asset Schemas ──────────────────────────────────────────────────────────────

class AssetCreate(BaseModel):
    """Schema for creating a new asset."""
    type: AssetType
    value: str = Field(..., min_length=1, max_length=500)
    status: AssetStatus = AssetStatus.ACTIVE
    source: Optional[str] = Field(None, max_length=200)
    tags: list[str] = Field(default_factory=list, description="List of tag names")
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict)


class AssetUpdate(BaseModel):
    """Schema for updating an existing asset. All fields optional."""
    type: Optional[AssetType] = None
    value: Optional[str] = Field(None, min_length=1, max_length=500)
    status: Optional[AssetStatus] = None
    source: Optional[str] = Field(None, max_length=200)
    tags: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None


class AssetResponse(BaseModel):
    """Full asset response with tags and relationships."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: AssetType
    value: str
    status: AssetStatus
    source: Optional[str]
    first_seen: datetime
    last_seen: datetime
    metadata: Optional[dict[str, Any]] = Field(None, alias="metadata_")
    tags: list[TagInline] = []
    created_at: datetime
    updated_at: datetime


class AssetDetailResponse(AssetResponse):
    """Asset response with relationship details for single-asset views."""
    source_relationships: list[RelationshipInline] = []
    target_relationships: list[RelationshipInline] = []


class AssetListResponse(BaseModel):
    """Paginated list of assets."""
    items: list[AssetResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ─── Bulk Import Schemas ────────────────────────────────────────────────────────

class AssetImportItem(BaseModel):
    """Single asset in a bulk import payload."""
    type: AssetType
    value: str = Field(..., min_length=1, max_length=500)
    source: Optional[str] = Field(None, max_length=200)
    tags: list[str] = Field(default_factory=list)
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict)


class BulkImportRequest(BaseModel):
    """Bulk import request containing a list of assets."""
    assets: list[AssetImportItem] = Field(
        ..., min_length=1, max_length=10000
    )


class BulkImportResponse(BaseModel):
    """Summary of a bulk import operation."""
    created_count: int
    updated_count: int
    error_count: int
    errors: list[str] = []
    total_processed: int


# ─── Lifecycle Schema ───────────────────────────────────────────────────────────

class LifecycleUpdateRequest(BaseModel):
    """Schema for updating asset lifecycle status."""
    status: AssetStatus
