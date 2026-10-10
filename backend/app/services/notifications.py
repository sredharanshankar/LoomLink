"""A-M9: Notification service — create, list, mark read."""
from __future__ import annotations
import uuid
import json
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.errors import AppError
from app.core import time as app_time


def _actor(user: dict) -> uuid.UUID | None:
    raw = user.get("sub") or user.get("id")
    return uuid.UUID(str(raw)) if raw else None


def notify(
    session: Session,
    user_id: uuid.UUID,
    notif_type: str,
    payload: dict,
) -> dict:
    """Create a notification row. Called from domain event handlers."""
    now = app_time.now()
    notif_id = uuid.uuid4()
    session.execute(text("""
        INSERT INTO notifications (id, user_id, type, payload, created_at)
        VALUES (:id, :uid, :type, :payload, :now)
    """), {
        "id": notif_id,
        "uid": user_id,
        "type": notif_type,
        "payload": json.dumps(payload),
        "now": now,
    })
    return {
        "id": str(notif_id),
        "user_id": str(user_id),
        "type": notif_type,
        "payload": payload,
        "read_at": None,
        "created_at": now.isoformat(),
    }


def list_notifications(
    session: Session, user: dict, unread_only: bool = False
) -> list[dict]:
    actor_id = _actor(user)
    if actor_id is None:
        return []

    where_extra = "AND n.read_at IS NULL" if unread_only else ""

    rows = session.execute(text(f"""
        SELECT n.id, n.user_id, n.type, n.payload, n.read_at, n.created_at
        FROM notifications n
        WHERE n.user_id = :uid {where_extra}
        ORDER BY n.created_at DESC
        LIMIT 100
    """), {"uid": actor_id}).fetchall()

    return [
        {
            "id": str(r.id), "user_id": str(r.user_id),
            "type": r.type,
            "payload": json.loads(r.payload) if isinstance(r.payload, str) else r.payload,
            "read_at": r.read_at.isoformat() if r.read_at else None,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


def mark_read(session: Session, notification_id: uuid.UUID, user: dict) -> dict:
    actor_id = _actor(user)
    now = app_time.now()

    row = session.execute(text("""
        SELECT id, user_id FROM notifications WHERE id = :nid
    """), {"nid": notification_id}).fetchone()
    if row is None:
        raise AppError("NOT_FOUND", "Notification not found")
    if str(row.user_id) != str(actor_id):
        raise AppError("FORBIDDEN", "Cannot mark another user's notification")

    session.execute(text("""
        UPDATE notifications SET read_at = :now WHERE id = :nid AND read_at IS NULL
    """), {"now": now, "nid": notification_id})

    return {"id": str(notification_id), "read_at": now.isoformat()}


def mark_all_read(session: Session, user: dict) -> dict:
    actor_id = _actor(user)
    now = app_time.now()
    result = session.execute(text("""
        UPDATE notifications SET read_at = :now
        WHERE user_id = :uid AND read_at IS NULL
        RETURNING id
    """), {"now": now, "uid": actor_id})
    count = len(result.fetchall())
    return {"marked_read": count}


def get_unread_count(session: Session, user: dict) -> int:
    actor_id = _actor(user)
    if actor_id is None:
        return 0
    return int(session.execute(text("""
        SELECT COUNT(*) FROM notifications WHERE user_id = :uid AND read_at IS NULL
    """), {"uid": actor_id}).scalar() or 0)
