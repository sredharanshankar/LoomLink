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
    from sqlalchemy import text
    from app.core.time import now
    from app.core.events import publish

    ts = now()
    params: dict = {"jid": str(job_id), "mid": str(machine_id), "now": ts}
    sql = "UPDATE jobs SET machine_id = :mid, updated_at = :now"
    if queue_position is not None:
        sql += ", queue_position = :qp"
        params["qp"] = queue_position
    sql += " WHERE id = :jid"
    session.execute(text(sql), params)
    publish(session, "job.assigned", {
        "job_id": str(job_id), "machine_id": str(machine_id), "reason": reason,
    }, actor_id=actor_id)


def reorder_queue(
    session: Session,
    machine_id: uuid.UUID,
    job_ids_in_order: list[uuid.UUID],
    actor_id: uuid.UUID | None,
    reason: str,
) -> None:
    """Reorder jobs on a machine queue."""
    from sqlalchemy import text
    from app.core.time import now
    from app.core.events import publish

    ts = now()
    for pos, jid in enumerate(job_ids_in_order, start=1):
        session.execute(
            text("UPDATE jobs SET queue_position = :pos, updated_at = :now WHERE id = :id AND machine_id = :mid"),
            {"pos": pos, "id": str(jid), "mid": str(machine_id), "now": ts},
        )
    publish(session, "job.reordered", {
        "machine_id": str(machine_id),
        "job_ids": [str(j) for j in job_ids_in_order],
        "reason": reason,
    }, actor_id=actor_id)


def split_job(
    session: Session,
    job_id: uuid.UUID,
    parts_qty: list[int],
    actor_id: uuid.UUID | None,
    reason: str,
) -> list[uuid.UUID]:
    """Split a job into child jobs of given quantities; returns new job IDs."""
    from sqlalchemy import text
    from app.core.time import now
    from app.core.events import publish
    from app.core.ids import next_code

    row = session.execute(
        text("SELECT order_id, stage, seq, unit, planned_qty, machine_id FROM jobs WHERE id = :jid"),
        {"jid": str(job_id)},
    ).fetchone()
    if row is None:
        from app.core.errors import AppError
        raise AppError("NOT_FOUND", f"Job {job_id} not found")

    ts = now()
    new_ids: list[uuid.UUID] = []
    for qty in parts_qty:
        nid = uuid.uuid4()
        code = next_code(session, "job")
        session.execute(
            text(
                "INSERT INTO jobs (id, code, order_id, stage, seq, unit, planned_qty, produced_qty, waste_qty, "
                "machine_id, status, split_from_job_id, created_at) "
                "VALUES (:id, :code, :oid, :stage, :seq, :unit, :qty, 0, 0, :mid, 'planned', :parent, :now)"
            ),
            {
                "id": str(nid), "code": code, "oid": str(row.order_id), "stage": row.stage,
                "seq": row.seq, "unit": row.unit, "qty": qty,
                "mid": str(row.machine_id) if row.machine_id else None,
                "parent": str(job_id), "now": ts,
            },
        )
        new_ids.append(nid)

    new_total = sum(parts_qty)
    session.execute(
        text("UPDATE jobs SET planned_qty = planned_qty - :n, updated_at = :now WHERE id = :jid"),
        {"n": new_total, "jid": str(job_id), "now": ts},
    )
    publish(session, "job.split", {
        "parent_job_id": str(job_id),
        "new_job_ids": [str(i) for i in new_ids],
        "reason": reason,
    }, actor_id=actor_id)
    return new_ids


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
    from sqlalchemy import text
    from app.core.time import now
    from app.core.events import publish

    existing = session.execute(
        text(
            "SELECT id FROM shift_assignments "
            "WHERE worker_id = :wid AND date = :date AND shift_code = :sc"
        ),
        {"wid": str(worker_id) if worker_id else None, "date": date, "sc": shift_code},
    ).fetchone()
    if existing:
        return uuid.UUID(str(existing.id))

    sa_id = uuid.uuid4()
    session.execute(
        text(
            "INSERT INTO shift_assignments (id, worker_id, machine_id, date, shift_code, note, created_at) "
            "VALUES (:id, :wid, :mid, :date, :sc, :note, :now)"
        ),
        {
            "id": str(sa_id), "wid": str(worker_id) if worker_id else None,
            "mid": str(machine_id), "date": date, "sc": shift_code,
            "note": f"OT: {reason}", "now": now(),
        },
    )
    publish(session, "overtime.assigned", {
        "shift_assignment_id": str(sa_id), "machine_id": str(machine_id),
        "date": str(date), "shift_code": shift_code, "reason": reason,
    }, actor_id=actor_id)
    return sa_id


def expedite_purchase(
    session: Session,
    po_id: uuid.UUID,
    new_expected_date: dt.date,
    actor_id: uuid.UUID | None,
    reason: str,
) -> None:
    """Bring forward a purchase order's expected delivery date."""
    from sqlalchemy import text
    from app.core.time import now
    from app.core.events import publish

    session.execute(
        text("UPDATE purchase_orders SET expected_date = :d, updated_at = :now WHERE id = :id"),
        {"d": new_expected_date, "now": now(), "id": str(po_id)},
    )
    publish(session, "po.expedited", {
        "po_id": str(po_id), "new_expected_date": str(new_expected_date), "reason": reason,
    }, actor_id=actor_id)


def record_machine_signal(
    session: Session,
    machine_id: uuid.UUID,
    kind: str,
    params: dict,
    source: str,
) -> None:
    """Record a machine event from the simulator or voice (source label preserved)."""
    from sqlalchemy import text
    from app.core.time import now
    import json

    session.execute(
        text(
            "INSERT INTO machine_events (id, machine_id, kind, params, source, created_at) "
            "VALUES (:id, :mid, :kind, :params::jsonb, :source, :now)"
        ),
        {
            "id": str(uuid.uuid4()), "mid": str(machine_id), "kind": kind,
            "params": json.dumps(params), "source": source, "now": now(),
        },
    )


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
    from sqlalchemy import text

    row = session.execute(
        text(
            "SELECT o.code, o.status, o.quantity_cm, o.dispatch_by, o.dispatched_at, "
            "o.fabric_description, b.name as buyer_name "
            "FROM orders o "
            "JOIN buyers b ON b.id = o.buyer_id "
            "WHERE o.tracking_token = :tok AND o.deleted_at IS NULL"
        ),
        {"tok": tracking_token},
    ).fetchone()
    if row is None:
        return None

    return {
        "order_code": row.code,
        "status": row.status,
        "quantity_cm": row.quantity_cm,
        "dispatch_by": str(row.dispatch_by) if row.dispatch_by else None,
        "dispatched_at": row.dispatched_at.isoformat() if row.dispatched_at else None,
        "fabric_description": row.fabric_description,
        "buyer_name": row.buyer_name,
    }


def find_buyer_by_phone(session: Session, phone_e164: str) -> dict | None:
    """Return {buyer_id, name, open_orders:[{order_id, code, tracking_token}]} or None."""
    from sqlalchemy import text

    buyer = session.execute(
        text("SELECT id, name FROM buyers WHERE phone = :ph AND is_active = true"),
        {"ph": phone_e164},
    ).fetchone()
    if buyer is None:
        return None

    orders = session.execute(
        text(
            "SELECT id, code, tracking_token FROM orders "
            "WHERE buyer_id = :bid AND status NOT IN ('cancelled','delivered') AND deleted_at IS NULL "
            "ORDER BY created_at DESC LIMIT 20"
        ),
        {"bid": str(buyer.id)},
    ).fetchall()

    return {
        "buyer_id": str(buyer.id),
        "name": buyer.name,
        "open_orders": [
            {"order_id": str(o.id), "code": o.code, "tracking_token": o.tracking_token}
            for o in orders
        ],
    }


# ---------------------------------------------------------------------------
# B-functions: implemented by Lane B; called by Lane A for dashboards/order detail
# ---------------------------------------------------------------------------

def get_order_health(session: Session, order_id: uuid.UUID) -> dict | None:
    """Return {health, slack_minutes, predicted_dispatch_at, confidence_minutes} or None.

    Safe default until Lane B implements: returns None so callers handle absence.
    """
    return None


def get_orders_health(session: Session, order_ids: list[uuid.UUID]) -> dict[uuid.UUID, dict]:
    """Return mapping of order_id -> health dict for all requested orders.

    Safe default until Lane B implements: returns empty dict.
    """
    return {}


def get_open_ripple_count(session: Session) -> int:
    """Return count of open Ripple events.

    Safe default until Lane B implements: returns 0.
    """
    return 0


def get_leak_today(session: Session) -> dict:
    """Return {total_paise, by_category} for today's leak entries.

    Safe default until Lane B implements: returns zero totals.
    """
    return {"total_paise": 0, "by_category": {}}
