from __future__ import annotations
import asyncio
import json
import logging
import queue
import threading
import datetime as dt
from typing import Callable
from uuid import UUID
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_handlers: dict[str, list[Callable]] = {}
_dispatch_queue: queue.Queue = queue.Queue()
_loop_ref: asyncio.AbstractEventLoop | None = None
_ws_broadcast: Callable | None = None

_STATE_VERSION_TYPES = {
    "stock.received", "stock.issued", "stock.returned", "stock.adjusted", "stock.low",
    "order.created", "order.confirmed", "order.updated", "order.cancelled", "order.status_changed",
    "job.assigned", "job.reordered", "job.split", "job.started", "job.paused",
    "job.resumed", "job.finished", "job.progress", "job.handover",
    "machine.status_changed",
    "roll.created", "roll.inspected", "roll.rework_complete",
    "dispatch.updated", "dispatch.confirmed",
    "attendance.changed", "shift.overtime_assigned",
    "forecast.updated", "ripple.created", "ripple.resolved", "ripple.dismissed",
    "leak.updated",
}


def subscribe(type_or_prefix: str, handler: Callable) -> None:
    _handlers.setdefault(type_or_prefix, []).append(handler)


def set_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _loop_ref
    _loop_ref = loop


def set_ws_broadcast(fn: Callable) -> None:
    global _ws_broadcast
    _ws_broadcast = fn


def publish(
    session: Session,
    event_type: str,
    payload: dict,
    actor_id: UUID | None = None,
) -> None:
    """Insert a domain event in the same transaction; schedule post-commit dispatch."""
    from sqlalchemy import text
    from sqlalchemy import event as sa_event

    from app.core.time import now as _now
    now = _now()

    result = session.execute(
        text(
            "INSERT INTO domain_events (type, payload, actor_id, created_at) "
            "VALUES (:etype, :payload, :actor_id, :now) RETURNING id"
        ),
        {
            "etype": event_type,
            "payload": json.dumps(payload),
            "actor_id": str(actor_id) if actor_id else None,
            "now": now,
        },
    )
    event_id = result.scalar()

    if event_type in _STATE_VERSION_TYPES:
        session.execute(text("UPDATE mill_settings SET state_version = state_version + 1"))

    @sa_event.listens_for(session, "after_commit", once=True)
    def _on_commit(sess):  # noqa: ARG001
        _dispatch_queue.put(event_id)


def _dispatch_event(event_id: int) -> None:
    from app.db import SessionLocal
    from sqlalchemy import text

    with SessionLocal() as session:
        row = session.execute(
            text("SELECT type, payload, actor_id, created_at FROM domain_events WHERE id = :id"),
            {"id": event_id},
        ).fetchone()
        if row is None:
            return
        event_type, payload_str, actor_id, created_at = row
        payload = json.loads(payload_str) if payload_str else {}

    event_data = {
        "type": event_type,
        "payload": payload,
        "actor_id": actor_id,
        "ts": created_at.isoformat(),
    }

    for prefix, handlers in _handlers.items():
        if event_type == prefix or event_type.startswith(prefix):
            for handler in handlers:
                for attempt in range(3):
                    try:
                        with SessionLocal() as s2:
                            handler(s2, event_data)
                            s2.commit()
                        break
                    except Exception as exc:
                        logger.warning("Handler error attempt %d: %s", attempt + 1, exc)

    if _ws_broadcast is not None and _loop_ref is not None:
        try:
            asyncio.run_coroutine_threadsafe(
                _ws_broadcast(event_type, payload),
                _loop_ref,
            )
        except Exception as exc:
            logger.warning("WS broadcast error: %s", exc)

    from app.core.time import now as _now2
    with SessionLocal() as session:
        session.execute(
            text("UPDATE domain_events SET dispatched_at = :now WHERE id = :id"),
            {"id": event_id, "now": _now2()},
        )
        session.commit()


def _dispatch_worker() -> None:
    while True:
        event_id = _dispatch_queue.get()
        try:
            _dispatch_event(event_id)
        except Exception as exc:
            logger.exception("Failed to dispatch event %s: %s", event_id, exc)
        finally:
            _dispatch_queue.task_done()


def start_dispatcher() -> None:
    t = threading.Thread(target=_dispatch_worker, daemon=True)
    t.start()
    _recover_undispatched()


def _recover_undispatched() -> None:
    from app.db import SessionLocal
    from sqlalchemy import text

    from app.core.time import now as _now
    cutoff = _now() - dt.timedelta(seconds=5)
    try:
        with SessionLocal() as session:
            rows = session.execute(
                text(
                    "SELECT id FROM domain_events "
                    "WHERE dispatched_at IS NULL AND created_at < :cutoff ORDER BY created_at"
                ),
                {"cutoff": cutoff},
            ).fetchall()
        for row in rows:
            _dispatch_queue.put(row[0])
    except Exception as exc:
        logger.warning("Could not recover undispatched events: %s", exc)