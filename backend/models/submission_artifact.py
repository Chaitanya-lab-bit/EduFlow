from datetime import datetime, timezone
from sqlalchemy import (
    String, BigInteger, Boolean, DateTime,
    ForeignKey, UniqueConstraint, CheckConstraint, Index, Enum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.extensions import db
from backend.models.enums import ArtifactType

class SubmissionArtifact(db.Model):
    __tablename__ = "submission_artifact"

    artifact_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    submission_id: Mapped[str] = mapped_column(
        String(96),
        ForeignKey("submission.submission_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    artifact_type: Mapped[ArtifactType] = mapped_column(
        Enum(ArtifactType, native_enum=False, length=64),
        nullable=False,
        index=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    submission = relationship("Submission", back_populates="artifacts")

    __table_args__ = (
        CheckConstraint("file_size_bytes > 0", name="chk_artifact_size"),
        UniqueConstraint("submission_id", "artifact_type", name="uq_submission_artifact_type"),
        Index("idx_artifact_submission", "submission_id"),
        Index("idx_artifact_type", "artifact_type"),
    )

    def __repr__(self) -> str:
        return f"<SubmissionArtifact {self.artifact_id} ({self.artifact_type}: {self.file_name})>"
