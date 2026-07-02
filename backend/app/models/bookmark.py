import uuid
from typing import Optional
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Bookmark(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "bookmarks"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    grant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("grants.id", ondelete="CASCADE"), index=True, nullable=False)
    collection_name: Mapped[Optional[str]] = mapped_column(String(100), default="General", nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    application_status: Mapped[str] = mapped_column(String(50), default="Interested", nullable=False)  # Interested, Applied, In Progress, etc.

    # Relationships
    user: Mapped["User"] = relationship(back_populates="bookmarks")
    grant: Mapped["Grant"] = relationship(back_populates="bookmarks")

    def __repr__(self) -> str:
        return f"<Bookmark User:{self.user_id} Grant:{self.grant_id}>"
