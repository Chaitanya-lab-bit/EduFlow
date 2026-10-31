from datetime import datetime, timezone
from sqlalchemy import (
    String, Text, DateTime,
    ForeignKey, CheckConstraint, Index, Enum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.extensions import db
from backend.models.enums import ResubmissionStatus

class Resubmission(db.Model):
    __tablename__ = "resubmission"

    resubmission_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    original_submission_id: Mapped[str] = mapped_column(
        String(96),
        ForeignKey("submission.submission_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    new_submission_id: Mapped[str] = mapped_column(
        String(96),
        ForeignKey("submission.submission_id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
        index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[ResubmissionStatus] = mapped_column(
        Enum(ResubmissionStatus, native_enum=False, length=32),
        nullable=False,
        default=ResubmissionStatus.SUBMITTED
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
    original_submission = relationship(
        "Submission",
        foreign_keys=[original_submission_id],
        back_populates="resubmissions_as_original"
    )
    new_submission = relationship(
        "Submission",
        foreign_keys=[new_submission_id],
        back_populates="resubmission_as_new"
    )

    __table_args__ = (
        CheckConstraint(
            "original_submission_id <> new_submission_id",
            name="chk_resubmission_distinct"
        ),
        Index("idx_resubmission_original", "original_submission_id"),
        Index("idx_resubmission_new", "new_submission_id"),
    )

    def __repr__(self) -> str:
        return f"<Resubmission {self.resubmission_id} (Original: {self.original_submission_id} -> New: {self.new_submission_id})>"
