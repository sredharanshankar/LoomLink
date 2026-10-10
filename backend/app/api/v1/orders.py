from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, Query

from app.deps import get_db, require_permission
import app.services.master_data as md

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
def buyer_outstanding(id: str, user=Depends(require_permission("finance.view"))):
    raise NotImplementedError


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
# Orders — implemented in A-M3
# ---------------------------------------------------------------------------

@router.get("/orders")
def list_orders(user=Depends(require_permission("orders.view"))):
    raise NotImplementedError


@router.post("/orders")
def create_order(user=Depends(require_permission("orders.manage"))):
    raise NotImplementedError


@router.get("/orders/lookup")
def lookup_orders(user=Depends(require_permission("orders.lookup"))):
    raise NotImplementedError


@router.get("/orders/{id}")
def get_order(id: str, user=Depends(require_permission("orders.view"))):
    raise NotImplementedError


@router.patch("/orders/{id}")
def update_order(id: str, user=Depends(require_permission("orders.manage"))):
    raise NotImplementedError


@router.post("/orders/feasibility")
def check_feasibility(user=Depends(require_permission("orders.view"))):
    raise NotImplementedError


@router.post("/orders/{id}/confirm")
def confirm_order(id: str, user=Depends(require_permission("orders.manage"))):
    raise NotImplementedError


@router.post("/orders/{id}/cancel")
def cancel_order(id: str, user=Depends(require_permission("orders.manage"))):
    raise NotImplementedError


@router.get("/orders/{id}/timeline")
def order_timeline(id: str, user=Depends(require_permission("orders.view"))):
    raise NotImplementedError


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
