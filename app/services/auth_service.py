"""
Auth Service - business logic for user registration and login.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate


class AuthService:
    """Business logic for authentication and user management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def register(self, data: UserCreate) -> User:
        """
        Register a new user.

        Raises:
            HTTPException 409: If username or email already exists.
        """
        # Check if username exists
        existing_username = await self.user_repo.get_by_username(data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already registered",
            )

        # Check if email exists
        existing_email = await self.user_repo.get_by_email(data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        # Create user
        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
        )
        return await self.user_repo.create(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        """
        Authenticate a user and return a JWT access token.

        Raises:
            HTTPException 401: If authentication fails.
        """
        user = await self.user_repo.get_by_username(data.username)

        # Verify user exists, is active, and password matches
        if not user or not user.is_active or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create access token
        access_token = create_access_token(data={"sub": user.username})

        return TokenResponse(access_token=access_token)
