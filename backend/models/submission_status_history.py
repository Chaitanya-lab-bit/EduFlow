from datetime import datetime, timezone
from sqlalchemy import (
    String, Text, DateTime,
    ForeignKey, Index, Enum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.extensions import db
from backend.models.enums import SubmissionStatus

class SubmissionStatusHistory(db.Model):
    __tablename__ = "submission_status_history"

    history_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    submission_id: Mapped[str] = mapped_column(
        String(96),
        ForeignKey("submission.submission_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    old_status: Mapped[SubmissionStatus | None] = mapped_column(
        Enum(SubmissionStatus, native_enum=False, length=32),
        nullable=True
    )
    new_status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, native_enum=False, length=32),
        nullable=False
    )
    changed_by: Mapped[str] = mapped_column(String(64), nullable=False)
    change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )

    # Relationships
    submission = relationship("Submission", back_populates="status_history")

    __table_args__ = (
        Index("idx_ssh_submission", "submission_id"),
        Index("idx_ssh_changed_at", "changed_at"),
    )

    def __repr__(self) -> str:
        return f"<SubmissionStatusHistory {self.history_id} ({self.old_status} -> {self.new_status})>"
