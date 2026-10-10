from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, Query

from app.deps import get_db, require_permission
import app.services.master_data as md

router = APIRouter()


# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------

@router.get("/suppliers")
def list_suppliers(
    active_only: bool = Query(True),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user=Depends(require_permission("suppliers.view")),
    db=Depends(get_db),
):
    items, total = md.list_suppliers(db, active_only=active_only, page=page, size=size)
    return {"items": [_sup_out(r) for r in items], "total": total, "page": page, "size": size}


@router.post("/suppliers", status_code=201)
def create_supplier(
    body: dict,
    user=Depends(require_permission("suppliers.manage")),
    db=Depends(get_db),
):
    row = md.create_supplier(db, body, user)
    db.commit()
    return _sup_out(row)


@router.get("/suppliers/{id}")
def get_supplier(
    id: uuid.UUID,
    user=Depends(require_permission("suppliers.view")),
    db=Depends(get_db),
):
    row = md.get_supplier(db, id)
    yarn_types = md.supplier_yarn_types(db, id)
    out = _sup_out(row)
    out["yarn_types"] = [_yt_out(y) for y in yarn_types]
    return out


@router.patch("/suppliers/{id}")
def update_supplier(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("suppliers.manage")),
    db=Depends(get_db),
):
    row = md.update_supplier(db, id, body, user)
    db.commit()
    return _sup_out(row)


@router.get("/suppliers/{id}/history")
def supplier_history(
    id: uuid.UUID,
    user=Depends(require_permission("suppliers.view")),
    db=Depends(get_db),
):
    from sqlalchemy import text
    rows = db.execute(
        text(
            "SELECT code, status, expected_date, created_at FROM purchase_orders "
            "WHERE supplier_id = :sid ORDER BY created_at DESC LIMIT 50"
        ),
        {"sid": id},
    ).fetchall()
    return {"items": [
        {"code": r[0], "status": r[1], "expected_date": str(r[2]) if r[2] else None,
         "created_at": r[3].isoformat()}
        for r in rows
    ]}


# ---------------------------------------------------------------------------
# Yarn Types
# ---------------------------------------------------------------------------

@router.get("/yarn-types")
def list_yarn_types(
    active_only: bool = Query(True),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user=Depends(require_permission("inventory.view")),
    db=Depends(get_db),
):
    items, total = md.list_yarn_types(db, active_only=active_only, page=page, size=size)
    return {"items": [_yt_out(r) for r in items], "total": total, "page": page, "size": size}


@router.post("/yarn-types", status_code=201)
def create_yarn_type(
    body: dict,
    user=Depends(require_permission("inventory.manage")),
    db=Depends(get_db),
):
    row = md.create_yarn_type(db, body, user)
    db.commit()
    return _yt_out(row)


@router.get("/yarn-types/{id}")
def get_yarn_type(
    id: uuid.UUID,
    user=Depends(require_permission("inventory.view")),
    db=Depends(get_db),
):
    return _yt_out(md.get_yarn_type(db, id))


@router.patch("/yarn-types/{id}")
def update_yarn_type(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("inventory.manage")),
    db=Depends(get_db),
):
    row = md.update_yarn_type(db, id, body, user)
    db.commit()
    return _yt_out(row)


# ---------------------------------------------------------------------------
# Inventory operations — implemented in A-M2
# ---------------------------------------------------------------------------

@router.get("/inventory/stock")
def get_stock(user=Depends(require_permission("inventory.view"))):
    raise NotImplementedError


@router.get("/inventory/batches")
def list_batches(user=Depends(require_permission("inventory.view"))):
    raise NotImplementedError


@router.get("/inventory/batches/{id}")
def get_batch(id: str, user=Depends(require_permission("inventory.view"))):
    raise NotImplementedError


@router.post("/inventory/receipts")
def receive_stock(user=Depends(require_permission("inventory.receive"))):
    raise NotImplementedError


@router.post("/inventory/issues")
def issue_stock(user=Depends(require_permission("inventory.issue"))):
    raise NotImplementedError


@router.post("/inventory/returns")
def return_stock(user=Depends(require_permission("inventory.issue"))):
    raise NotImplementedError


@router.post("/inventory/adjustments")
def adjust_stock(user=Depends(require_permission("inventory.adjust"))):
    raise NotImplementedError


@router.get("/inventory/alerts")
def inventory_alerts(user=Depends(require_permission("inventory.view"))):
    raise NotImplementedError


@router.get("/inventory/purchase-needs")
def purchase_needs(user=Depends(require_permission("inventory.view"))):
    raise NotImplementedError


@router.get("/purchase-orders")
def list_pos(user=Depends(require_permission("purchasing.manage"))):
    raise NotImplementedError


@router.post("/purchase-orders")
def create_po(user=Depends(require_permission("purchasing.manage"))):
    raise NotImplementedError


@router.get("/purchase-orders/{id}")
def get_po(id: str, user=Depends(require_permission("purchasing.manage"))):
    raise NotImplementedError


@router.patch("/purchase-orders/{id}")
def update_po(id: str, user=Depends(require_permission("purchasing.manage"))):
    raise NotImplementedError


# ---------------------------------------------------------------------------
# serializers
# ---------------------------------------------------------------------------

def _sup_out(r) -> dict:
    return {
        "id": str(r.id),
        "code": r.code,
        "name": r.name,
        "contact_person": r.contact_person,
        "phone": r.phone,
        "email": r.email,
        "address": r.address,
        "gstin": r.gstin,
        "payment_terms_days": r.payment_terms_days,
        "notes": r.notes,
        "is_active": r.is_active,
        "created_at": r.created_at.isoformat(),
    }


def _yt_out(r) -> dict:
    return {
        "id": str(r.id),
        "code": r.code,
        "material": r.material,
        "count_label": r.count_label,
        "colour": r.colour,
        "colour_hex": r.colour_hex,
        "reorder_level_g": r.reorder_level_g,
        "standard_rate_paise_per_kg": r.standard_rate_paise_per_kg,
        "is_active": r.is_active,
        "created_at": r.created_at.isoformat(),
    }
