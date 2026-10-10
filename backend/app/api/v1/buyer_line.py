"""Buyer messaging endpoints — owned by Lane B."""
from fastapi import APIRouter, Depends
from app.deps import require_permission

router = APIRouter()


@router.post("/buyer-line/chat")
def buyer_chat():
    raise NotImplementedError


@router.post("/buyer-line/whatsapp/webhook")
def whatsapp_webhook():
    raise NotImplementedError


@router.get("/buyer-line/messages")
def buyer_messages(user=Depends(require_permission("orders.view"))):
    raise NotImplementedError