from datetime import datetime, timezone
from sqlalchemy import (
    String, Text, DateTime,
    ForeignKey, Index, Enum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.extensions import db
from backend.models.enums import FeedbackVisibility

class Feedback(db.Model):
    __tablename__ = "feedback"

    feedback_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    grade_id: Mapped[str] = mapped_column(
        String(112),
        ForeignKey("grade.grade_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    submission_id: Mapped[str] = mapped_column(
        String(96),
        ForeignKey("submission.submission_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    author_id: Mapped[str] = mapped_column(String(64), nullable=False)
    visibility: Mapped[FeedbackVisibility] = mapped_column(
        Enum(FeedbackVisibility, native_enum=False, length=32),
        nullable=False,
        default=FeedbackVisibility.LEARNER_VISIBLE
    )
    general_comments: Mapped[str] = mapped_column(Text, nullable=False)
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)
    areas_for_improvement: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime] = mapped_column(
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
    grade = relationship("Grade", back_populates="feedback_entries")
    submission = relationship("Submission", back_populates="feedback_entries")

    __table_args__ = (
        Index("idx_feedback_grade", "grade_id"),
        Index("idx_feedback_submission", "submission_id"),
    )

    def __repr__(self) -> str:
        return f"<Feedback {self.feedback_id} (Grade: {self.grade_id}, Author: {self.author_id})>"
