"""A-M5: Quality control router — rolls, inspections, defect patterns, passports."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, Query
from app.deps import get_db, require_permission
import app.services.quality as svc

router = APIRouter()


@router.post("/rolls", status_code=201)
def create_rolls(body: dict, user=Depends(require_permission("rolls.create")), db=Depends(get_db)):
    result = svc.create_rolls(db, body, user)
    db.commit()
    return result


@router.get("/rolls")
def list_rolls(
    status: str | None = Query(None),
    order_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user=Depends(require_permission("quality.view")),
    db=Depends(get_db),
):
    items, total = svc.list_rolls(db, {
        "status": status,
        "order_id": str(order_id) if order_id else None,
        "page": page, "size": size,
    })
    return {"items": items, "total": total, "page": page, "size": size}


@router.get("/rolls/{id}")
def get_roll(id: uuid.UUID, user=Depends(require_permission("quality.view")), db=Depends(get_db)):
    return svc.get_roll(db, id)


@router.post("/rolls/{id}/inspections", status_code=201)
def inspect_roll(
    id: uuid.UUID, body: dict,
    user=Depends(require_permission("quality.inspect")), db=Depends(get_db),
):
    result = svc.inspect_roll(db, id, body, user)
    db.commit()
    return result


@router.post("/rolls/{id}/rework-complete")
def rework_complete(
    id: uuid.UUID,
    user=Depends(require_permission("quality.inspect")), db=Depends(get_db),
):
    result = svc.rework_complete(db, id, user)
    db.commit()
    return result


@router.get("/quality/queues")
def quality_queues(user=Depends(require_permission("quality.view")), db=Depends(get_db)):
    return svc.get_quality_queues(db)


@router.get("/quality/defect-patterns")
def defect_patterns(user=Depends(require_permission("quality.view")), db=Depends(get_db)):
    return {"patterns": svc.get_defect_patterns(db)}


@router.get("/rolls/{id}/passport")
def roll_passport(
    id: uuid.UUID,
    user=Depends(require_permission("rolls.passport")), db=Depends(get_db),
):
    return svc.get_roll_passport(db, id, user)
