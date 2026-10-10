from __future__ import annotations
import datetime as dt
from uuid import UUID
from sqlalchemy.orm import Session


def audit(
    session: Session,
    actor_id: UUID | None,
    action: str,
    entity: str,
    entity_id: str,
    before: dict | None = None,
    after: dict | None = None,
    ip: str | None = None,
) -> None:
    """Append an audit log entry. Call inside an open transaction."""
    from sqlalchemy import text
    import json

    session.execute(
        text("""
            INSERT INTO audit_log (actor_id, action, entity, entity_id, before, after, ip, created_at)
            VALUES (:actor_id, :action, :entity, :entity_id, :before, :after, :ip, :now)
        """),
        {
            "actor_id": str(actor_id) if actor_id else None,
            "action": action,
            "entity": entity,
            "entity_id": str(entity_id),
            "before": json.dumps(before) if before else None,
            "after": json.dumps(after) if after else None,
            "ip": ip,
            "now": dt.datetime.now(dt.timezone.utc),
        },
    )