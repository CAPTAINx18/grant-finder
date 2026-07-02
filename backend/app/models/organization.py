from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin, TimestampMixin


class Organization(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    website: Mapped[str] = mapped_column(String(512), nullable=True)

    def __repr__(self) -> str:
        return f"<Organization {self.name}>"
