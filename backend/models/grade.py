from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    String, Numeric, Boolean, DateTime,
    ForeignKey, CheckConstraint, Index, Enum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.extensions import db
from backend.models.enums import GradeStatus

class Grade(db.Model):
    __tablename__ = "grade"

    grade_id: Mapped[str] = mapped_column(String(112), primary_key=True)
    submission_id: Mapped[str] = mapped_column(
        String(96),
        ForeignKey("submission.submission_id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
        index=True
    )
    graded_by: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    raw_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    late_penalty_applied: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    bonus_points: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    final_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    grade_status: Mapped[GradeStatus] = mapped_column(
        Enum(GradeStatus, native_enum=False, length=32),
        nullable=False,
        default=GradeStatus.PROVISIONAL,
        index=True
    )
    graded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
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
    submission = relationship("Submission", back_populates="grade")
    criterion_scores = relationship(
        "GradeCriterionScore",
        back_populates="grade",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    feedback_entries = relationship("Feedback", back_populates="grade", passive_deletes="all")
    appeals = relationship("Appeal", back_populates="grade", passive_deletes="all")

    __table_args__ = (
        CheckConstraint(
            "raw_score >= 0 AND late_penalty_applied >= 0 AND bonus_points >= 0 AND final_score >= 0",
            name="chk_grade_scores"
        ),
        Index("idx_grade_submission", "submission_id"),
        Index("idx_grade_status", "grade_status"),
        Index("idx_grade_graded_by", "graded_by"),
    )

    def __repr__(self) -> str:
        return f"<Grade {self.grade_id} (Final: {self.final_score}, Status: {self.grade_status})>"
