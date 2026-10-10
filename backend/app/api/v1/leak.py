"""Leak tracking endpoints — owned by Lane B."""
from fastapi import APIRouter, Depends
from app.deps import require_permission

router = APIRouter()


@router.get("/leak/today")
def leak_today(user=Depends(require_permission("leak.view"))):
    raise NotImplementedError


@router.get("/leak")
def leak_series(user=Depends(require_permission("leak.view"))):
    raise NotImplementedError


@router.get("/leak/breakdown")
def leak_breakdown(user=Depends(require_permission("leak.view"))):
    raise NotImplementedError