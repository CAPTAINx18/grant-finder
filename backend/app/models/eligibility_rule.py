import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class EligibilityRule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "eligibility_rules"

    grant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("grants.id", ondelete="CASCADE"), index=True, nullable=False)
    applicant_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Student, Startup, Researcher, NGO, etc.
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Healthcare, Energy, Education, etc.
    project_stage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Idea, Prototype, MVP, Research, etc.
    min_funding_required: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)

    # Relationships
    grant: Mapped["Grant"] = relationship(back_populates="eligibility_rules")

    def __repr__(self) -> str:
        return f"<EligibilityRule for Grant {self.grant_id}>"
