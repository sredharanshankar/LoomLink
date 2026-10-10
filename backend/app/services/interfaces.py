"""Service interfaces for cross-lane communication.

Lane B (Ripple) MUST only call these functions — never write directly to tables
owned by Lane A.
"""
from __future__ import annotations
from typing import Protocol
import uuid
import datetime as dt
from sqlalchemy.orm import Session


def notify(
    session: Session,
    *,
    user_id: uuid.UUID | None = None,
    role: str | None = None,
    type: str,
    title_key: str,
    params: dict | None = None,
    link: str | None = None,
) -> None:
    """Insert a notification row. Can target a user or a whole role."""
    from sqlalchemy import text
    from app.core.time import now

    session.execute(
        text(
            "INSERT INTO notifications (id, user_id, role, type, title_key, params, link, created_at) "
            "VALUES (gen_random_uuid(), :uid, :role, :type, :title_key, :params, :link, :now)"
        ),
        {
            "uid": str(user_id) if user_id else None,
            "role": role,
            "type": type,
            "title_key": title_key,
            "params": params,
            "link": link,
            "now": now(),
        },
    )