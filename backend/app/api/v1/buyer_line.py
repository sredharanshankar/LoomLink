"""Buyer messaging endpoints — owned by Lane B."""
from __future__ import annotations
import re
import uuid
import datetime as dt
from fastapi import APIRouter, Depends, Body
from sqlalchemy import text
from app.deps import require_permission, get_db

router = APIRouter()


def _parse_order_code(message: str) -> str | None:
    m = re.search(r"(ORD-\d+)", message.upper())
    return m.group(1) if m else None


@router.post("/buyer-line/chat")
def buyer_chat(
    body: dict = Body(...),
    db=Depends(get_db),
):
    """Simulate a buyer sending their order number over WhatsApp and getting live status."""
    msg = (body.get("message") or "").strip()
    code = _parse_order_code(msg)

    if not code:
        return {
            "reply": "Hi! Please send your order number (e.g. ORD-104) to get live status.",
            "order": None,
        }

    row = db.execute(text("""
        SELECT o.id, o.code, o.status, o.quantity_cm, o.due_date, o.promised_date,
               b.id AS buyer_id, b.name AS buyer_name,
               ft.name AS fabric_type
        FROM orders o
        JOIN buyers b ON b.id = o.buyer_id
        JOIN fabric_types ft ON ft.id = o.fabric_type_id
        WHERE o.code = :code
    """), {"code": code}).fetchone()

    if not row:
        return {"reply": f"Order {code} not found. Please check and try again.", "order": None}

    ship = (row.promised_date or row.due_date).strftime("%d %b")
    status_map = {
        "draft": "being processed",
        "confirmed": "confirmed, awaiting production",
        "in_production": "currently in production",
        "qc": "undergoing quality check",
        "ready": "ready for dispatch",
        "partially_dispatched": "partially dispatched",
        "dispatched": "dispatched",
        "cancelled": "cancelled",
    }
    status_label = status_map.get(row.status, row.status.replace("_", " "))
    qty_m = round(row.quantity_cm / 100, 0)
    reply = (
        f"*{code}* — {row.fabric_type}\n"
        f"Qty: {qty_m:.0f} m | Status: {status_label}\n"
        f"Expected ship: {ship}\n\n"
        f"_Everest Textile Mills via LoomLink_"
    )

    # Log inbound + outbound messages
    now = dt.datetime.now(dt.timezone.utc)
    for direction, body_text in [("in", msg), ("out", reply)]:
        db.execute(text("""
            INSERT INTO buyer_messages (id, buyer_id, order_id, channel, direction, body, status, created_at)
            VALUES (:id, :bid, :oid, 'whatsapp', :dir, :body, 'delivered', :now)
        """), {
            "id": str(uuid.uuid4()), "bid": str(row.buyer_id), "oid": str(row.id),
            "dir": direction, "body": body_text, "now": now,
        })
    db.commit()

    return {
        "reply": reply,
        "order": {
            "code": code,
            "status": row.status,
            "ship_date": (row.promised_date or row.due_date).isoformat(),
        },
    }


@router.post("/buyer-line/whatsapp/webhook")
def whatsapp_webhook(body: dict = Body(default={})):
    """WhatsApp Business API webhook receiver (sandbox). Always returns 200."""
    return {"status": "ok"}


@router.get("/buyer-line/messages")
def buyer_messages(
    user=Depends(require_permission("orders.view")),
    db=Depends(get_db),
):
    """Return recent buyer messages from buyer_messages table."""
    rows = db.execute(text("""
        SELECT bm.id, bm.direction, bm.body, bm.channel, bm.status, bm.created_at,
               b.name AS buyer_name,
               o.code AS order_code
        FROM buyer_messages bm
        JOIN buyers b ON b.id = bm.buyer_id
        LEFT JOIN orders o ON o.id = bm.order_id
        ORDER BY bm.created_at DESC
        LIMIT 50
    """)).fetchall()

    return {
        "items": [
            {
                "id": str(r.id),
                "direction": r.direction,
                "text": r.body,
                "channel": r.channel,
                "status": r.status,
                "buyer": r.buyer_name,
                "order_code": r.order_code,
                "at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }
