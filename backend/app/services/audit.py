"""Immutable audit log of sensitive actions (docs/01-product-vision.md §auditability)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlmodel import Session, desc, select

from app.models.enums import AuditActorKind
from app.models.org import AuditLog
from app.services.repository import add


def record_audit(
    session: Session,
    *,
    org_id: uuid.UUID,
    action: str,
    target_type: str,
    target_id: uuid.UUID | None = None,
    actor_kind: AuditActorKind = AuditActorKind.user,
    actor_id: str | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
) -> AuditLog:
    """Append an audit entry (append-only)."""
    return add(
        session,
        AuditLog(
            org_id=org_id,
            actor_kind=actor_kind,
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            before=before,
            after=after,
        ),
    )


def list_audit(session: Session, org_id: uuid.UUID, limit: int = 100) -> list[AuditLog]:
    return list(
        session.exec(
            select(AuditLog)
            .where(AuditLog.org_id == org_id)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        ).all()
    )
