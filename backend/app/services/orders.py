"""A-M3: Order management service."""
from __future__ import annotations

import uuid
import secrets
from typing import Any

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
# feasibility
# ---------------------------------------------------------------------------

def feasibility(session: Session, fabric_type_id: uuid.UUID, quantity_cm: int) -> dict:
    from app.models.sales import FabricType

    ft = session.get(FabricType, fabric_type_id)
    if ft is None:
        raise AppError("NOT_FOUND", f"FabricType {fabric_type_id} not found")

    yarn_needed_g = ft.yarn_g_per_100m * quantity_cm // 100

    # Get available stock for that yarn_type
    from app.services.inventory import get_stock_view
    stock = get_stock_view(session)
    yt_stock = next((s for s in stock if s["yarn_type_id"] == str(ft.yarn_type_id)), None)
    available_g = yt_stock["available_g"] if yt_stock else 0

    shortage_g = max(0, yarn_needed_g - available_g)

    # Suggested batches
    batches = session.execute(text("""
        SELECT yb.id, yb.code, yb.received_at, yb.rate_paise_per_kg,
               COALESCE(SUM(sm.qty_g), 0) AS on_hand_g
        FROM yarn_batches yb
        LEFT JOIN stock_movements sm ON sm.batch_id = yb.id
        WHERE yb.yarn_type_id = :ytid AND yb.status = 'active'
        GROUP BY yb.id
        HAVING COALESCE(SUM(sm.qty_g), 0) > 0
        ORDER BY yb.received_at
    """), {"ytid": ft.yarn_type_id}).fetchall()

    return {
        "fabric_type_id": str(fabric_type_id),
        "yarn_type_id": str(ft.yarn_type_id),
        "yarn_needed_g": yarn_needed_g,
        "available_g": available_g,
        "shortage_g": shortage_g,
        "feasible": shortage_g == 0,
        "suggested_batches": [
            {
                "id": str(b.id), "code": b.code,
                "on_hand_g": int(b.on_hand_g),
                "rate_paise_per_kg": b.rate_paise_per_kg,
                "received_at": b.received_at.isoformat(),
            }
            for b in batches
        ],
    }


# ---------------------------------------------------------------------------
# create order
# ---------------------------------------------------------------------------

def create_order(session: Session, body: dict, user: dict) -> Any:
    from app.models.sales import Order, Buyer, FabricType
    from app.core.security import generate_tracking_token

    actor_id = _actor(user)

    buyer_id = uuid.UUID(str(body["buyer_id"]))
    fabric_type_id = uuid.UUID(str(body["fabric_type_id"]))

    buyer = session.get(Buyer, buyer_id)
    if buyer is None:
        raise AppError("NOT_FOUND", f"Buyer {buyer_id} not found")

    ft = session.get(FabricType, fabric_type_id)
    if ft is None:
        raise AppError("NOT_FOUND", f"FabricType {fabric_type_id} not found")

    quantity_cm = int(body["quantity_cm"])
    if quantity_cm <= 0:
        raise AppError("VALIDATION_ERROR", "quantity_cm must be positive")

    now = app_time.now()
    code = next_code(session, "order")
    tracking_token = secrets.token_urlsafe(24)

    order = Order(
        id=uuid.uuid4(),
        code=code,
        buyer_id=buyer_id,
        fabric_type_id=fabric_type_id,
        quantity_cm=quantity_cm,
        price_paise_per_m=int(body.get("price_paise_per_m") or ft.default_price_paise_per_m),
        due_date=body["due_date"],
        promised_date=body.get("promised_date"),
        priority=body.get("priority", "normal"),
        status="draft",
        late_penalty_paise_per_day=int(
            body.get("late_penalty_paise_per_day")
            or buyer.default_late_penalty_paise_per_day
            or 0
        ),
        tracking_token=tracking_token,
        notes=body.get("notes"),
        created_by=actor_id,
        created_at=now,
    )
    session.add(order)
    session.flush()

    ev.publish(session, "order.created", {
        "order_id": str(order.id),
        "code": code,
        "buyer_id": str(buyer_id),
        "fabric_type_id": str(fabric_type_id),
        "quantity_cm": quantity_cm,
    }, actor_id=actor_id)

    return order


# ---------------------------------------------------------------------------
# list orders
# ---------------------------------------------------------------------------

def list_orders(session: Session, filters: dict | None = None) -> tuple[list[dict], int]:
    from app.services.interfaces import get_orders_health

    filters = filters or {}
    page = int(filters.get("page", 1))
    size = int(filters.get("size", 50))
    offset = (page - 1) * size

    where_clauses = []
    params: dict = {}

    if filters.get("status"):
        where_clauses.append("o.status = :status")
        params["status"] = filters["status"]
    if filters.get("buyer_id"):
        where_clauses.append("o.buyer_id = :buyer_id")
        params["buyer_id"] = str(filters["buyer_id"])
    if filters.get("due_before"):
        where_clauses.append("o.due_date <= :due_before")
        params["due_before"] = filters["due_before"]
    if filters.get("q"):
        q = "%" + filters["q"] + "%"
        where_clauses.append("(o.code ILIKE :q OR b.name ILIKE :q)")
        params["q"] = q

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    total = session.execute(text(f"""
        SELECT COUNT(*) FROM orders o
        LEFT JOIN buyers b ON b.id = o.buyer_id
        {where_sql}
    """), params).scalar() or 0

    rows = session.execute(text(f"""
        SELECT o.id, o.code, o.buyer_id, b.name AS buyer_name,
               o.fabric_type_id, o.quantity_cm, o.price_paise_per_m,
               o.due_date, o.promised_date, o.status, o.priority,
               o.created_at, o.confirmed_at
        FROM orders o
        LEFT JOIN buyers b ON b.id = o.buyer_id
        {where_sql}
        ORDER BY o.created_at DESC
        LIMIT :limit OFFSET :offset
    """), {**params, "limit": size, "offset": offset}).fetchall()

    order_ids = [r.id for r in rows]
    health_map = get_orders_health(session, order_ids) if order_ids else {}

    items = []
    for r in rows:
        h = health_map.get(r.id)
        items.append({
            "id": str(r.id),
            "code": r.code,
            "buyer_id": str(r.buyer_id),
            "buyer_name": r.buyer_name,
            "fabric_type_id": str(r.fabric_type_id),
            "quantity_cm": r.quantity_cm,
            "price_paise_per_m": r.price_paise_per_m,
            "due_date": r.due_date.isoformat(),
            "promised_date": r.promised_date.isoformat() if r.promised_date else None,
            "status": r.status,
            "priority": r.priority,
            "created_at": r.created_at.isoformat(),
            "confirmed_at": r.confirmed_at.isoformat() if r.confirmed_at else None,
            "health": h,
        })
    return items, int(total)


# ---------------------------------------------------------------------------
# get order
# ---------------------------------------------------------------------------

def get_order(session: Session, order_id: uuid.UUID, user: dict | None = None) -> dict:
    from app.models.sales import Order
    from app.core.rbac import has_permission

    order = session.get(Order, order_id)
    if order is None:
        raise AppError("NOT_FOUND", f"Order {order_id} not found")

    jobs = session.execute(text("""
        SELECT id, code, stage, seq, unit, planned_qty, produced_qty,
               waste_qty, machine_id, queue_position, status, started_at,
               finished_at, current_operator_id, created_at
        FROM jobs WHERE order_id = :oid ORDER BY seq
    """), {"oid": order_id}).fetchall()

    rolls_summary = session.execute(text("""
        SELECT status, COUNT(*) as count, SUM(length_cm) as total_cm
        FROM rolls WHERE order_id = :oid GROUP BY status
    """), {"oid": order_id}).fetchall()

    dispatches = session.execute(text("""
        SELECT id, code, status, dispatched_at, created_at FROM dispatches
        WHERE order_id = :oid ORDER BY created_at DESC
    """), {"oid": order_id}).fetchall()

    # Invoices - role-filtered
    invoices = []
    if user is None or has_permission(user.get("role", ""), "finance.view"):
        inv_rows = session.execute(text("""
            SELECT id, number, total_paise, amount_paid_paise, status, issue_date
            FROM invoices WHERE order_id = :oid ORDER BY issue_date DESC
        """), {"oid": order_id}).fetchall()
        invoices = [
            {
                "id": str(i.id), "number": i.number,
                "total_paise": i.total_paise,
                "amount_paid_paise": i.amount_paid_paise,
                "status": i.status,
                "issue_date": i.issue_date.isoformat(),
            }
            for i in inv_rows
        ]

    return {
        "id": str(order.id),
        "code": order.code,
        "buyer_id": str(order.buyer_id),
        "fabric_type_id": str(order.fabric_type_id),
        "quantity_cm": order.quantity_cm,
        "price_paise_per_m": order.price_paise_per_m,
        "due_date": order.due_date.isoformat(),
        "promised_date": order.promised_date.isoformat() if order.promised_date else None,
        "priority": order.priority,
        "status": order.status,
        "late_penalty_paise_per_day": order.late_penalty_paise_per_day,
        "tracking_token": order.tracking_token,
        "notes": order.notes,
        "confirmed_at": order.confirmed_at.isoformat() if order.confirmed_at else None,
        "created_at": order.created_at.isoformat(),
        "jobs": [
            {
                "id": str(j.id), "code": j.code, "stage": j.stage,
                "seq": j.seq, "unit": j.unit,
                "planned_qty": j.planned_qty, "produced_qty": j.produced_qty,
                "waste_qty": j.waste_qty,
                "machine_id": str(j.machine_id) if j.machine_id else None,
                "queue_position": j.queue_position,
                "status": j.status,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "finished_at": j.finished_at.isoformat() if j.finished_at else None,
            }
            for j in jobs
        ],
        "rolls_summary": [
            {"status": r.status, "count": r.count, "total_cm": int(r.total_cm or 0)}
            for r in rolls_summary
        ],
        "dispatches": [
            {
                "id": str(d.id), "code": d.code, "status": d.status,
                "dispatched_at": d.dispatched_at.isoformat() if d.dispatched_at else None,
                "created_at": d.created_at.isoformat(),
            }
            for d in dispatches
        ],
        "invoices": invoices,
    }


# ---------------------------------------------------------------------------
# update order
# ---------------------------------------------------------------------------

def update_order(session: Session, order_id: uuid.UUID, body: dict, user: dict) -> dict:
    from app.models.sales import Order
    actor_id = _actor(user)

    order = session.get(Order, order_id)
    if order is None:
        raise AppError("NOT_FOUND", f"Order {order_id} not found")

    if order.status not in ("draft", "confirmed"):
        raise AppError("INVALID_STATE", f"Cannot update order in status {order.status}")

    allowed_fields = ["notes", "due_date", "promised_date", "priority",
                      "price_paise_per_m", "late_penalty_paise_per_day", "quantity_cm"]
    for field in allowed_fields:
        if field in body:
            setattr(order, field, body[field])
    order.updated_at = app_time.now()

    ev.publish(session, "order.updated", {"order_id": str(order_id)}, actor_id=actor_id)
    return get_order(session, order_id, user)


# ---------------------------------------------------------------------------
# confirm order
# ---------------------------------------------------------------------------

def confirm_order(session: Session, order_id: uuid.UUID, body: dict, user: dict) -> dict:
    from app.models.sales import Order, OrderStatusHistory, FabricType, RouteTemplate, RouteStep
    from app.models.production import Job
    from app.services.inventory import reserve_yarn, get_stock_view

    actor_id = _actor(user)

    order = session.get(Order, order_id)
    if order is None:
        raise AppError("NOT_FOUND", f"Order {order_id} not found")
    if order.status != "draft":
        raise AppError("INVALID_STATE", f"Order must be draft, got {order.status}")

    ft = session.get(FabricType, order.fabric_type_id)
    yarn_needed_g = ft.yarn_g_per_100m * order.quantity_cm // 100

    # Check available stock
    stock = get_stock_view(session)
    yt_stock = next((s for s in stock if s["yarn_type_id"] == str(ft.yarn_type_id)), None)
    available_g = yt_stock["available_g"] if yt_stock else 0

    if available_g < yarn_needed_g:
        raise AppError("INSUFFICIENT_STOCK",
                       f"Need {yarn_needed_g}g, available {available_g}g")

    # Reserve yarn
    reserve_yarn(session, ft.yarn_type_id, order_id, yarn_needed_g)

    # Create jobs per route steps
    now = app_time.now()
    order_num = int(order.code.split("-")[-1])

    if ft.route_template_id:
        steps = session.execute(text("""
            SELECT seq, stage, buffer_minutes FROM route_steps
            WHERE template_id = :tid ORDER BY seq
        """), {"tid": ft.route_template_id}).fetchall()
    else:
        steps = []

    for step in steps:
        job_code = next_code(session, "job", order_no=order_num)
        job = Job(
            id=uuid.uuid4(),
            code=job_code,
            order_id=order_id,
            stage=step.stage,
            seq=step.seq,
            unit="cm",
            planned_qty=order.quantity_cm,
            produced_qty=0,
            waste_qty=0,
            status="planned",
            created_at=now,
        )
        session.add(job)

    # Update order
    old_status = order.status
    order.status = "confirmed"
    if body.get("promised_date"):
        order.promised_date = body["promised_date"]
    order.confirmed_at = now
    order.updated_at = now

    # History row
    history = OrderStatusHistory(
        id=uuid.uuid4(),
        order_id=order_id,
        from_status=old_status,
        to_status="confirmed",
        actor_id=actor_id,
        note=body.get("note"),
        created_at=now,
    )
    session.add(history)

    audit(session, actor_id, "confirm", "order", str(order_id),
          before={"status": old_status}, after={"status": "confirmed"})

    ev.publish(session, "order.confirmed", {
        "order_id": str(order_id),
        "code": order.code,
        "yarn_reserved_g": yarn_needed_g,
    }, actor_id=actor_id)

    return get_order(session, order_id, user)


# ---------------------------------------------------------------------------
# cancel order
# ---------------------------------------------------------------------------

def cancel_order(session: Session, order_id: uuid.UUID, body: dict, user: dict) -> dict:
    from app.models.sales import Order, OrderStatusHistory
    from app.services.inventory import release_reservations

    actor_id = _actor(user)

    order = session.get(Order, order_id)
    if order is None:
        raise AppError("NOT_FOUND", f"Order {order_id} not found")

    if order.status in ("closed", "cancelled"):
        raise AppError("INVALID_STATE", f"Order is already {order.status}")

    # Release reservations
    release_reservations(session, order_id)

    # Cancel jobs
    session.execute(text("""
        UPDATE jobs SET status = 'cancelled', updated_at = :now
        WHERE order_id = :oid AND status NOT IN ('done', 'cancelled')
    """), {"oid": order_id, "now": app_time.now()})

    old_status = order.status
    now = app_time.now()
    order.status = "cancelled"
    order.updated_at = now

    history = OrderStatusHistory(
        id=uuid.uuid4(),
        order_id=order_id,
        from_status=old_status,
        to_status="cancelled",
        actor_id=actor_id,
        note=body.get("reason"),
        created_at=now,
    )
    session.add(history)

    audit(session, actor_id, "cancel", "order", str(order_id),
          before={"status": old_status}, after={"status": "cancelled"})

    ev.publish(session, "order.cancelled", {
        "order_id": str(order_id),
        "reason": body.get("reason"),
    }, actor_id=actor_id)

    return get_order(session, order_id, user)


# ---------------------------------------------------------------------------
# timeline
# ---------------------------------------------------------------------------

def get_timeline(session: Session, order_id: uuid.UUID) -> dict:
    from app.models.sales import Order
    order = session.get(Order, order_id)
    if order is None:
        raise AppError("NOT_FOUND", f"Order {order_id} not found")

    history = session.execute(text("""
        SELECT from_status, to_status, actor_id, note, created_at
        FROM order_status_history WHERE order_id = :oid ORDER BY created_at
    """), {"oid": order_id}).fetchall()

    job_events = session.execute(text("""
        SELECT j.stage, j.status, j.started_at, j.finished_at, j.code
        FROM jobs j WHERE j.order_id = :oid ORDER BY j.seq
    """), {"oid": order_id}).fetchall()

    return {
        "order_id": str(order_id),
        "status_history": [
            {
                "from_status": h.from_status,
                "to_status": h.to_status,
                "actor_id": str(h.actor_id) if h.actor_id else None,
                "note": h.note,
                "created_at": h.created_at.isoformat(),
            }
            for h in history
        ],
        "jobs": [
            {
                "code": j.code, "stage": j.stage, "status": j.status,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "finished_at": j.finished_at.isoformat() if j.finished_at else None,
            }
            for j in job_events
        ],
    }


# ---------------------------------------------------------------------------
# lookup
# ---------------------------------------------------------------------------

def lookup_orders(session: Session, q: str) -> list[dict]:
    q_like = "%" + q + "%"
    rows = session.execute(text("""
        SELECT o.id, o.code, b.name AS buyer_name, o.status, o.due_date
        FROM orders o JOIN buyers b ON b.id = o.buyer_id
        WHERE o.code ILIKE :q OR b.name ILIKE :q OR b.phone ILIKE :q
        ORDER BY o.created_at DESC
        LIMIT 10
    """), {"q": q_like}).fetchall()

    return [
        {
            "id": str(r.id), "code": r.code,
            "buyer_name": r.buyer_name, "status": r.status,
            "due_date": r.due_date.isoformat(),
        }
        for r in rows
    ]
