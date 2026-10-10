"""Label PDF endpoints — owned by Lane A."""
from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.deps import get_db, require_permission
from app.api.v1.scan import _entity_label_data

router = APIRouter()


@router.get("/{entity_type}/{id}.pdf")
def label_pdf(
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
