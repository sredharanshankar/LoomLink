"""Bol voice-sentence parser endpoint — owned by Lane B."""
from fastapi import APIRouter, Depends
from app.deps import require_permission

router = APIRouter()


@router.post("/bol/parse")
def bol_parse(user=Depends(require_permission("bol.use"))):
    raise NotImplementedError