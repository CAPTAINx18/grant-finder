from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from app.models.base import Base, UUIDMixin, TimestampMixin


class GrantProvider(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "grant_providers"

    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    website: Mapped[str] = mapped_column(String(512), nullable=True)
    provider_type: Mapped[str] = mapped_column(String(100), nullable=True)  # Government, NGO, University, Corporate, etc.

    # Relationships
    grants: Mapped[List["Grant"]] = relationship(back_populates="provider", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<GrantProvider {self.name}>"
