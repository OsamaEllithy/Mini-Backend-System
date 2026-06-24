"""
Pydantic schemas for Relationship CRUD and graph retrieval.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RelationshipType(str, Enum):
    """Valid relationship types between assets."""
    SUBDOMAIN_OF = "subdomain_of"
    SERVICE_ON = "service_on"
    CERT_FOR = "cert_for"
    TECH_ON = "tech_on"


# Mapping of relationship type → (valid source types, valid target types)
VALID_RELATIONSHIP_RULES: dict[str, tuple[list[str], list[str]]] = {
    "subdomain_of": (["subdomain"], ["domain"]),
    "service_on": (["service"], ["ip_address"]),
    "cert_for": (["certificate"], ["domain", "subdomain"]),
    "tech_on": (["technology"], ["service", "subdomain"]),
}


class RelationshipCreate(BaseModel):
    """Schema for creating a new relationship between assets."""
    source_asset_id: UUID
    target_asset_id: UUID
    relationship_type: RelationshipType


class RelationshipResponse(BaseModel):
    """Full relationship response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_asset_id: UUID
    target_asset_id: UUID
    relationship_type: str
    created_at: datetime


class RelationshipWithAssets(RelationshipResponse):
    """Relationship response with embedded asset summaries."""
    source_asset_value: Optional[str] = None
    source_asset_type: Optional[str] = None
    target_asset_value: Optional[str] = None
    target_asset_type: Optional[str] = None


class GraphNode(BaseModel):
    """A node in the asset relationship graph."""
    id: UUID
    type: str
    value: str
    status: str


class GraphEdge(BaseModel):
    """An edge in the asset relationship graph."""
    id: UUID
    source_id: UUID
    target_id: UUID
    relationship_type: str


class AssetGraphResponse(BaseModel):
    """Asset graph containing nodes and edges."""
    root_asset: GraphNode
    nodes: list[GraphNode]
    edges: list[GraphEdge]
