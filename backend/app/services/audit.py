from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def write_audit(
    db: Session,
    *,
    actor: str,
    action: str,
    tenant_id: str | None = None,
    target: str = "",
    metadata: dict | None = None,
) -> AuditLog:
    row = AuditLog(
        actor=actor,
        tenant_id=tenant_id,
        action=action,
        target=target,
        metadata_json=metadata or {},
    )
    db.add(row)
    return row
