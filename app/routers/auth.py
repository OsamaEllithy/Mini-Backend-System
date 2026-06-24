"""
Authentication API routes.
"""

from fastapi import APIRouter, status

from app.core.dependencies import DbSession
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(data: UserCreate, db: DbSession):
    """
    Register a new user.
    Required for getting an access token to perform write operations.
    """
    service = AuthService(db)
    return await service.register(data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login to get access token",
)
async def login(data: LoginRequest, db: DbSession):
    """
    Authenticate and return a JWT token.
    Pass this token in the Authorization header as 'Bearer <token>'.
    """
    service = AuthService(db)
    return await service.login(data)
