from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    String, Text, Numeric, Integer, Boolean,
    ForeignKey, UniqueConstraint, CheckConstraint, Index, Enum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.extensions import db
from backend.models.enums import SubmissionStatus
from backend.models.types import UTCDateTime

class Submission(db.Model):
    __tablename__ = "submission"

    submission_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    assignment_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("assignment.assignment_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    learner_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("learner.learner_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    enrollment_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("enrollment.enrollment_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    submitted_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, native_enum=False, length=32),
        nullable=False,
        default=SubmissionStatus.SUBMITTED,
        index=True
    )
    is_late: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    late_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    late_penalty_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    raw_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    final_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    learner_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    learner = relationship("Learner", back_populates="submissions")
    enrollment = relationship("Enrollment", back_populates="submissions")
    artifacts = relationship(
        "SubmissionArtifact",
        back_populates="submission",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    grade = relationship("Grade", back_populates="submission", uselist=False, passive_deletes="all")
    feedback_entries = relationship("Feedback", back_populates="submission", passive_deletes="all")
    status_history = relationship(
        "SubmissionStatusHistory",
        back_populates="submission",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    resubmissions_as_original = relationship(
        "Resubmission",
        foreign_keys="Resubmission.original_submission_id",
        back_populates="original_submission",
        passive_deletes="all"
    )
    resubmission_as_new = relationship(
        "Resubmission",
        foreign_keys="Resubmission.new_submission_id",
        back_populates="new_submission",
        uselist=False,
        passive_deletes="all"
    )
    appeals = relationship("Appeal", back_populates="submission", passive_deletes="all")

    __table_args__ = (
        UniqueConstraint("assignment_id", "learner_id", "attempt_number", name="uq_submission_attempt"),
        CheckConstraint("attempt_number >= 1", name="chk_submission_attempt"),
        CheckConstraint("late_duration_seconds >= 0", name="chk_submission_late_duration"),
        CheckConstraint(
            "late_penalty_percentage >= 0 AND late_penalty_percentage <= 100",
            name="chk_submission_late_penalty"
        ),
        CheckConstraint(
            "(raw_score IS NULL OR raw_score >= 0) AND (final_score IS NULL OR final_score >= 0)",
            name="chk_submission_scores"
        ),
        Index("idx_submission_assignment", "assignment_id"),
        Index("idx_submission_learner", "learner_id"),
        Index("idx_submission_status", "status"),
        Index("idx_submission_submitted_at", "submitted_at"),
        Index("idx_submission_lookup", "assignment_id", "learner_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Submission {self.submission_id} (Attempt #{self.attempt_number}, Status: {self.status})>"
