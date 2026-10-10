"""Label PDF endpoints — owned by Lane A."""
from fastapi import APIRouter, Depends
from app.deps import require_permission

router = APIRouter()


@router.get("/labels/{entity_type}/{id}.pdf")
def label_pdf(entity_type: str, id: str, user=Depends(require_permission("labels.print"))):
    raise NotImplementedError


@router.post("/labels/bulk.pdf")
def bulk_labels(user=Depends(require_permission("labels.print"))):
    raise NotImplementedError