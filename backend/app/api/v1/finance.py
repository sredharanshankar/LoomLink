"""A-M8: Finance router — invoices, payments, supplier bills, expenses, reports."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from app.deps import get_db, require_permission
import app.services.finance as svc

router = APIRouter()


@router.get("/invoices")
def list_invoices(
    buyer_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user=Depends(require_permission("finance.view")),
    db=Depends(get_db),
):
    items, total = svc.list_invoices(db, {
        "buyer_id": str(buyer_id) if buyer_id else None,
        "status": status, "page": page, "size": size,
    })
    return {"items": items, "total": total, "page": page, "size": size}


@router.get("/invoices/{id}")
def get_invoice(
    id: uuid.UUID,
    user=Depends(require_permission("finance.view")),
    db=Depends(get_db),
):
    return svc.get_invoice(db, id)


@router.get("/invoices/{id}.pdf")
def invoice_pdf(
    id: uuid.UUID,
    user=Depends(require_permission("finance.view")),
    db=Depends(get_db),
):
    from app.pdf import invoice as pdf_mod
    from sqlalchemy import text as sql_text

    inv = svc.get_invoice(db, id)
    mill_row = db.execute(
        sql_text("SELECT name, address_line1, gstin FROM mill_settings LIMIT 1")
    ).fetchone()
    mill = {"name": mill_row.name, "address_line1": mill_row.address_line1, "gstin": mill_row.gstin} if mill_row else None
    data = pdf_mod.generate(inv, mill)
    return Response(
        content=data, media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=invoice-{inv['number']}.pdf"},
    )


@router.post("/payments", status_code=201)
def record_payment(
    body: dict,
    user=Depends(require_permission("finance.record_payment")),
    db=Depends(get_db),
):
    result = svc.record_payment(db, body, user)
    db.commit()
    return result


@router.get("/supplier-bills")
def list_bills(
    supplier_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user=Depends(require_permission("finance.view")),
    db=Depends(get_db),
):
    items = svc.list_supplier_bills(db, {
        "supplier_id": str(supplier_id) if supplier_id else None,
        "status": status,
    })
    total = len(items)
    start = (page - 1) * size
    return {"items": items[start:start + size], "total": total, "page": page, "size": size}


@router.post("/supplier-bills", status_code=201)
def create_bill(
    body: dict,
    user=Depends(require_permission("finance.manage")),
    db=Depends(get_db),
):
    result = svc.create_supplier_bill(db, body, user)
    db.commit()
    return result


@router.get("/supplier-bills/{id}")
def get_bill(
    id: uuid.UUID,
    user=Depends(require_permission("finance.view")),
    db=Depends(get_db),
):
    return svc.get_supplier_bill(db, id)


@router.post("/supplier-bills/{id}/payments", status_code=201)
def pay_bill(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("finance.manage")),
    db=Depends(get_db),
):
    result = svc.pay_supplier_bill(db, id, body, user)
    db.commit()
    return result


@router.get("/expenses")
def list_expenses(
    category: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user=Depends(require_permission("finance.view")),
    db=Depends(get_db),
):
    items = svc.list_expenses(db, {
        "category": category, "date_from": date_from, "date_to": date_to,
    })
    total = len(items)
    start = (page - 1) * size
    return {"items": items[start:start + size], "total": total, "page": page, "size": size}


@router.post("/expenses", status_code=201)
def create_expense(
    body: dict,
    user=Depends(require_permission("finance.manage")),
    db=Depends(get_db),
):
    result = svc.create_expense(db, body, user)
    db.commit()
    return result


@router.get("/finance/orders/{id}/cost")
def order_cost(
    id: uuid.UUID,
    user=Depends(require_permission("finance.view_costs")),
    db=Depends(get_db),
):
    return svc.get_order_cost(db, id)


@router.get("/finance/rolls/{id}/cost")
def roll_cost(
    id: uuid.UUID,
    user=Depends(require_permission("finance.view_costs")),
    db=Depends(get_db),
):
    return svc.get_roll_cost(db, id)


@router.get("/finance/month-close")
def month_close(
    period: str = Query(..., description="YYYY-MM"),
    user=Depends(require_permission("finance.view")),
    db=Depends(get_db),
):
    return svc.get_month_close(db, period)


@router.get("/finance/receivables")
def receivables(
    user=Depends(require_permission("finance.view")),
    db=Depends(get_db),
):
    return svc.get_receivables(db)


@router.get("/finance/payables")
def payables(
    user=Depends(require_permission("finance.view")),
    db=Depends(get_db),
):
    return svc.get_payables(db)
