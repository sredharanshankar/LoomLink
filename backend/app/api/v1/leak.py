"""Leak tracking endpoints — owned by Lane B."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.deps import require_permission, get_db
from app.ripple_service.queries import get_leak_today

router = APIRouter()


@router.get("/leak/today")
def leak_today(user=Depends(require_permission("leak.view")), db: Session = Depends(get_db)):
    raw = get_leak_today(db)
    total = raw.get("total_paise", 0)
    by_cat = raw.get("by_category", {})
    return {
        "idle_paise": by_cat.get("idle", 0),
        "rework_paise": by_cat.get("rework", 0),
        "waste_paise": by_cat.get("waste", 0),
        "overtime_paise": by_cat.get("overtime", 0),
        "total_paise": total,
    }


@router.get("/leak")
def leak_series(user=Depends(require_permission("leak.view")), db: Session = Depends(get_db)):
    raw = get_leak_today(db)
    return {"today": raw, "series": []}


@router.get("/leak/breakdown")
def leak_breakdown(user=Depends(require_permission("leak.view")), db: Session = Depends(get_db)):
    return get_leak_today(db)