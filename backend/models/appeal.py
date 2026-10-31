from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    String, Text, Numeric, DateTime,
    ForeignKey, CheckConstraint, Index, Enum, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.extensions import db
from backend.models.enums import AppealStatus, AppealReasonCategory

class Appeal(db.Model):
    __tablename__ = "appeal"

    appeal_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    submission_id: Mapped[str] = mapped_column(
        String(96),
        ForeignKey("submission.submission_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    grade_id: Mapped[str] = mapped_column(
        String(112),
        ForeignKey("grade.grade_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    learner_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("learner.learner_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    reviewed_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[AppealStatus] = mapped_column(
        Enum(AppealStatus, native_enum=False, length=32),
        nullable=False,
        default=AppealStatus.SUBMITTED,
        index=True
    )
    reason_category: Mapped[AppealReasonCategory] = mapped_column(
        Enum(AppealReasonCategory, native_enum=False, length=64),
        nullable=False
    )
    learner_statement: Mapped[str] = mapped_column(Text, nullable=False)
    contested_criteria: Mapped[list | None] = mapped_column(JSON, nullable=True)
    original_grade: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    requested_grade: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    final_grade: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
    submission = relationship("Submission", back_populates="appeals")
    grade = relationship("Grade", back_populates="appeals")
    learner = relationship("Learner", back_populates="appeals")

    __table_args__ = (
        CheckConstraint(
            "original_grade >= 0 AND (requested_grade IS NULL OR requested_grade >= 0) AND (final_grade IS NULL OR final_grade >= 0)",
            name="chk_appeal_grades"
        ),
        Index("idx_appeal_submission", "submission_id"),
        Index("idx_appeal_grade", "grade_id"),
        Index("idx_appeal_learner", "learner_id"),
        Index("idx_appeal_status", "status"),
        Index("idx_appeal_submitted_at", "submitted_at"),
    )

    def __repr__(self) -> str:
        return f"<Appeal {self.appeal_id} (Submission: {self.submission_id}, Status: {self.status})>"
