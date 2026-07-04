from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.security import decode_token
from app.services.storage import BaseStorageService, LocalFileStorageService, S3StorageService
from app.services.ai import (
    BaseAIService,
    BaseEmbeddingService,
    MockAIService,
    MockEmbeddingService,
    OpenAIService,
    OpenAIEmbeddingService,
    GeminiService,
    GeminiEmbeddingService,
)

# OAuth2 scheme extracting credentials from Authorization Bearer header
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    """FastAPI dependency to extract JWT claims and return the authenticated User."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 1. Decode token claims
    claims = decode_token(token)
    if not claims or claims.get("type") != "access":
        raise credentials_exception
        
    user_id = claims.get("sub")
    if not user_id:
        raise credentials_exception
        
    # 2. Retrieve user from DB
    repo = UserRepository(db)
    user = await repo.get(user_id)
    if not user:
        raise credentials_exception
        
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency verifying the user account is verified and active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account. Please verify your email."
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Dependency verifying the active user has administrator privileges."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges"
        )
    return current_user


def get_storage_service() -> BaseStorageService:
    """FastAPI dependency to inject storage provider (Local filesystem fallback vs S3)."""
    if settings.S3_ACCESS_KEY and settings.S3_SECRET_KEY:
        return S3StorageService()
    return LocalFileStorageService()


def get_embedding_service() -> BaseEmbeddingService:
    """FastAPI dependency to inject text vectorization provider (Gemini vs OpenAI vs Mock)."""
    if settings.GEMINI_API_KEY:
        return GeminiEmbeddingService()
    elif settings.OPENAI_API_KEY:
        return OpenAIEmbeddingService()
    return MockEmbeddingService()


def get_ai_service() -> BaseAIService:
    """FastAPI dependency to inject LLM chat provider (Gemini vs OpenAI vs Mock)."""
    if settings.GEMINI_API_KEY:
        return GeminiService()
    elif settings.OPENAI_API_KEY:
        return OpenAIService()
    return MockAIService()
