from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    String, Text, Numeric, Integer, Boolean, DateTime,
    ForeignKey, UniqueConstraint, CheckConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.extensions import db

class Rubric(db.Model):
    __tablename__ = "rubric"

    rubric_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    assignment_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("assignment.assignment_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_points: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("100.00")
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
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
    assignment = relationship("Assignment", back_populates="rubrics")
    criteria = relationship(
        "RubricCriterion",
        back_populates="rubric",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    __table_args__ = (
        UniqueConstraint("assignment_id", "version", name="uq_rubric_assignment_version"),
        CheckConstraint("total_points > 0", name="chk_rubric_total_points"),
        Index("idx_rubric_assignment", "assignment_id"),
    )

    def __repr__(self) -> str:
        return f"<Rubric {self.rubric_id} (Assignment: {self.assignment_id}, v{self.version})>"
