import uuid
from typing import Any
from sqlalchemy import String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Alert(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "alerts"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    alert_type: Mapped[str] = mapped_column(String(50), default="New Grants", nullable=False)
    filters: Mapped[Any] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="alerts")

    def __repr__(self) -> str:
        return f"<Alert for User {self.user_id}>"
