from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Index, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.extensions import db
from backend.models.enums import EnrollmentStatus

class Learner(db.Model):
    __tablename__ = "learner"

    learner_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    student_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(EnrollmentStatus, native_enum=False, length=32),
        nullable=False,
        default=EnrollmentStatus.ACTIVE
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
    enrollments = relationship("Enrollment", back_populates="learner", passive_deletes="all")
    submissions = relationship("Submission", back_populates="learner", passive_deletes="all")
    appeals = relationship("Appeal", back_populates="learner", passive_deletes="all")

    __table_args__ = (
        Index("idx_learner_email", "email"),
        Index("idx_learner_student_number", "student_number"),
    )

    def __repr__(self) -> str:
        return f"<Learner {self.learner_id} ({self.email})>"
