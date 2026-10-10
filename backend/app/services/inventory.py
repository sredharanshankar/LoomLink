"""A-M2: Raw material inventory service."""
from __future__ import annotations

import uuid
import datetime as dt
from typing import Any

from sqlalchemy import select, func, text
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
# helpers
# ---------------------------------------------------------------------------

def on_hand_g(session: Session, batch_id: uuid.UUID) -> int:
    """Sum of all stock_movements.qty_g for this batch."""
    result = session.execute(
        text("SELECT COALESCE(SUM(qty_g), 0) FROM stock_movements WHERE batch_id = :bid"),
        {"bid": batch_id},
    ).scalar()
    return int(result or 0)


def _check_idempotency(session: Session, idempotency_key: str | None, actor_id: uuid.UUID | None) -> bool:
    """Return True if this key was already processed (caller should skip and return existing)."""
    if not idempotency_key:
        return False
    row = session.execute(
        text(
            "SELECT id FROM stock_movements WHERE idempotency_key = :k AND actor_id = :aid LIMIT 1"
        ),
        {"k": idempotency_key, "aid": str(actor_id) if actor_id else None},
    ).fetchone()
    return row is not None


# ---------------------------------------------------------------------------
# receipt
# ---------------------------------------------------------------------------

def receipt(session: Session, body: dict, user: dict) -> Any:
    """Create YarnBatch + StockMovement(receipt). Returns batch."""
    from app.models.materials import YarnBatch, StockMovement, YarnType, Supplier

    actor_id = _actor(user)
    idempotency_key = body.get("idempotency_key")

    received_g = int(body.get("received_g", 0))
    if received_g <= 0:
        raise AppError("VALIDATION_ERROR", "received_g must be positive")

    yarn_type_id = uuid.UUID(str(body["yarn_type_id"]))
    supplier_id = uuid.UUID(str(body["supplier_id"]))

    yt = session.get(YarnType, yarn_type_id)
    if yt is None:
        raise AppError("NOT_FOUND", f"YarnType {yarn_type_id} not found")
    sup = session.get(Supplier, supplier_id)
    if sup is None:
        raise AppError("NOT_FOUND", f"Supplier {supplier_id} not found")

    now = app_time.now()
    code = next_code(session, "yarn_batch")
    batch = YarnBatch(
        id=uuid.uuid4(),
        code=code,
        yarn_type_id=yarn_type_id,
        supplier_id=supplier_id,
        po_id=uuid.UUID(str(body["po_id"])) if body.get("po_id") else None,
        intended_order_id=uuid.UUID(str(body["intended_order_id"])) if body.get("intended_order_id") else None,
        received_g=received_g,
        rate_paise_per_kg=int(body.get("rate_paise_per_kg") or yt.standard_rate_paise_per_kg),
        location=body.get("location"),
        received_at=now,
        received_by=actor_id,
        supplier_invoice_ref=body.get("supplier_invoice_ref"),
        status="active",
        notes=body.get("notes"),
        created_at=now,
    )
    session.add(batch)
    session.flush()

    movement = StockMovement(
        id=uuid.uuid4(),
        batch_id=batch.id,
        kind="receipt",
        qty_g=received_g,
        order_id=uuid.UUID(str(body["intended_order_id"])) if body.get("intended_order_id") else None,
        reason=body.get("notes"),
        actor_id=actor_id,
        idempotency_key=idempotency_key,
        created_at=now,
    )
    session.add(movement)

    audit(session, actor_id, "receipt", "yarn_batch", str(batch.id),
          after={"code": code, "received_g": received_g})

    ev.publish(session, "stock.received", {
        "batch_id": str(batch.id),
        "yarn_type_id": str(yarn_type_id),
        "received_g": received_g,
    }, actor_id=actor_id)

    return batch


# ---------------------------------------------------------------------------
# issue
# ---------------------------------------------------------------------------

def issue(session: Session, body: dict, user: dict) -> Any:
    """Create StockMovement(issue). SELECT batch FOR UPDATE."""
    from app.models.materials import StockMovement, YarnBatch
    from app.models.production import Job

    actor_id = _actor(user)
    idempotency_key = body.get("idempotency_key")

    if idempotency_key and _check_idempotency(session, idempotency_key, actor_id):
        # Return existing movement
        row = session.execute(
            text("SELECT id FROM stock_movements WHERE idempotency_key = :k LIMIT 1"),
            {"k": idempotency_key},
        ).fetchone()
        return session.get(StockMovement, row[0])

    batch_id = uuid.UUID(str(body["batch_id"]))
    qty_g = int(body.get("qty_g", 0))
    if qty_g <= 0:
        raise AppError("VALIDATION_ERROR", "qty_g must be positive")

    job_id = uuid.UUID(str(body["job_id"])) if body.get("job_id") else None
    if job_id:
        job = session.get(Job, job_id)
        if job is None:
            raise AppError("NOT_FOUND", f"Job {job_id} not found")

    # Lock batch row
    batch = session.execute(
        text("SELECT id FROM yarn_batches WHERE id = :bid FOR UPDATE"),
        {"bid": batch_id},
    ).fetchone()
    if batch is None:
        raise AppError("NOT_FOUND", f"YarnBatch {batch_id} not found")

    current_on_hand = on_hand_g(session, batch_id)
    if current_on_hand < qty_g:
        raise AppError("INSUFFICIENT_STOCK",
                       f"On-hand {current_on_hand}g, requested {qty_g}g")

    now = app_time.now()
    movement = StockMovement(
        id=uuid.uuid4(),
        batch_id=batch_id,
        kind="issue",
        qty_g=-qty_g,
        order_id=uuid.UUID(str(body["order_id"])) if body.get("order_id") else None,
        job_id=job_id,
        reason=body.get("reason"),
        actor_id=actor_id,
        idempotency_key=idempotency_key,
        created_at=now,
    )
    session.add(movement)

    ev.publish(session, "stock.issued", {
        "batch_id": str(batch_id),
        "qty_g": qty_g,
        "job_id": str(job_id) if job_id else None,
    }, actor_id=actor_id)

    return movement


# ---------------------------------------------------------------------------
# return_yarn
# ---------------------------------------------------------------------------

def return_yarn(session: Session, body: dict, user: dict) -> Any:
    from app.models.materials import StockMovement, YarnBatch
    from app.models.production import Job

    actor_id = _actor(user)
    idempotency_key = body.get("idempotency_key")

    if idempotency_key and _check_idempotency(session, idempotency_key, actor_id):
        row = session.execute(
            text("SELECT id FROM stock_movements WHERE idempotency_key = :k LIMIT 1"),
            {"k": idempotency_key},
        ).fetchone()
        return session.get(StockMovement, row[0])

    batch_id = uuid.UUID(str(body["batch_id"]))
    qty_g = int(body.get("qty_g", 0))
    if qty_g <= 0:
        raise AppError("VALIDATION_ERROR", "qty_g must be positive")

    batch = session.get(YarnBatch, batch_id)
    if batch is None:
        raise AppError("NOT_FOUND", f"YarnBatch {batch_id} not found")

    job_id = uuid.UUID(str(body["job_id"])) if body.get("job_id") else None
    if job_id:
        job = session.get(Job, job_id)
        if job is None:
            raise AppError("NOT_FOUND", f"Job {job_id} not found")

    now = app_time.now()
    movement = StockMovement(
        id=uuid.uuid4(),
        batch_id=batch_id,
        kind="return",
        qty_g=qty_g,
        job_id=job_id,
        reason=body.get("reason"),
        actor_id=actor_id,
        idempotency_key=idempotency_key,
        created_at=now,
    )
    session.add(movement)

    ev.publish(session, "stock.returned", {
        "batch_id": str(batch_id),
        "qty_g": qty_g,
    }, actor_id=actor_id)

    return movement


# ---------------------------------------------------------------------------
# adjustment
# ---------------------------------------------------------------------------

def adjustment(session: Session, body: dict, user: dict) -> Any:
    from app.models.materials import StockMovement, YarnBatch

    actor_id = _actor(user)
    batch_id = uuid.UUID(str(body["batch_id"]))
    qty_g = int(body.get("qty_g", 0))  # signed

    batch = session.get(YarnBatch, batch_id)
    if batch is None:
        raise AppError("NOT_FOUND", f"YarnBatch {batch_id} not found")

    current_on_hand = on_hand_g(session, batch_id)
    if current_on_hand + qty_g < 0:
        raise AppError("INSUFFICIENT_STOCK",
                       f"Adjustment would result in negative stock ({current_on_hand + qty_g}g)")

    now = app_time.now()
    movement = StockMovement(
        id=uuid.uuid4(),
        batch_id=batch_id,
        kind="adjustment",
        qty_g=qty_g,
        reason=body.get("reason"),
        actor_id=actor_id,
        created_at=now,
    )
    session.add(movement)

    audit(session, actor_id, "adjustment", "yarn_batch", str(batch_id),
          before={"on_hand_g": current_on_hand},
          after={"on_hand_g": current_on_hand + qty_g, "delta_g": qty_g})

    ev.publish(session, "stock.adjusted", {
        "batch_id": str(batch_id),
        "delta_g": qty_g,
        "new_on_hand_g": current_on_hand + qty_g,
    }, actor_id=actor_id)

    return movement


# ---------------------------------------------------------------------------
# stock view
# ---------------------------------------------------------------------------

def get_stock_view(session: Session) -> list[dict]:
    """Per yarn_type: on_hand_g, reserved_g, available_g, reorder_level_g, is_low, batches_count."""
    rows = session.execute(text("""
        SELECT
            yt.id AS yarn_type_id,
            yt.code,
            yt.material,
            yt.count_label,
            yt.colour,
            yt.colour_hex,
            yt.reorder_level_g,
            COALESCE(sm_agg.on_hand_g, 0) AS on_hand_g,
            COALESCE(sr_agg.reserved_g, 0) AS reserved_g,
            COALESCE(batch_agg.batches_count, 0) AS batches_count
        FROM yarn_types yt
        LEFT JOIN (
            SELECT yb.yarn_type_id, SUM(sm.qty_g) AS on_hand_g
            FROM yarn_batches yb
            JOIN stock_movements sm ON sm.batch_id = yb.id
            WHERE yb.status != 'quarantined'
            GROUP BY yb.yarn_type_id
        ) sm_agg ON sm_agg.yarn_type_id = yt.id
        LEFT JOIN (
            SELECT yarn_type_id, SUM(qty_g) AS reserved_g
            FROM stock_reservations
            WHERE status = 'active'
            GROUP BY yarn_type_id
        ) sr_agg ON sr_agg.yarn_type_id = yt.id
        LEFT JOIN (
            SELECT yarn_type_id, COUNT(*) AS batches_count
            FROM yarn_batches
            WHERE status = 'active'
            GROUP BY yarn_type_id
        ) batch_agg ON batch_agg.yarn_type_id = yt.id
        WHERE yt.is_active = true
        ORDER BY yt.code
    """)).fetchall()

    result = []
    for r in rows:
        on_hand = int(r.on_hand_g or 0)
        reserved = int(r.reserved_g or 0)
        available = max(0, on_hand - reserved)
        result.append({
            "yarn_type_id": str(r.yarn_type_id),
            "code": r.code,
            "material": r.material,
            "count_label": r.count_label,
            "colour": r.colour,
            "colour_hex": r.colour_hex,
            "reorder_level_g": r.reorder_level_g,
            "on_hand_g": on_hand,
            "reserved_g": reserved,
            "available_g": available,
            "is_low": available < r.reorder_level_g,
            "batches_count": int(r.batches_count or 0),
        })
    return result


# ---------------------------------------------------------------------------
# batches
# ---------------------------------------------------------------------------

def get_batches(session: Session, filters: dict | None = None) -> tuple[list[dict], int]:
    filters = filters or {}
    page = int(filters.get("page", 1))
    size = int(filters.get("size", 50))
    offset = (page - 1) * size

    where_clauses = []
    params: dict = {}

    if filters.get("yarn_type_id"):
        where_clauses.append("yb.yarn_type_id = :yarn_type_id")
        params["yarn_type_id"] = str(filters["yarn_type_id"])
    if filters.get("status"):
        where_clauses.append("yb.status = :status")
        params["status"] = filters["status"]
    if filters.get("supplier_id"):
        where_clauses.append("yb.supplier_id = :supplier_id")
        params["supplier_id"] = str(filters["supplier_id"])

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    count_row = session.execute(
        text(f"SELECT COUNT(*) FROM yarn_batches yb {where_sql}"), params
    ).scalar()
    total = int(count_row or 0)

    rows = session.execute(text(f"""
        SELECT yb.id, yb.code, yb.yarn_type_id, yb.supplier_id, yb.received_g,
               yb.rate_paise_per_kg, yb.location, yb.received_at, yb.status, yb.notes,
               yb.supplier_invoice_ref,
               COALESCE(SUM(sm.qty_g), 0) AS on_hand_g,
               COUNT(sm.id) AS movements_count
        FROM yarn_batches yb
        LEFT JOIN stock_movements sm ON sm.batch_id = yb.id
        {where_sql}
        GROUP BY yb.id
        ORDER BY yb.received_at DESC
        LIMIT :limit OFFSET :offset
    """), {**params, "limit": size, "offset": offset}).fetchall()

    items = []
    for r in rows:
        items.append({
            "id": str(r.id),
            "code": r.code,
            "yarn_type_id": str(r.yarn_type_id),
            "supplier_id": str(r.supplier_id),
            "received_g": r.received_g,
            "on_hand_g": int(r.on_hand_g or 0),
            "rate_paise_per_kg": r.rate_paise_per_kg,
            "location": r.location,
            "received_at": r.received_at.isoformat(),
            "status": r.status,
            "notes": r.notes,
            "supplier_invoice_ref": r.supplier_invoice_ref,
            "movements_count": int(r.movements_count or 0),
        })
    return items, total


def get_batch(session: Session, batch_id: uuid.UUID) -> dict:
    from app.models.materials import YarnBatch
    batch = session.get(YarnBatch, batch_id)
    if batch is None:
        raise AppError("NOT_FOUND", f"YarnBatch {batch_id} not found")

    movements = session.execute(text("""
        SELECT id, kind, qty_g, order_id, job_id, reason, actor_id, created_at
        FROM stock_movements WHERE batch_id = :bid ORDER BY created_at
    """), {"bid": batch_id}).fetchall()

    consumptions = session.execute(text("""
        SELECT jmc.id, jmc.job_id, jmc.qty_g, j.code AS job_code
        FROM job_material_consumption jmc
        JOIN jobs j ON j.id = jmc.job_id
        WHERE jmc.batch_id = :bid
    """), {"bid": batch_id}).fetchall()

    return {
        "id": str(batch.id),
        "code": batch.code,
        "yarn_type_id": str(batch.yarn_type_id),
        "supplier_id": str(batch.supplier_id),
        "received_g": batch.received_g,
        "on_hand_g": on_hand_g(session, batch_id),
        "rate_paise_per_kg": batch.rate_paise_per_kg,
        "location": batch.location,
        "received_at": batch.received_at.isoformat(),
        "status": batch.status,
        "notes": batch.notes,
        "supplier_invoice_ref": batch.supplier_invoice_ref,
        "movements": [
            {
                "id": str(m.id), "kind": m.kind, "qty_g": m.qty_g,
                "order_id": str(m.order_id) if m.order_id else None,
                "job_id": str(m.job_id) if m.job_id else None,
                "reason": m.reason, "created_at": m.created_at.isoformat(),
            }
            for m in movements
        ],
        "consumptions": [
            {"id": str(c.id), "job_id": str(c.job_id), "job_code": c.job_code, "qty_g": c.qty_g}
            for c in consumptions
        ],
    }


# ---------------------------------------------------------------------------
# alerts
# ---------------------------------------------------------------------------

def get_alerts(session: Session) -> dict:
    """Low stock + quarantined batches."""
    stock_view = get_stock_view(session)
    low_stock = [s for s in stock_view if s["is_low"]]

    quarantined = session.execute(text("""
        SELECT yb.id, yb.code, yb.yarn_type_id, yb.received_g,
               COALESCE(SUM(sm.qty_g), 0) AS on_hand_g
        FROM yarn_batches yb
        LEFT JOIN stock_movements sm ON sm.batch_id = yb.id
        WHERE yb.status = 'quarantined'
        GROUP BY yb.id
    """)).fetchall()

    return {
        "low_stock": low_stock,
        "quarantined_batches": [
            {
                "id": str(r.id), "code": r.code,
                "yarn_type_id": str(r.yarn_type_id),
                "received_g": r.received_g,
                "on_hand_g": int(r.on_hand_g or 0),
            }
            for r in quarantined
        ],
    }


# ---------------------------------------------------------------------------
# purchase needs
# ---------------------------------------------------------------------------

def get_purchase_needs(session: Session) -> list[dict]:
    """Per yarn_type: needed for confirmed orders minus available, plus reorder gap."""
    stock_view = {s["yarn_type_id"]: s for s in get_stock_view(session)}

    # Yarn needed for confirmed/in_production orders (via stock reservations)
    reservations = session.execute(text("""
        SELECT yarn_type_id, SUM(qty_g) AS reserved_g
        FROM stock_reservations WHERE status = 'active'
        GROUP BY yarn_type_id
    """)).fetchall()

    reserved_by_type = {str(r.yarn_type_id): int(r.reserved_g) for r in reservations}

    result = []
    for yt_id, sv in stock_view.items():
        available = sv["available_g"]
        reorder = sv["reorder_level_g"]
        reserved = reserved_by_type.get(yt_id, 0)

        # shortage: how much more is needed
        shortage_g = max(0, reserved - available)
        # reorder gap: how far below reorder level
        reorder_gap_g = max(0, reorder - available)
        needed_g = max(shortage_g, reorder_gap_g)

        if needed_g <= 0:
            continue

        # Suggested supplier
        supplier = session.execute(text("""
            SELECT s.id, s.name FROM supplier_yarn_types syt
            JOIN suppliers s ON s.id = syt.supplier_id
            WHERE syt.yarn_type_id = :ytid AND s.is_active = true
            LIMIT 1
        """), {"ytid": yt_id}).fetchone()

        result.append({
            "yarn_type_id": yt_id,
            "code": sv["code"],
            "available_g": available,
            "reserved_g": reserved,
            "reorder_level_g": reorder,
            "shortage_g": shortage_g,
            "reorder_gap_g": reorder_gap_g,
            "suggested_qty_g": needed_g,
            "suggested_supplier_id": str(supplier.id) if supplier else None,
            "suggested_supplier_name": supplier.name if supplier else None,
        })

    return result


# ---------------------------------------------------------------------------
# purchase orders
# ---------------------------------------------------------------------------

def create_po(session: Session, body: dict, user: dict) -> Any:
    from app.models.materials import PurchaseOrder, PurchaseOrderLine, Supplier, YarnType

    actor_id = _actor(user)
    supplier_id = uuid.UUID(str(body["supplier_id"]))
    sup = session.get(Supplier, supplier_id)
    if sup is None:
        raise AppError("NOT_FOUND", f"Supplier {supplier_id} not found")

    now = app_time.now()
    code = next_code(session, "purchase_order")
    po = PurchaseOrder(
        id=uuid.uuid4(),
        code=code,
        supplier_id=supplier_id,
        status="draft",
        expected_date=body.get("expected_date"),
        notes=body.get("notes"),
        created_at=now,
    )
    session.add(po)
    session.flush()

    lines = []
    for line_data in body.get("lines", []):
        yt_id = uuid.UUID(str(line_data["yarn_type_id"]))
        yt = session.get(YarnType, yt_id)
        if yt is None:
            raise AppError("NOT_FOUND", f"YarnType {yt_id} not found")
        line = PurchaseOrderLine(
            id=uuid.uuid4(),
            po_id=po.id,
            yarn_type_id=yt_id,
            qty_g=int(line_data["qty_g"]),
            rate_paise_per_kg=int(line_data.get("rate_paise_per_kg") or yt.standard_rate_paise_per_kg),
            received_g=0,
            created_at=now,
        )
        session.add(line)
        lines.append(line)

    audit(session, actor_id, "create", "purchase_order", str(po.id),
          after={"code": code, "supplier_id": str(supplier_id)})

    return po, lines


def list_pos(session: Session, filters: dict | None = None) -> tuple[list[dict], int]:
    filters = filters or {}
    page = int(filters.get("page", 1))
    size = int(filters.get("size", 50))
    offset = (page - 1) * size

    where_clauses = []
    params: dict = {}
    if filters.get("status"):
        where_clauses.append("status = :status")
        params["status"] = filters["status"]
    if filters.get("supplier_id"):
        where_clauses.append("supplier_id = :supplier_id")
        params["supplier_id"] = str(filters["supplier_id"])

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    total = session.execute(
        text(f"SELECT COUNT(*) FROM purchase_orders {where_sql}"), params
    ).scalar() or 0

    rows = session.execute(text(f"""
        SELECT id, code, supplier_id, status, expected_date, notes, created_at
        FROM purchase_orders {where_sql}
        ORDER BY created_at DESC LIMIT :limit OFFSET :offset
    """), {**params, "limit": size, "offset": offset}).fetchall()

    items = [
        {
            "id": str(r.id), "code": r.code, "supplier_id": str(r.supplier_id),
            "status": r.status,
            "expected_date": r.expected_date.isoformat() if r.expected_date else None,
            "notes": r.notes, "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
    return items, int(total)


def get_po(session: Session, po_id: uuid.UUID) -> dict:
    from app.models.materials import PurchaseOrder
    po = session.get(PurchaseOrder, po_id)
    if po is None:
        raise AppError("NOT_FOUND", f"PurchaseOrder {po_id} not found")

    lines = session.execute(text("""
        SELECT id, yarn_type_id, qty_g, rate_paise_per_kg, received_g
        FROM purchase_order_lines WHERE po_id = :pid
    """), {"pid": po_id}).fetchall()

    return {
        "id": str(po.id), "code": po.code, "supplier_id": str(po.supplier_id),
        "status": po.status,
        "expected_date": po.expected_date.isoformat() if po.expected_date else None,
        "notes": po.notes, "created_at": po.created_at.isoformat(),
        "lines": [
            {
                "id": str(l.id), "yarn_type_id": str(l.yarn_type_id),
                "qty_g": l.qty_g, "rate_paise_per_kg": l.rate_paise_per_kg,
                "received_g": l.received_g,
            }
            for l in lines
        ],
    }


def update_po(session: Session, po_id: uuid.UUID, body: dict, user: dict) -> dict:
    from app.models.materials import PurchaseOrder
    actor_id = _actor(user)
    po = session.get(PurchaseOrder, po_id)
    if po is None:
        raise AppError("NOT_FOUND", f"PurchaseOrder {po_id} not found")

    if "status" in body:
        po.status = body["status"]
    if "expected_date" in body:
        po.expected_date = body["expected_date"]
    if "notes" in body:
        po.notes = body["notes"]
    po.updated_at = app_time.now()

    audit(session, actor_id, "update", "purchase_order", str(po_id), after=body)
    return get_po(session, po_id)


# ---------------------------------------------------------------------------
# reservations
# ---------------------------------------------------------------------------

def reserve_yarn(
    session: Session,
    yarn_type_id: uuid.UUID,
    order_id: uuid.UUID,
    qty_g: int,
) -> Any:
    from app.models.materials import StockReservation
    now = app_time.now()
    res = StockReservation(
        id=uuid.uuid4(),
        yarn_type_id=yarn_type_id,
        order_id=order_id,
        qty_g=qty_g,
        status="active",
        created_at=now,
    )
    session.add(res)
    return res


def consume_reservation(session: Session, order_id: uuid.UUID, qty_g_consumed: int) -> None:
    """Mark reservations consumed up to qty_g_consumed (in order of creation)."""
    reservations = session.execute(text("""
        SELECT id, qty_g FROM stock_reservations
        WHERE order_id = :oid AND status = 'active'
        ORDER BY created_at
    """), {"oid": order_id}).fetchall()

    remaining = qty_g_consumed
    now = app_time.now()
    for r in reservations:
        if remaining <= 0:
            break
        session.execute(text("""
            UPDATE stock_reservations SET status = 'consumed', updated_at = :now WHERE id = :id
        """), {"id": r.id, "now": now})
        remaining -= r.qty_g


def release_reservations(session: Session, order_id: uuid.UUID) -> None:
    """Set all active reservations for this order to released."""
    session.execute(text("""
        UPDATE stock_reservations SET status = 'released', updated_at = :now
        WHERE order_id = :oid AND status = 'active'
    """), {"oid": order_id, "now": app_time.now()})
