import uuid
from typing import Optional, Any
from sqlalchemy import String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class AuditLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # CREATE, UPDATE, DELETE, etc.
    table_name: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    record_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    details: Mapped[Optional[Any]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog Action:{self.action} User:{self.user_id}>"
