from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    String, Text, Numeric, DateTime,
    ForeignKey, UniqueConstraint, CheckConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.extensions import db

class GradeCriterionScore(db.Model):
    __tablename__ = "grade_criterion_score"

    score_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    grade_id: Mapped[str] = mapped_column(
        String(112),
        ForeignKey("grade.grade_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    criterion_id: Mapped[str] = mapped_column(
        String(96),
        ForeignKey("rubric_criterion.criterion_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    score_awarded: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    evaluator_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    grade = relationship("Grade", back_populates="criterion_scores")
    criterion = relationship("RubricCriterion", back_populates="criterion_scores")

    __table_args__ = (
        UniqueConstraint("grade_id", "criterion_id", name="uq_grade_criterion"),
        CheckConstraint("score_awarded >= 0", name="chk_criterion_score_awarded"),
        Index("idx_gcs_grade", "grade_id"),
        Index("idx_gcs_criterion", "criterion_id"),
    )

    def __repr__(self) -> str:
        return f"<GradeCriterionScore {self.score_id} (Grade: {self.grade_id}, Score: {self.score_awarded})>"
