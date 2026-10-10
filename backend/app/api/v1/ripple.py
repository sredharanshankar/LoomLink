"""Ripple & intelligence endpoints — owned by Lane B."""
from fastapi import APIRouter, Depends
from app.deps import require_permission

router = APIRouter()


@router.get("/ripple/forecast")
def get_forecast(user=Depends(require_permission("ripple.view"))):
    raise NotImplementedError


@router.post("/ripple/recompute")
def recompute(user=Depends(require_permission("ripple.manage"))):
    raise NotImplementedError


@router.get("/ripple/orders/{id}/health")
def order_health(id: str, user=Depends(require_permission("orders.view"))):
    raise NotImplementedError


@router.get("/ripple/events")
def list_events(user=Depends(require_permission("ripple.view"))):
    raise NotImplementedError


@router.get("/ripple/events/{id}")
def get_event(id: str, user=Depends(require_permission("ripple.view"))):
    raise NotImplementedError


@router.post("/ripple/events/{id}/fixes/{fix_id}/apply")
def apply_fix(id: str, fix_id: str, user=Depends(require_permission("ripple.apply"))):
    raise NotImplementedError


@router.post("/ripple/events/{id}/dismiss")
def dismiss_event(id: str, user=Depends(require_permission("ripple.apply"))):
    raise NotImplementedError


@router.post("/ripple/what-if")
def what_if(user=Depends(require_permission("ripple.view"))):
    raise NotImplementedError


@router.post("/ripple/promise-date")
def promise_date(user=Depends(require_permission("orders.manage"))):
    raise NotImplementedError


@router.get("/ripple/idle-hunter")
def idle_hunter(user=Depends(require_permission("ripple.view"))):
    raise NotImplementedError