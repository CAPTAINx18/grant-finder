from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository handling all database queries for the User model."""

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a User by their email address (case-insensitive)."""
        query = select(User).where(User.email == email.lower())
        result = await self.db.execute(query)
        return result.scalars().first()
