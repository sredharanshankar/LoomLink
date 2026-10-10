from fastapi import APIRouter, Depends
from app.deps import require_permission

router = APIRouter()


@router.get("/dashboard/owner")
def owner_dashboard(user=Depends(require_permission("dashboard.owner"))):
    raise NotImplementedError


@router.get("/dashboard/daily-brief")
def daily_brief(user=Depends(require_permission("dashboard.owner"))):
    raise NotImplementedError


@router.get("/dashboard/production")
def production_dashboard(user=Depends(require_permission("production.view"))):
    raise NotImplementedError


@router.get("/public/track/{tracking_token}")
def track_order(tracking_token: str):
    raise NotImplementedError


@router.get("/buyer/orders")
def buyer_orders(user=Depends(require_permission("buyer.own"))):
    raise NotImplementedError


@router.get("/notifications")
def list_notifications(user=Depends(require_permission(""))):
    raise NotImplementedError


@router.post("/notifications/{id}/read")
def mark_read(id: str, user=Depends(require_permission(""))):
    raise NotImplementedError


@router.post("/notifications/read-all")
def read_all(user=Depends(require_permission(""))):
    raise NotImplementedError