"""Service interfaces for cross-lane communication.

Lane B (Ripple) MUST only call these functions — never write directly to tables
owned by Lane A.
Lane A MUST only call the B-functions below — never import from ripple_service directly.
"""
from __future__ import annotations
import uuid
import datetime as dt
from sqlalchemy.orm import Session


# ---------------------------------------------------------------------------
# A-functions: implemented by Lane A; called by Lane B when applying fixes
# ---------------------------------------------------------------------------

def assign_job(
    session: Session,
    job_id: uuid.UUID,
    machine_id: uuid.UUID,
    queue_position: int | None,
    actor_id: uuid.UUID | None,
    reason: str,
) -> None:
    """Assign a job to a machine at the given queue position."""
    raise NotImplementedError("Lane A")


def reorder_queue(
    session: Session,
    machine_id: uuid.UUID,
    job_ids_in_order: list[uuid.UUID],
    actor_id: uuid.UUID | None,
    reason: str,
) -> None:
    """Reorder jobs on a machine queue."""
    raise NotImplementedError("Lane A")


def split_job(
    session: Session,
    job_id: uuid.UUID,
    parts_qty: list[int],
    actor_id: uuid.UUID | None,
    reason: str,
) -> list[uuid.UUID]:
    """Split a job into child jobs of given quantities; returns new job IDs."""
    raise NotImplementedError("Lane A")


def assign_overtime(
    session: Session,
    machine_id: uuid.UUID,
    date: dt.date,
    shift_code: str,
    worker_id: uuid.UUID | None,
    actor_id: uuid.UUID | None,
    reason: str,
) -> uuid.UUID:
    """Create or confirm an overtime shift assignment; returns shift_assignment UUID."""
    raise NotImplementedError("Lane A")


def expedite_purchase(
    session: Session,
    po_id: uuid.UUID,
    new_expected_date: dt.date,
    actor_id: uuid.UUID | None,
    reason: str,
) -> None:
    """Bring forward a purchase order's expected delivery date."""
    raise NotImplementedError("Lane A")


def record_machine_signal(
    session: Session,
    machine_id: uuid.UUID,
    kind: str,
    params: dict,
    source: str,
) -> None:
    """Record a machine event from the simulator or voice (source label preserved)."""
    raise NotImplementedError("Lane A")


def notify(
    session: Session,
    *,
    user_id: uuid.UUID | None = None,
    role: str | None = None,
    type: str,
    title_key: str,
    params: dict | None = None,
    link: str | None = None,
) -> uuid.UUID:
    """Insert a notification row. Can target a user or a whole role. Returns notification UUID."""
    from sqlalchemy import text
    from app.core.time import now
    import uuid as _uuid

    nid = _uuid.uuid4()
    session.execute(
        text(
            "INSERT INTO notifications (id, user_id, role, type, title_key, params, link, created_at) "
            "VALUES (:id, :uid, :role, :type, :title_key, :params, :link, :now)"
        ),
        {
            "id": nid,
            "uid": str(user_id) if user_id else None,
            "role": role,
            "type": type,
            "title_key": title_key,
            "params": params,
            "link": link,
            "now": now(),
        },
    )
    return nid


def get_public_tracking(session: Session, tracking_token: str) -> dict | None:
    """Return buyer-safe order tracking payload for the given token, or None."""
    raise NotImplementedError("Lane A")


def find_buyer_by_phone(session: Session, phone_e164: str) -> dict | None:
    """Return {buyer_id, name, open_orders:[{order_id, code, tracking_token}]} or None."""
    raise NotImplementedError("Lane A")


# ---------------------------------------------------------------------------
# B-functions: implemented by Lane B; called by Lane A for dashboards/order detail
# ---------------------------------------------------------------------------

def get_order_health(session: Session, order_id: uuid.UUID) -> dict | None:
    """Return {health, slack_minutes, predicted_dispatch_at, confidence_minutes} or None.

    Safe default until Lane B implements: returns None so callers handle absence.
    """
    from app.ripple_service.queries import get_order_health as ripple_get_order_health

    return ripple_get_order_health(session, order_id)


def get_orders_health(session: Session, order_ids: list[uuid.UUID]) -> dict[uuid.UUID, dict]:
    """Return mapping of order_id -> health dict for all requested orders.

    Safe default until Lane B implements: returns empty dict.
    """
    from app.ripple_service.queries import get_orders_health as ripple_get_orders_health

    return ripple_get_orders_health(session, order_ids)


def get_open_ripple_count(session: Session) -> int:
    """Return count of open Ripple events.

    Safe default until Lane B implements: returns 0.
    """
    from app.ripple_service.queries import get_open_ripple_count as ripple_get_open_ripple_count

    return ripple_get_open_ripple_count(session)


def get_leak_today(session: Session) -> dict:
    """Return {total_paise, by_category} for today's leak entries.

    Safe default until Lane B implements: returns zero totals.
    """
    from app.ripple_service.queries import get_leak_today as ripple_get_leak_today

    return ripple_get_leak_today(session)
