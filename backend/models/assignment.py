from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    String, Text, Numeric, Integer, ForeignKey,
    CheckConstraint, Index, Enum, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.extensions import db
from backend.models.enums import AssignmentStatus
from backend.models.types import UTCDateTime

class Assignment(db.Model):
    __tablename__ = "assignment"

    assignment_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    course_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("course.course_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("100.00")
    )
    due_date: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, index=True)
    cutoff_date: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    late_penalty_per_day: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        default=Decimal("5.00")
    )
    max_late_days: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    grace_period_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    max_resubmissions: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    required_artifact_types: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: ["report_pdf"]
    )
    status: Mapped[AssignmentStatus] = mapped_column(
        Enum(AssignmentStatus, native_enum=False, length=32),
        nullable=False,
        default=AssignmentStatus.DRAFT,
        index=True
    )
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
    course = relationship("Course", back_populates="assignments")
    rubrics = relationship("Rubric", back_populates="assignment", passive_deletes="all")
    submissions = relationship("Submission", back_populates="assignment", passive_deletes="all")

    __table_args__ = (
        CheckConstraint("max_score > 0", name="chk_assignment_max_score"),
        CheckConstraint("cutoff_date >= due_date", name="chk_assignment_dates"),
        CheckConstraint(
            "late_penalty_per_day >= 0 AND late_penalty_per_day <= 100",
            name="chk_assignment_penalty"
        ),
        CheckConstraint("grace_period_minutes >= 0", name="chk_assignment_grace"),
        CheckConstraint("max_resubmissions >= 0", name="chk_assignment_resubmissions"),
        Index("idx_assignment_course", "course_id"),
        Index("idx_assignment_status", "status"),
        Index("idx_assignment_due_date", "due_date"),
    )

    def __repr__(self) -> str:
        return f"<Assignment {self.assignment_id} ({self.title})>"
