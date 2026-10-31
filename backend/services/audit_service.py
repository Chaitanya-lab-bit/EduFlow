from datetime import datetime, timezone
from backend.extensions import db
from backend.models.audit_log import AuditLog
from backend.models.enums import AuditActionType

class AuditService:
    @staticmethod
    def create_audit_entry(
        audit_id: str,
        entity_name: str,
        entity_id: str,
        action: AuditActionType,
        actor_id: str,
        actor_role: str = "system",
        old_values: dict | None = None,
        new_values: dict | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """
        Record an immutable audit entry in the audit log.
        Does not allow modifying or deleting existing audit logs.
        """
        entry = AuditLog(
            audit_id=audit_id,
            entity_name=entity_name,
            entity_id=entity_id,
            action=action,
            actor_id=actor_id,
            actor_role=actor_role,
            timestamp=datetime.now(timezone.utc),
            old_values=old_values,
            new_values=new_values,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        db.session.add(entry)
        return entry
