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


@router.get("/leak/today")
def leak_today(user=Depends(require_permission("leak.view"))):
    raise NotImplementedError


@router.get("/leak")
def leak_series(user=Depends(require_permission("leak.view"))):
    raise NotImplementedError


@router.get("/leak/breakdown")
def leak_breakdown(user=Depends(require_permission("leak.view"))):
    raise NotImplementedError


@router.post("/bol/parse")
def bol_parse(user=Depends(require_permission("bol.use"))):
    raise NotImplementedError


@router.post("/buyer-line/chat")
def buyer_chat():
    raise NotImplementedError


@router.post("/buyer-line/whatsapp/webhook")
def whatsapp_webhook():
    raise NotImplementedError


@router.get("/buyer-line/messages")
def buyer_messages(user=Depends(require_permission("orders.view"))):
    raise NotImplementedError


@router.post("/simulator/machines/{id}/emit")
def simulator_emit(id: str, user=Depends(require_permission("ripple.manage"))):
    raise NotImplementedError


@router.post("/demo/reset")
def demo_reset(user=Depends(require_permission("demo.reset"))):
    raise NotImplementedError