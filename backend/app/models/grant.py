import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Any
from sqlalchemy import String, Numeric, DateTime, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Grant(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "grants"

    provider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("grant_providers.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    funding_amount_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    funding_amount_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    country_eligibility: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    official_source_link: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    application_link: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    document_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    click_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bookmark_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # India-first Filtering Metadata
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    funding_currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    eligibility_country: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    # Advanced Search Columns
    search_vector: Mapped[Optional[Any]] = mapped_column(TSVECTOR, nullable=True)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536), nullable=True)

    # Relationships
    provider: Mapped["GrantProvider"] = relationship(back_populates="grants")
    eligibility_rules: Mapped[List["EligibilityRule"]] = relationship(back_populates="grant", cascade="all, delete-orphan")
    bookmarks: Mapped[List["Bookmark"]] = relationship(back_populates="grant", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Grant {self.name}>"


# Define specialized search indexes
# FTS GIN Index
Index("grants_search_vector_idx", Grant.search_vector, postgresql_using="gin")
# pgvector HNSW Index for cosine distance searches
Index(
    "grants_embedding_cosine_idx", 
    Grant.embedding, 
    postgresql_using="hnsw", 
    postgresql_ops={"embedding": "vector_cosine_ops"},
    postgresql_with={"m": 16, "ef_construction": 64}
)
