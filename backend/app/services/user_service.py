import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.security import get_password_hash, verify_password, decode_token, create_access_token
from app.services.email import send_verification_email, send_reset_password_email

logger = logging.getLogger(__name__)


class UserService:
    """Service layer managing business logic for User lifecycle actions."""

    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def register_user(self, email: str, password: str) -> User:
        """Register a new user account with hashed password and trigger verification email."""
        # 1. Check if email already exists
        existing_user = await self.repo.get_by_email(email)
        if existing_user:
            logger.warning(f"Registration failed: User with email {email} already exists.")
            raise ValueError("A user with this email address already exists.")

        # 2. Hash password and instantiate model
        hashed = get_password_hash(password)
        new_user = User(
            email=email.lower(),
            hashed_password=hashed,
            is_active=False,  # Needs email verification to activate
            is_admin=False
        )

        # 3. Save in DB
        created_user = await self.repo.create(new_user)
        logger.info(f"User account registered successfully: {email}")

        # 4. Generate verification token and send verification email
        verify_token = create_access_token(subject=created_user.id)
        send_verification_email(created_user.email, verify_token)

        return created_user

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user credentials."""
        user = await self.repo.get_by_email(email)
        if not user:
            logger.warning(f"Authentication failed: No user found with email {email}")
            return None

        if not verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: Password mismatch for user {email}")
            return None

        logger.info(f"User authenticated successfully: {email}")
        return user

    async def verify_email(self, token: str) -> bool:
        """Verify user email address using verification token."""
        claims = decode_token(token)
        if not claims or claims.get("type") != "access":
            logger.warning("Email verification failed: Token is invalid or expired.")
            return False

        user_id = claims.get("sub")
        if not user_id:
            return False

        user = await self.repo.get(user_id)
        if not user:
            logger.warning(f"Email verification failed: User {user_id} not found.")
            return False

        if user.is_active:
            # Already active
            return True

        # Activate the user
        await self.repo.update(user, {"is_active": True})
        logger.info(f"User verified and activated successfully: {user.email}")
        return True

    async def request_password_reset(self, email: str) -> bool:
        """Trigger password reset email for specified user."""
        user = await self.repo.get_by_email(email)
        if not user:
            logger.warning(f"Password reset request ignored: No user with email {email}")
            # Return True to prevent email enumeration attacks
            return True

        # Generate reset token (expires quickly, e.g. 2 hours)
        reset_token = create_access_token(subject=user.id)
        send_reset_password_email(user.email, reset_token)
        return True

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset user password using recovery token."""
        claims = decode_token(token)
        if not claims or claims.get("type") != "access":
            logger.warning("Password reset failed: Recovery token is invalid or expired.")
            return False

        user_id = claims.get("sub")
        if not user_id:
            return False

        user = await self.repo.get(user_id)
        if not user:
            logger.warning(f"Password reset failed: User {user_id} not found.")
            return False

        hashed = get_password_hash(new_password)
        await self.repo.update(user, {"hashed_password": hashed})
        logger.info(f"Password reset successfully completed for user: {user.email}")
        return True
