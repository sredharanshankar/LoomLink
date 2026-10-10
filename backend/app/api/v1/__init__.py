from fastapi import APIRouter
from app.api.v1 import (
    auth, health, settings as settings_router, ws,
    scan, labels, inventory, orders, production, quality,
    dispatch, workers, finance, dashboard, users,
    ripple, leak, bol, buyer_line, buyer_portal,
)
from app.config import get_settings

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(settings_router.router, prefix="/settings", tags=["settings"])
router.include_router(ws.router, tags=["ws"])
router.include_router(scan.router, prefix="/scan", tags=["scan"])
router.include_router(labels.router, tags=["labels"])
router.include_router(inventory.router, tags=["inventory"])
router.include_router(orders.router, tags=["orders"])
router.include_router(production.router, tags=["production"])
router.include_router(quality.router, tags=["quality"])
router.include_router(dispatch.router, tags=["dispatch"])
router.include_router(workers.router, tags=["workers"])
router.include_router(finance.router, tags=["finance"])
router.include_router(dashboard.router, tags=["dashboard"])
router.include_router(users.router, tags=["users"])
# Lane B routers
router.include_router(ripple.router, tags=["ripple"])
router.include_router(leak.router, tags=["leak"])
router.include_router(bol.router, tags=["bol"])
router.include_router(buyer_line.router, tags=["buyer-line"])
router.include_router(buyer_portal.router, tags=["buyer-portal"])
# Demo-only routers (mounted conditionally)
if get_settings().demo_mode:
    from app.api.v1 import simulator, demo
    router.include_router(simulator.router, tags=["simulator"])
    router.include_router(demo.router, tags=["demo"])