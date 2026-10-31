from datetime import datetime, timezone
from sqlalchemy import (
    String, Text, DateTime,
    Index, Enum, JSON
)
from sqlalchemy.orm import Mapped, mapped_column
from backend.extensions import db
from backend.models.enums import AuditActionType

class AuditLog(db.Model):
    __tablename__ = "audit_log"

    audit_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    entity_name: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[AuditActionType] = mapped_column(
        Enum(AuditActionType, native_enum=False, length=32),
        nullable=False,
        index=True
    )
    actor_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    actor_role: Mapped[str] = mapped_column(String(32), nullable=False, default="system")
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    old_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    client_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_audit_entity", "entity_name", "entity_id"),
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_actor", "actor_id"),
        Index("idx_audit_action", "action"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.audit_id} ({self.action} on {self.entity_name}:{self.entity_id} by {self.actor_id})>"
