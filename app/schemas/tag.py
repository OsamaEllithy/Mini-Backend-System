"""
Pydantic schemas for Tag operations.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TagCreate(BaseModel):
    """Schema for creating a new tag."""
    name: str = Field(..., min_length=1, max_length=100)


class TagResponse(BaseModel):
    """Tag response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
