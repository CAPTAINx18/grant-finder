from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin, TimestampMixin


class GrantSourceRegistry(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "grant_source_registry"

    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    update_method: Mapped[str] = mapped_column(String(50), nullable=False)  # RSS, Sitemap, API, Scraper
    cron_schedule: Mapped[str] = mapped_column(String(50), default="0 0 * * *", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # SUCCESS, FAILED, RUNNING
    last_run_error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    metadata_json: Mapped[Optional[Any]] = mapped_column(JSON, default=dict, nullable=True)

    def __repr__(self) -> str:
        return f"<GrantSource {self.name} [{self.update_method}]>"
