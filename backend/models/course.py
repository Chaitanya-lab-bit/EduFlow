from datetime import datetime, timezone
from sqlalchemy import String, Text, CheckConstraint, Index, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.extensions import db
from backend.models.enums import CourseStatus
from backend.models.types import UTCDateTime

class Course(db.Model):
    __tablename__ = "course"

    course_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    term: Mapped[str] = mapped_column(String(32), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    status: Mapped[CourseStatus] = mapped_column(
        Enum(CourseStatus, native_enum=False, length=32),
        nullable=False,
        default=CourseStatus.DRAFT,
        index=True
    )
    start_date: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
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
    enrollments = relationship("Enrollment", back_populates="course", passive_deletes="all")
    assignments = relationship("Assignment", back_populates="course", passive_deletes="all")

    __table_args__ = (
        CheckConstraint("end_date > start_date", name="chk_course_dates"),
        Index("idx_course_status", "status"),
        Index("idx_course_code", "code"),
    )

    def __repr__(self) -> str:
        return f"<Course {self.course_id} ({self.code})>"
