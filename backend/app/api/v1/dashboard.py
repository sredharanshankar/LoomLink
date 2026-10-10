"""A-M9: Dashboard, notifications, public tracking router."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, Query
from app.deps import get_db, require_permission
import app.services.dashboard as dash_svc
import app.services.notifications as notif_svc

router = APIRouter()


@router.get("/dashboard/owner")
def owner_dashboard(
    user=Depends(require_permission("dashboard.owner")),
    db=Depends(get_db),
):
    return dash_svc.get_owner_dashboard(db)


@router.get("/dashboard/daily-brief")
def daily_brief(
    user=Depends(require_permission("dashboard.owner")),
    db=Depends(get_db),
):
    return dash_svc.get_daily_brief(db)


@router.get("/dashboard/production")
def production_dashboard(
    user=Depends(require_permission("production.view")),
    db=Depends(get_db),
):
    return dash_svc.get_production_dashboard(db)


@router.get("/public/track/{tracking_token}")
def track_order(tracking_token: str, db=Depends(get_db)):
    result = dash_svc.get_public_tracking(db, tracking_token)
    if result is None:
        from app.core.errors import AppError
        raise AppError("NOT_FOUND", "Tracking token not found.")
    return result


@router.get("/buyer/orders")
def buyer_orders(
    user=Depends(require_permission("buyer.own")),
    db=Depends(get_db),
):
    from sqlalchemy import text
    bid = str(user.buyer_id) if hasattr(user, "buyer_id") else str(user.id)
    rows = db.execute(
        text(
            "SELECT o.id, o.code, o.status, o.quantity_cm, o.dispatch_by, o.tracking_token "
            "FROM orders o "
            "WHERE o.buyer_id = :bid AND o.deleted_at IS NULL "
            "ORDER BY o.created_at DESC"
        ),
        {"bid": bid},
    ).fetchall()
    return {"items": [dict(r._mapping) for r in rows]}


@router.get("/notifications")
def list_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user=Depends(require_permission("")),
    db=Depends(get_db),
):
    items, total = notif_svc.list_notifications(db, user.id, unread_only=unread_only, page=page, size=size)
    unread = notif_svc.get_unread_count(db, user.id)
    return {"items": items, "total": total, "unread_count": unread, "page": page, "size": size}


@router.post("/notifications/{id}/read", status_code=200)
def mark_read(
    id: uuid.UUID,
    user=Depends(require_permission("")),
    db=Depends(get_db),
):
    notif_svc.mark_read(db, user.id, id)
    db.commit()
    return {"ok": True}


@router.post("/notifications/read-all", status_code=200)
def read_all(
    user=Depends(require_permission("")),
    db=Depends(get_db),
):
    notif_svc.mark_all_read(db, user.id)
    db.commit()
    return {"ok": True}
