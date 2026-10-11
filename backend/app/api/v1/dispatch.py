"""A-M6: Dispatch router — finished stock, create/scan/confirm dispatches, packing list PDF."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response
from app.deps import get_db, require_permission
import app.services.dispatch as svc

router = APIRouter()


@router.get("/dispatch/finished-stock")
def finished_stock(user=Depends(require_permission("dispatch.view")), db=Depends(get_db)):
    return {"items": svc.get_finished_stock(db)}


@router.get("/dispatch/aged-stock")
def aged_stock(
    days: int = Query(30, ge=1),
    user=Depends(require_permission("dispatch.view")),
    db=Depends(get_db),
):
    return {"items": svc.get_aged_stock(db, days=days)}


@router.get("/dispatches")
def list_dispatches(
    status: str | None = Query(None),
    order_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user=Depends(require_permission("dispatch.view")),
    db=Depends(get_db),
):
    items, total = svc.list_dispatches(db, {
        "status": status,
        "order_id": str(order_id) if order_id else None,
        "page": page, "size": size,
    })
    return {"items": items, "total": total, "page": page, "size": size}


@router.post("/dispatches", status_code=201)
def create_dispatch(body: dict, user=Depends(require_permission("dispatch.manage")), db=Depends(get_db)):
    result = svc.create_dispatch(db, body, user)
    db.commit()
    return result


@router.get("/dispatches/{id}")
def get_dispatch(id: uuid.UUID, user=Depends(require_permission("dispatch.view")), db=Depends(get_db)):
    return svc.get_dispatch(db, id)


@router.post("/dispatches/{id}/scan", status_code=200)
def scan_dispatch(
    id: uuid.UUID, body: dict, request: Request,
    user=Depends(require_permission("dispatch.manage")), db=Depends(get_db),
):
    idem = request.headers.get("Idempotency-Key")
    if idem:
        body = {**body, "idempotency_key": idem}
    result = svc.scan_roll(db, id, body, user)
    db.commit()
    return result


@router.delete("/dispatches/{id}/items/{item_id}", status_code=200)
def remove_dispatch_item(
    id: uuid.UUID, item_id: uuid.UUID,
    user=Depends(require_permission("dispatch.manage")), db=Depends(get_db),
):
    result = svc.remove_item(db, id, item_id, user)
    db.commit()
    return result


@router.post("/dispatches/{id}/confirm", status_code=200)
def confirm_dispatch(
    id: uuid.UUID, body: dict,
    user=Depends(require_permission("dispatch.manage")), db=Depends(get_db),
):
    result = svc.confirm_dispatch(db, id, body, user)
    db.commit()
    return result


@router.post("/dispatches/{id}/status", status_code=200)
def update_dispatch_status(
    id: uuid.UUID, body: dict,
    user=Depends(require_permission("dispatch.manage")), db=Depends(get_db),
):
    result = svc.update_dispatch_status(db, id, body, user)
    db.commit()
    return result


@router.get("/dispatches/{id}/packing-list.pdf")
def packing_list(
    id: uuid.UUID,
    user=Depends(require_permission("dispatch.view")), db=Depends(get_db),
):
    from app.pdf import packing_list as pdf_mod
    from sqlalchemy import text as sql_text

    dispatch = svc.get_dispatch(db, id)
    mill_row = db.execute(sql_text("SELECT name, address_line1, gstin FROM mill_settings LIMIT 1")).fetchone()
    mill = {
        "name": mill_row.name, "address_line1": mill_row.address_line1, "gstin": mill_row.gstin
    } if mill_row else None
    data = pdf_mod.generate(dispatch, mill)
    return Response(
        content=data, media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=packing-list-{dispatch['code']}.pdf"},
    )
