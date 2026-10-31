from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    String, Text, Numeric, Integer, DateTime,
    ForeignKey, CheckConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.extensions import db

class RubricCriterion(db.Model):
    __tablename__ = "rubric_criterion"

    criterion_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    rubric_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("rubric.rubric_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    criterion_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_points: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, default=Decimal("1.00"))
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    rubric = relationship("Rubric", back_populates="criteria")
    criterion_scores = relationship("GradeCriterionScore", back_populates="criterion", passive_deletes="all")

    __table_args__ = (
        CheckConstraint("max_points > 0", name="chk_criterion_max_points"),
        CheckConstraint("weight > 0", name="chk_criterion_weight"),
        Index("idx_criterion_rubric", "rubric_id"),
    )

    def __repr__(self) -> str:
        return f"<RubricCriterion {self.criterion_id} ({self.criterion_name}: {self.max_points} pts)>"
