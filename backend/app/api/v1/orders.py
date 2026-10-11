from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, Query

from app.deps import get_db, require_permission
from app.core.errors import AppError
import app.services.master_data as md
import app.services.orders as ord_svc

router = APIRouter()


# ---------------------------------------------------------------------------
# Buyers
# ---------------------------------------------------------------------------

@router.get("/buyers")
def list_buyers(
    active_only: bool = Query(True),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user=Depends(require_permission("buyers.view")),
    db=Depends(get_db),
):
    items, total = md.list_buyers(db, active_only=active_only, page=page, size=size)
    return {"items": [_buyer_out(r) for r in items], "total": total, "page": page, "size": size}


@router.post("/buyers", status_code=201)
def create_buyer(
    body: dict,
    user=Depends(require_permission("buyers.manage")),
    db=Depends(get_db),
):
    row = md.create_buyer(db, body, user)
    db.commit()
    return _buyer_out(row)


@router.get("/buyers/{id}")
def get_buyer(
    id: uuid.UUID,
    user=Depends(require_permission("buyers.view")),
    db=Depends(get_db),
):
    return _buyer_out(md.get_buyer(db, id))


@router.patch("/buyers/{id}")
def update_buyer(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("buyers.manage")),
    db=Depends(get_db),
):
    row = md.update_buyer(db, id, body, user)
    db.commit()
    return _buyer_out(row)


@router.get("/buyers/{id}/outstanding")
def buyer_outstanding(
    id: uuid.UUID,
    user=Depends(require_permission("finance.view")),
    db=Depends(get_db),
):
    from app.services.finance import get_buyer_outstanding
    return get_buyer_outstanding(db, id)


# ---------------------------------------------------------------------------
# Fabric Types
# ---------------------------------------------------------------------------

@router.get("/fabric-types")
def list_fabric_types(
    active_only: bool = Query(True),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user=Depends(require_permission("orders.view")),
    db=Depends(get_db),
):
    items, total = md.list_fabric_types(db, active_only=active_only, page=page, size=size)
    return {"items": [_ft_out(r) for r in items], "total": total, "page": page, "size": size}


@router.post("/fabric-types", status_code=201)
def create_fabric_type(
    body: dict,
    user=Depends(require_permission("orders.manage")),
    db=Depends(get_db),
):
    row = md.create_fabric_type(db, body, user)
    db.commit()
    return _ft_out(row)


@router.get("/fabric-types/{id}")
def get_fabric_type(
    id: uuid.UUID,
    user=Depends(require_permission("orders.view")),
    db=Depends(get_db),
):
    return _ft_out(md.get_fabric_type(db, id))


@router.patch("/fabric-types/{id}")
def update_fabric_type(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("orders.manage")),
    db=Depends(get_db),
):
    row = md.update_fabric_type(db, id, body, user)
    db.commit()
    return _ft_out(row)


# ---------------------------------------------------------------------------
# Route Templates
# ---------------------------------------------------------------------------

@router.get("/route-templates")
def list_route_templates(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user=Depends(require_permission("orders.view")),
    db=Depends(get_db),
):
    items, total = md.list_route_templates(db, page=page, size=size)
    return {"items": [_rt_out(r) for r in items], "total": total, "page": page, "size": size}


@router.post("/route-templates", status_code=201)
def create_route_template(
    body: dict,
    user=Depends(require_permission("orders.manage")),
    db=Depends(get_db),
):
    tmpl, steps = md.create_route_template(db, body, user)
    db.commit()
    return _rt_detail_out(tmpl, steps)


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

@router.post("/orders/feasibility")
def check_feasibility(
    body: dict,
    user=Depends(require_permission("orders.view")),
    db=Depends(get_db),
):
    fabric_type_id = uuid.UUID(str(body["fabric_type_id"]))
    quantity_cm = int(body["quantity_cm"])
    return ord_svc.feasibility(db, fabric_type_id, quantity_cm)


@router.get("/orders/lookup")
def lookup_orders(
    q: str = Query(..., min_length=1),
    user=Depends(require_permission("orders.lookup")),
    db=Depends(get_db),
):
    return {"items": ord_svc.lookup_orders(db, q)}


@router.get("/orders")
def list_orders(
    status: str | None = Query(None),
    buyer_id: uuid.UUID | None = Query(None),
    due_before: str | None = Query(None),
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user=Depends(require_permission("orders.view")),
    db=Depends(get_db),
):
    filters = {
        "status": status, "buyer_id": buyer_id,
        "due_before": due_before, "q": q,
        "page": page, "size": size,
    }
    items, total = ord_svc.list_orders(db, filters)
    return {"items": items, "total": total, "page": page, "size": size}


@router.post("/orders", status_code=201)
def create_order(
    body: dict,
    user=Depends(require_permission("orders.manage")),
    db=Depends(get_db),
):
    order = ord_svc.create_order(db, body, user)
    db.commit()
    return ord_svc.get_order(db, order.id, user)


@router.get("/orders/{id}")
def get_order(
    id: uuid.UUID,
    user=Depends(require_permission("orders.view")),
    db=Depends(get_db),
):
    return ord_svc.get_order(db, id, user)


@router.patch("/orders/{id}")
def update_order(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("orders.manage")),
    db=Depends(get_db),
):
    result = ord_svc.update_order(db, id, body, user)
    db.commit()
    return result


@router.post("/orders/{id}/confirm")
def confirm_order(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("orders.manage")),
    db=Depends(get_db),
):
    result = ord_svc.confirm_order(db, id, body, user)
    db.commit()
    return result


@router.post("/orders/{id}/cancel")
def cancel_order(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("orders.manage")),
    db=Depends(get_db),
):
    result = ord_svc.cancel_order(db, id, body, user)
    db.commit()
    return result


@router.post("/orders/{id}/approve")
def approve_order(
    id: uuid.UUID,
    user=Depends(require_permission("orders.manage")),
    db=Depends(get_db),
):
    from sqlalchemy import text
    from app.core.time import now
    row = db.execute(text("SELECT id, status FROM orders WHERE id = :id"), {"id": str(id)}).fetchone()
    if not row:
        raise AppError("NOT_FOUND", f"Order {id} not found.")
    if row.status != "pending_approval":
        raise AppError("INVALID_STATE", f"Order status is '{row.status}', not pending_approval.")
    db.execute(
        text("UPDATE orders SET status = 'draft', updated_at = :now WHERE id = :id"),
        {"id": str(id), "now": now()},
    )
    db.commit()
    return {"id": str(id), "status": "draft"}


@router.post("/orders/{id}/reject")
def reject_order(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("orders.manage")),
    db=Depends(get_db),
):
    from sqlalchemy import text
    from app.core.time import now
    row = db.execute(text("SELECT id, status FROM orders WHERE id = :id"), {"id": str(id)}).fetchone()
    if not row:
        raise AppError("NOT_FOUND", f"Order {id} not found.")
    if row.status != "pending_approval":
        raise AppError("INVALID_STATE", f"Order status is '{row.status}', not pending_approval.")
    db.execute(
        text("UPDATE orders SET status = 'cancelled', updated_at = :now WHERE id = :id"),
        {"id": str(id), "now": now()},
    )
    db.commit()
    return {"id": str(id), "status": "cancelled", "reason": body.get("reason", "")}


@router.get("/orders/{id}/timeline")
def order_timeline(
    id: uuid.UUID,
    user=Depends(require_permission("orders.view")),
    db=Depends(get_db),
):
    return ord_svc.get_timeline(db, id)


# ---------------------------------------------------------------------------
# Public buyer tracking (no auth required)
# ---------------------------------------------------------------------------

@router.get("/orders/track/{token}")
def track_order(token: str, db=Depends(get_db)):
    from sqlalchemy import text
    row = db.execute(text("""
        SELECT o.code, o.status, o.quantity_cm, o.due_date, o.promised_date,
               o.updated_at, o.created_at,
               b.name AS buyer_name,
               ft.name AS fabric_type_name,
               ft.colour AS fabric_colour
        FROM orders o
        JOIN buyers b ON b.id = o.buyer_id
        JOIN fabric_types ft ON ft.id = o.fabric_type_id
        WHERE o.tracking_token = :tok
    """), {"tok": token}).fetchone()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Order not found")
    # Count rolls ready (passed QC) — rolls.order_id links directly to orders
    rolls = db.execute(text("""
        SELECT COUNT(*) FROM rolls r
        JOIN orders o ON o.id = r.order_id
        WHERE o.tracking_token = :tok AND r.status = 'passed'
    """), {"tok": token}).scalar() or 0
    metres_ready = db.execute(text("""
        SELECT COALESCE(SUM(r.length_cm), 0) FROM rolls r
        JOIN orders o ON o.id = r.order_id
        WHERE o.tracking_token = :tok AND r.status = 'passed'
    """), {"tok": token}).scalar() or 0
    ship_date = row.promised_date or row.due_date
    return {
        "order_number": row.code,
        "status": row.status,
        "fabric_type": row.fabric_type_name,
        "fabric_colour": row.fabric_colour,
        "quantity_m": round(row.quantity_cm / 100, 1),
        "metres_ready": round(metres_ready / 100, 1),
        "rolls_passed": rolls,
        "expected_ship_date": ship_date.isoformat() if ship_date else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else row.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# serializers
# ---------------------------------------------------------------------------

def _buyer_out(r) -> dict:
    return {
        "id": str(r.id),
        "code": r.code,
        "name": r.name,
        "contact_person": r.contact_person,
        "phone": r.phone,
        "whatsapp": r.whatsapp,
        "email": r.email,
        "gstin": r.gstin,
        "state_code": r.state_code,
        "address": r.address,
        "payment_terms_days": r.payment_terms_days,
        "default_late_penalty_paise_per_day": r.default_late_penalty_paise_per_day,
        "is_active": r.is_active,
        "created_at": r.created_at.isoformat(),
    }


def _ft_out(r) -> dict:
    return {
        "id": str(r.id),
        "code": r.code,
        "name": r.name,
        "construction": r.construction,
        "width_cm": r.width_cm,
        "gsm": r.gsm,
        "colour": r.colour,
        "yarn_type_id": str(r.yarn_type_id),
        "yarn_g_per_100m": r.yarn_g_per_100m,
        "route_template_id": str(r.route_template_id) if r.route_template_id else None,
        "hsn_code": r.hsn_code,
        "default_price_paise_per_m": r.default_price_paise_per_m,
        "gst_bp": r.gst_bp,
        "is_active": r.is_active,
        "created_at": r.created_at.isoformat(),
    }


def _rt_out(r) -> dict:
    return {
        "id": str(r.id),
        "name": r.name,
        "description": r.description,
        "created_at": r.created_at.isoformat(),
    }


def _rt_detail_out(tmpl, steps) -> dict:
    out = _rt_out(tmpl)
    out["steps"] = [
        {"id": str(s.id), "seq": s.seq, "stage": s.stage, "buffer_minutes": s.buffer_minutes}
        for s in steps
    ]
    return out
