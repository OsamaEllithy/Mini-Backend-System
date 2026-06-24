"""
Pydantic schemas for authentication (login/token).
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login credentials."""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
