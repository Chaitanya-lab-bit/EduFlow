from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, Index, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.extensions import db
from backend.models.enums import EnrollmentStatus

class Enrollment(db.Model):
    __tablename__ = "enrollment"

    enrollment_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    course_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("course.course_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    learner_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("learner.learner_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(EnrollmentStatus, native_enum=False, length=32),
        nullable=False,
        default=EnrollmentStatus.ACTIVE,
        index=True
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    dropped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
    course = relationship("Course", back_populates="enrollments")
    learner = relationship("Learner", back_populates="enrollments")
    submissions = relationship("Submission", back_populates="enrollment", passive_deletes="all")

    __table_args__ = (
        UniqueConstraint("course_id", "learner_id", name="uq_course_learner"),
        Index("idx_enrollment_course", "course_id"),
        Index("idx_enrollment_learner", "learner_id"),
        Index("idx_enrollment_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Enrollment {self.enrollment_id} (Course: {self.course_id}, Learner: {self.learner_id})>"
