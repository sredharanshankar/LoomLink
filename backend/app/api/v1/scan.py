from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.deps import get_db, require_permission
import app.services.scan as scan_svc

router = APIRouter()


@router.get("/{code}")
def resolve_scan(
    code: str,
    user=Depends(require_permission("scan.use")),
    db=Depends(get_db),
):
    return scan_svc.resolve(db, code, user)


@router.get("/{entity_type}/{id}.pdf")
def print_label(
    entity_type: str,
    id: str,
    format: str = Query("thermal"),
    user=Depends(require_permission("labels.print")),
    db=Depends(get_db),
):
    from app.config import get_settings
    from app.pdf.labels import thermal_pdf, a4_sheet_pdf
    settings = get_settings()
    code, lines = _entity_label_data(db, entity_type, id)
    if format == "a4":
        pdf_bytes = a4_sheet_pdf(settings.public_base_url, [(code, lines)])
    else:
        pdf_bytes = thermal_pdf(settings.public_base_url, code, lines)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{code}.pdf"'},
    )


@router.post("/bulk.pdf")
def bulk_labels(
    body: dict,
    user=Depends(require_permission("labels.print")),
    db=Depends(get_db),
):
    from app.config import get_settings
    from app.pdf.labels import a4_sheet_pdf
    settings = get_settings()
    entity_type = body.get("entity_type", "yarn_batch")
    ids = body.get("ids", [])
    items = []
    for eid in ids:
        try:
            code, lines = _entity_label_data(db, entity_type, eid)
            items.append((code, lines))
        except Exception:
            pass
    pdf_bytes = a4_sheet_pdf(settings.public_base_url, items)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="labels.pdf"'},
    )


def _entity_label_data(db, entity_type: str, id: str) -> tuple[str, list[str]]:
    from app.core.errors import AppError
    from sqlalchemy import select
    if entity_type == "yarn_batch":
        from app.models.materials import YarnBatch
        row = db.scalar(select(YarnBatch).where(YarnBatch.id == id))
        if row is None:
            raise AppError("NOT_FOUND", f"YarnBatch {id} not found")
        return row.code, [f"Received: {row.received_g}g", f"Location: {row.location or '-'}"]
    elif entity_type == "roll":
        from app.models.quality import Roll
        row = db.scalar(select(Roll).where(Roll.id == id))
        if row is None:
            raise AppError("NOT_FOUND", f"Roll {id} not found")
        return row.code, [f"Length: {row.length_cm}cm", f"Status: {row.status}"]
    elif entity_type == "order":
        from app.models.sales import Order
        row = db.scalar(select(Order).where(Order.id == id))
        if row is None:
            raise AppError("NOT_FOUND", f"Order {id} not found")
        return row.code, [f"Qty: {row.quantity_cm}cm", f"Due: {row.due_date}"]
    else:
        raise AppError("VALIDATION_ERROR", f"Unknown entity_type: {entity_type}")
