"""Buyer self-service portal — all endpoints require only the buyer.own permission.

A buyer user has User.buyer_id set in the database. Every endpoint here
derives the buyer_id from the JWT subject (user_id) rather than accepting
it as a query/path parameter, so a buyer can only ever see their own data.
"""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select

from app.deps import get_db, require_permission
import app.services.orders as ord_svc
import app.services.master_data as md

router = APIRouter()


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _resolve_buyer_id(user: dict, db) -> uuid.UUID:
    from app.models.identity import User as UserModel
    u = db.scalar(select(UserModel).where(UserModel.id == uuid.UUID(str(user["id"]))))
    if not u or not u.buyer_id:
        raise HTTPException(status_code=403, detail="No buyer profile is linked to this account.")
    return u.buyer_id


# ---------------------------------------------------------------------------
# Buyer profile
# ---------------------------------------------------------------------------

@router.get("/buyer/portal/me")
def buyer_me(
    user=Depends(require_permission("buyer.own")),
    db=Depends(get_db),
):
    buyer_id = _resolve_buyer_id(user, db)
    from app.models.sales import Buyer
    b = db.get(Buyer, buyer_id)
    if not b:
        raise HTTPException(404, "Buyer profile not found.")
    return {
        "id": str(b.id),
        "code": b.code,
        "name": b.name,
        "contact_person": b.contact_person,
        "phone": b.phone,
        "email": b.email,
        "address": b.address,
        "payment_terms_days": b.payment_terms_days,
    }


# ---------------------------------------------------------------------------
# Buyer's fabric type catalogue (name + id only, no pricing)
# ---------------------------------------------------------------------------

@router.get("/buyer/portal/fabric-types")
def buyer_fabric_types(
    user=Depends(require_permission("buyer.own")),
    db=Depends(get_db),
):
    items, _ = md.list_fabric_types(db, active_only=True, page=1, size=200)
    return {"items": [
        {
            "id": str(f.id),
            "code": f.code,
            "name": f.name,
            "construction": getattr(f, "construction", None),
            "width_cm": getattr(f, "width_cm", None),
            "colour": getattr(f, "colour", None),
        }
        for f in items
    ]}


# ---------------------------------------------------------------------------
# Buyer orders
# ---------------------------------------------------------------------------

@router.get("/buyer/portal/orders")
def buyer_orders(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user=Depends(require_permission("buyer.own")),
    db=Depends(get_db),
):
    buyer_id = _resolve_buyer_id(user, db)
    filters = {"buyer_id": buyer_id, "page": page, "size": size}
    items, total = ord_svc.list_orders(db, filters)
    return {"items": items, "total": total, "page": page, "size": size}


@router.post("/buyer/portal/orders", status_code=201)
def buyer_create_order(
    body: dict,
    user=Depends(require_permission("buyer.own")),
    db=Depends(get_db),
):
    buyer_id = _resolve_buyer_id(user, db)
    body["buyer_id"] = str(buyer_id)
    body["_initial_status"] = "pending_approval"
    order = ord_svc.create_order(db, body, user)
    db.commit()
    return ord_svc.get_order(db, order.id, user)
