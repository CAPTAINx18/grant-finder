import uuid
from typing import Optional, Any
from sqlalchemy import String, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class SearchHistory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "search_history"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    query_text: Mapped[str] = mapped_column(String(512), nullable=False)
    filters: Mapped[Optional[Any]] = mapped_column(JSON, default=dict, nullable=True)
    results_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="search_histories")

    def __repr__(self) -> str:
        return f"<SearchHistory User:{self.user_id} Query:'{self.query_text}'>"
