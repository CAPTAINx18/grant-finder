from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.schemas.user import (
    UserCreate,
    UserResponse,
    Token,
    TokenRefresh,
    EmailVerificationRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.services.user_service import UserService
from app.services.security import create_access_token, create_refresh_token, decode_token

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)) -> Any:
    """Register a new user account."""
    service = UserService(db)
    try:
        user = await service.register_user(email=user_in.email, password=user_in.password)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Authenticate email and password credentials to retrieve JWT access & refresh tokens."""
    service = UserService(db)
    user = await service.authenticate(email=form_data.username, password=form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address to activate your account."
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(subject=user.id, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(subject=user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_in: TokenRefresh,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Issue a new access token using a valid refresh token."""
    claims = decode_token(refresh_in.refresh_token)
    if not claims or claims.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
        
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token claims"
        )
        
    service = UserService(db)
    user = await service.repo.get(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or not found"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(subject=user.id, expires_delta=access_token_expires)
    # Re-issue refresh token as well for sliding window sessions
    new_refresh_token = create_refresh_token(subject=user.id)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/verify-email")
async def verify_email(
    verify_in: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Verify user registration and activate account."""
    service = UserService(db)
    success = await service.verify_email(token=verify_in.token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification failed. Invalid or expired token."
        )
    return {"message": "Email verified and account activated successfully."}


@router.post("/password-reset-request")
async def request_password_reset(
    request_in: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Request a password reset link email."""
    service = UserService(db)
    await service.request_password_reset(email=request_in.email)
    # Always return success to prevent user email harvesting/probing attacks
    return {"message": "If the email exists, a password reset link has been sent."}


@router.post("/password-reset-confirm")
async def reset_password(
    confirm_in: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Reset password using the recovery token."""
    service = UserService(db)
    success = await service.reset_password(token=confirm_in.token, new_password=confirm_in.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset failed. Invalid or expired recovery token."
        )
    return {"message": "Password reset successfully."}


from app.api.deps import get_current_active_user
from app.models.user import User

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Retrieve details of the currently authenticated user."""
    return current_user
