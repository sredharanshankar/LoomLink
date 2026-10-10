from fastapi import APIRouter, Depends
from app.deps import require_permission

router = APIRouter()


@router.get("/{code}")
def resolve_scan(code: str, user=Depends(require_permission("scan.use"))):
    raise NotImplementedError


@router.get("/{entity_type}/{id}.pdf")
def print_label(entity_type: str, id: str, format: str = "thermal", user=Depends(require_permission("labels.print"))):
    raise NotImplementedError


@router.post("/bulk.pdf")
def bulk_labels(user=Depends(require_permission("labels.print"))):
    raise NotImplementedError