"""A-M6: Dispatch management service — finished stock, dispatch, invoice creation."""
from __future__ import annotations
import uuid
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.errors import AppError
from app.core.ids import next_code
from app.core import time as app_time
from app.core import events as ev
from app.core.audit import audit


def _actor(user: dict) -> uuid.UUID | None:
    raw = user.get("sub") or user.get("id")
    return uuid.UUID(str(raw)) if raw else None


# ---------------------------------------------------------------------------
# finished stock + aged stock views
# ---------------------------------------------------------------------------

def get_finished_stock(session: Session) -> list[dict]:
    """Passed rolls not yet dispatched."""
    rows = session.execute(text("""
        SELECT r.id, r.code, r.order_id, r.length_cm, r.weight_g,
               r.shelf_location, r.created_at,
               o.code AS order_code, b.name AS buyer_name
        FROM rolls r
        JOIN orders o ON o.id = r.order_id
        JOIN buyers b ON b.id = o.buyer_id
        WHERE r.status = 'passed'
          AND NOT EXISTS (
              SELECT 1 FROM dispatch_items di
              JOIN dispatches d ON d.id = di.dispatch_id
              WHERE di.roll_id = r.id AND d.status != 'cancelled'
          )
        ORDER BY r.created_at
    """)).fetchall()

    return [
        {
            "id": str(r.id), "code": r.code,
            "order_id": str(r.order_id), "order_code": r.order_code,
            "buyer_name": r.buyer_name,
            "length_cm": r.length_cm, "weight_g": r.weight_g,
            "shelf_location": r.shelf_location,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


def get_aged_stock(session: Session, days: int = 30) -> list[dict]:
    """Passed rolls sitting in warehouse longer than `days` days."""
    rows = session.execute(text("""
        SELECT r.id, r.code, r.order_id, r.length_cm, r.shelf_location, r.created_at,
               o.code AS order_code, b.name AS buyer_name,
               EXTRACT(EPOCH FROM (NOW() - r.created_at)) / 86400 AS age_days
        FROM rolls r
        JOIN orders o ON o.id = r.order_id
        JOIN buyers b ON b.id = o.buyer_id
        WHERE r.status = 'passed'
          AND r.created_at < NOW() - INTERVAL '1 day' * :days
          AND NOT EXISTS (
              SELECT 1 FROM dispatch_items di
              JOIN dispatches d ON d.id = di.dispatch_id
              WHERE di.roll_id = r.id AND d.status != 'cancelled'
          )
        ORDER BY r.created_at
    """), {"days": days}).fetchall()

    return [
        {
            "id": str(r.id), "code": r.code,
            "order_id": str(r.order_id), "order_code": r.order_code,
            "buyer_name": r.buyer_name,
            "length_cm": r.length_cm, "shelf_location": r.shelf_location,
            "age_days": int(r.age_days),
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# create dispatch
# ---------------------------------------------------------------------------

def create_dispatch(session: Session, body: dict, user: dict) -> dict:
    from app.models.quality import Dispatch

    actor_id = _actor(user)
    order_id = uuid.UUID(str(body["order_id"]))
    notes = body.get("notes")

    order_row = session.execute(
        text("SELECT id, code, buyer_id, status FROM orders WHERE id = :oid"),
        {"oid": order_id},
    ).fetchone()
    if order_row is None:
        raise AppError("NOT_FOUND", "Order not found")
    if order_row.status not in ("ready", "partly_dispatched"):
        raise AppError("INVALID_STATE",
                       f"Order must be ready or partly_dispatched, got {order_row.status}")

    code = next_code(session, "dispatch")
    now = app_time.now()

    dispatch = Dispatch(
        id=uuid.uuid4(),
        code=code,
        order_id=order_id,
        buyer_id=order_row.buyer_id,
        status="draft",
        notes=notes,
        created_by=actor_id,
        created_at=now,
        updated_at=now,
    )
    session.add(dispatch)
    session.flush()

    ev.publish(session, "dispatch.created", {
        "dispatch_id": str(dispatch.id),
        "order_id": str(order_id),
        "code": code,
    }, actor_id=actor_id)

    return get_dispatch(session, dispatch.id)


def list_dispatches(session: Session, filters: dict | None = None) -> tuple[list[dict], int]:
    filters = filters or {}
    page = int(filters.get("page", 1))
    size = int(filters.get("size", 50))
    offset = (page - 1) * size

    where_clauses = []
    params: dict = {}
    if filters.get("status"):
        where_clauses.append("d.status = :status")
        params["status"] = filters["status"]
    if filters.get("order_id"):
        where_clauses.append("d.order_id = :order_id")
        params["order_id"] = str(filters["order_id"])

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    total = session.execute(
        text(f"SELECT COUNT(*) FROM dispatches d {where_sql}"), params
    ).scalar() or 0

    rows = session.execute(text(f"""
        SELECT d.id, d.code, d.order_id, d.status, d.dispatched_at, d.created_at,
               o.code AS order_code, b.name AS buyer_name
        FROM dispatches d
        JOIN orders o ON o.id = d.order_id
        JOIN buyers b ON b.id = d.buyer_id
        {where_sql}
        ORDER BY d.created_at DESC
        LIMIT :limit OFFSET :offset
    """), {**params, "limit": size, "offset": offset}).fetchall()

    items = [
        {
            "id": str(r.id), "code": r.code,
            "order_id": str(r.order_id), "order_code": r.order_code,
            "buyer_name": r.buyer_name,
            "status": r.status,
            "dispatched_at": r.dispatched_at.isoformat() if r.dispatched_at else None,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
    return items, int(total)


def get_dispatch(session: Session, dispatch_id: uuid.UUID) -> dict:
    from app.models.quality import Dispatch
    dispatch = session.get(Dispatch, dispatch_id)
    if dispatch is None:
        raise AppError("NOT_FOUND", f"Dispatch {dispatch_id} not found")

    items = session.execute(text("""
        SELECT di.id, di.roll_id, r.code AS roll_code, di.length_cm
        FROM dispatch_items di
        JOIN rolls r ON r.id = di.roll_id
        WHERE di.dispatch_id = :did
        ORDER BY r.code
    """), {"did": dispatch_id}).fetchall()

    order_row = session.execute(
        text("SELECT code FROM orders WHERE id = :oid"), {"oid": dispatch.order_id}
    ).fetchone()
    buyer_row = session.execute(
        text("SELECT name FROM buyers WHERE id = :bid"), {"bid": dispatch.buyer_id}
    ).fetchone()

    total_cm = sum(i.length_cm for i in items)

    return {
        "id": str(dispatch.id), "code": dispatch.code,
        "order_id": str(dispatch.order_id),
        "order_code": order_row.code if order_row else None,
        "buyer_id": str(dispatch.buyer_id),
        "buyer_name": buyer_row.name if buyer_row else None,
        "status": dispatch.status,
        "notes": dispatch.notes,
        "total_length_cm": total_cm,
        "item_count": len(items),
        "dispatched_at": dispatch.dispatched_at.isoformat() if dispatch.dispatched_at else None,
        "created_at": dispatch.created_at.isoformat(),
        "items": [
            {
                "id": str(i.id), "roll_id": str(i.roll_id),
                "roll_code": i.roll_code, "length_cm": i.length_cm,
            }
            for i in items
        ],
    }


# ---------------------------------------------------------------------------
# scan roll into dispatch  [idem]
# ---------------------------------------------------------------------------

def scan_roll(session: Session, dispatch_id: uuid.UUID, body: dict, user: dict) -> dict:
    """Idempotent — scanning the same roll code twice is a no-op."""
    from app.models.quality import Dispatch, DispatchItem

    actor_id = _actor(user)
    roll_code = body["roll_code"].strip().upper()

    dispatch = session.get(Dispatch, dispatch_id)
    if dispatch is None:
        raise AppError("NOT_FOUND", f"Dispatch {dispatch_id} not found")
    if dispatch.status != "draft":
        raise AppError("INVALID_STATE", f"Dispatch status is {dispatch.status}, cannot add items")

    roll_row = session.execute(
        text("SELECT id, status, order_id, length_cm FROM rolls WHERE code = :code FOR UPDATE"),
        {"code": roll_code},
    ).fetchone()
    if roll_row is None:
        raise AppError("NOT_FOUND", f"Roll {roll_code} not found")
    if roll_row.status != "passed":
        raise AppError("INVALID_STATE", f"Roll {roll_code} status is {roll_row.status}, not passed")
    if str(roll_row.order_id) != str(dispatch.order_id):
        raise AppError("VALIDATION_ERROR", "Roll belongs to a different order")

    existing = session.execute(text("""
        SELECT id FROM dispatch_items
        WHERE dispatch_id = :did AND roll_id = :rid
    """), {"did": dispatch_id, "rid": roll_row.id}).fetchone()
    if existing:
        return get_dispatch(session, dispatch_id)

    now = app_time.now()
    item = DispatchItem(
        id=uuid.uuid4(),
        dispatch_id=dispatch_id,
        roll_id=roll_row.id,
        length_cm=roll_row.length_cm,
        created_at=now,
    )
    session.add(item)
    session.flush()

    return get_dispatch(session, dispatch_id)


def remove_item(session: Session, dispatch_id: uuid.UUID, item_id: uuid.UUID, user: dict) -> dict:
    from app.models.quality import DispatchItem, Dispatch

    dispatch = session.get(Dispatch, dispatch_id)
    if dispatch is None:
        raise AppError("NOT_FOUND", f"Dispatch {dispatch_id} not found")
    if dispatch.status != "draft":
        raise AppError("INVALID_STATE", "Cannot remove items from non-draft dispatch")

    item = session.get(DispatchItem, item_id)
    if item is None or str(item.dispatch_id) != str(dispatch_id):
        raise AppError("NOT_FOUND", "Dispatch item not found")

    session.delete(item)
    session.flush()

    return get_dispatch(session, dispatch_id)


# ---------------------------------------------------------------------------
# confirm dispatch → create invoice
# ---------------------------------------------------------------------------

def confirm_dispatch(session: Session, dispatch_id: uuid.UUID, body: dict, user: dict) -> dict:
    from app.models.quality import Dispatch
    from app.models.finance import Invoice, InvoiceLine

    actor_id = _actor(user)
    dispatch = session.get(Dispatch, dispatch_id)
    if dispatch is None:
        raise AppError("NOT_FOUND", f"Dispatch {dispatch_id} not found")
    if dispatch.status != "draft":
        raise AppError("INVALID_STATE", f"Dispatch is {dispatch.status}, not draft")

    items = session.execute(text("""
        SELECT di.id, di.roll_id, di.length_cm, r.code AS roll_code
        FROM dispatch_items di
        JOIN rolls r ON r.id = di.roll_id
        WHERE di.dispatch_id = :did
    """), {"did": dispatch_id}).fetchall()
    if not items:
        raise AppError("VALIDATION_ERROR", "Dispatch has no items")

    now = app_time.now()
    dispatch.status = "dispatched"
    dispatch.dispatched_at = now
    dispatch.updated_at = now

    for item in items:
        session.execute(text("""
            UPDATE rolls SET status = 'dispatched', updated_at = :now WHERE id = :rid
        """), {"rid": item.roll_id, "now": now})

    order_row = session.execute(text("""
        SELECT o.id, o.code, o.buyer_id, o.price_paise_per_m, o.status, o.quantity_cm
        FROM orders o WHERE o.id = :oid FOR UPDATE
    """), {"oid": dispatch.order_id}).fetchone()

    price_paise_per_m = int(order_row.price_paise_per_m or 0)
    gst_rate_bp = int(body.get("gst_rate_bp", 1200))
    due_days = int(body.get("due_days", 30))

    total_cm = sum(i.length_cm for i in items)
    # price_paise_per_m * total_cm / 100 (metres) — keep as integer paise
    subtotal_paise = price_paise_per_m * total_cm // 100
    gst_paise = subtotal_paise * gst_rate_bp // 10000
    total_paise = subtotal_paise + gst_paise

    invoice_number = next_code(session, "invoice")
    due_date_val = session.execute(
        text("SELECT CURRENT_DATE + :days"), {"days": due_days}
    ).scalar()

    invoice = Invoice(
        id=uuid.uuid4(),
        number=invoice_number,
        order_id=dispatch.order_id,
        dispatch_id=dispatch_id,
        buyer_id=dispatch.buyer_id,
        subtotal_paise=subtotal_paise,
        gst_bp=gst_rate_bp,
        gst_paise=gst_paise,
        total_paise=total_paise,
        amount_paid_paise=0,
        status="issued",
        issue_date=now.date(),
        due_date=due_date_val,
        created_at=now,
        updated_at=now,
    )
    session.add(invoice)
    session.flush()

    for item in items:
        line_amount_paise = price_paise_per_m * item.length_cm // 100
        il = InvoiceLine(
            id=uuid.uuid4(),
            invoice_id=invoice.id,
            description=f"Roll {item.roll_code} — {item.length_cm} cm",
            quantity_cm=item.length_cm,
            rate_paise_per_m=price_paise_per_m,
            amount_paise=line_amount_paise,
            created_at=now,
        )
        session.add(il)

    remaining = session.execute(text("""
        SELECT COUNT(*) FROM rolls
        WHERE order_id = :oid AND status = 'passed'
    """), {"oid": dispatch.order_id}).scalar() or 0

    new_order_status = "dispatched" if int(remaining) == 0 else "partly_dispatched"
    session.execute(text("""
        UPDATE orders SET status = :status, updated_at = :now WHERE id = :oid
    """), {"status": new_order_status, "oid": dispatch.order_id, "now": now})

    audit(session, actor_id, "confirm_dispatch", "dispatch", str(dispatch_id),
          before={"status": "draft"}, after={"status": "dispatched", "invoice": invoice_number})

    ev.publish(session, "dispatch.confirmed", {
        "dispatch_id": str(dispatch_id),
        "order_id": str(dispatch.order_id),
        "invoice_id": str(invoice.id),
        "invoice_number": invoice_number,
        "total_paise": total_paise,
    }, actor_id=actor_id)

    result = get_dispatch(session, dispatch_id)
    result["invoice"] = {
        "id": str(invoice.id),
        "number": invoice_number,
        "total_paise": total_paise,
    }
    return result


# ---------------------------------------------------------------------------
# update dispatch status
# ---------------------------------------------------------------------------

def update_dispatch_status(
    session: Session, dispatch_id: uuid.UUID, body: dict, user: dict
) -> dict:
    from app.models.quality import Dispatch

    actor_id = _actor(user)
    dispatch = session.get(Dispatch, dispatch_id)
    if dispatch is None:
        raise AppError("NOT_FOUND", f"Dispatch {dispatch_id} not found")

    allowed_transitions: dict[str, list[str]] = {
        "dispatched": ["in_transit", "delivered", "cancelled"],
        "in_transit": ["delivered", "returned"],
    }
    new_status = body["status"]
    allowed = allowed_transitions.get(dispatch.status, [])
    if new_status not in allowed:
        raise AppError("INVALID_STATE",
                       f"Cannot transition {dispatch.status} -> {new_status}")

    old_status = dispatch.status
    now = app_time.now()
    dispatch.status = new_status
    dispatch.updated_at = now

    audit(session, actor_id, "update_dispatch_status", "dispatch", str(dispatch_id),
          before={"status": old_status}, after={"status": new_status})

    ev.publish(session, "dispatch.status_changed", {
        "dispatch_id": str(dispatch_id),
        "from": old_status, "to": new_status,
    }, actor_id=actor_id)

    return get_dispatch(session, dispatch_id)
