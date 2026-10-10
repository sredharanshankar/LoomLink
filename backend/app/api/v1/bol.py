"""Bol voice-sentence parser endpoint — owned by Lane B."""
from __future__ import annotations
import re
from fastapi import APIRouter, Depends, Body
from sqlalchemy import text
from app.deps import require_permission, get_db

router = APIRouter()

# ---------------------------------------------------------------------------
# Keyword patterns for structured parsing
# ---------------------------------------------------------------------------

_BREAKDOWN_WORDS = re.compile(
    r"\b(band|breakdown|stop|fault|brok|down|aagipoy|toot|खराब|बंद|bandh)\b", re.I
)
_PROGRESS_WORDS = re.compile(
    r"\b(metres?|meter|done|complete|मीटर|metre|kiya|aagindi)\b", re.I
)
_RECEIVE_WORDS = re.compile(
    r"\b(kilo|kg|cotton|yarn|fabric|received|receive|आया|banda|laya|delivery)\b", re.I
)
_HANDOVER_WORDS = re.compile(
    r"\b(handover|hand over|shift end|shift over|over|shift)\b", re.I
)
_NUMBER_RE = re.compile(r"\b(\d+(?:\.\d+)?)\b")
_ORDER_RE = re.compile(r"\b(ORD-\d+)\b", re.I)
_MACHINE_RE = re.compile(r"\b(WV-\d+|SP-\d+|DY-\d+|FN-\d+|loom\s+\d+|machine\s+\d+)\b", re.I)


def _extract_numbers(text: str) -> list[float]:
    return [float(m) for m in _NUMBER_RE.findall(text)]


def _normalize_machine(raw: str) -> str:
    """Normalise 'loom 4' → 'WV-04'."""
    raw = raw.strip().upper()
    if re.match(r"^(WV|SP|DY|FN)-", raw):
        return raw
    num_match = re.search(r"\d+", raw)
    n = int(num_match.group()) if num_match else 1
    prefix = "WV"  # default to weaving
    return f"{prefix}-{n:02d}"


@router.post("/bol/parse")
def bol_parse(
    body: dict = Body(...),
    user=Depends(require_permission("bol.use")),
    db=Depends(get_db),
):
    """
    Parse a voice sentence into a structured LoomLink command.

    Input: { "text": "loom chaar band ho gaya, belt toot gaya" }
    Output: { "intent": "machine.breakdown", "machine_code": "WV-04", ... }
    """
    sentence: str = (body.get("text") or "").strip()
    if not sentence:
        return {"intent": "unknown", "text": sentence, "confidence": 0.0, "confirmation_card": None}

    numbers = _extract_numbers(sentence)
    order_match = _ORDER_RE.search(sentence)
    machine_match = _MACHINE_RE.search(sentence)

    order_code = order_match.group(1).upper() if order_match else None
    machine_code_raw = machine_match.group(1) if machine_match else None
    machine_code = _normalize_machine(machine_code_raw) if machine_code_raw else None

    # ── breakdown ────────────────────────────────────────────────────────────
    if _BREAKDOWN_WORDS.search(sentence):
        # Try to resolve machine code from DB if given
        machine_name = machine_code
        if machine_code:
            row = db.execute(
                text("SELECT name FROM machines WHERE code = :c"), {"c": machine_code}
            ).fetchone()
            machine_name = row[0] if row else machine_code

        # Detect reason from common words
        reason = None
        if re.search(r"\b(belt|बेल्ट)\b", sentence, re.I):
            reason = "belt_break"
        elif re.search(r"\b(motor|मोटर)\b", sentence, re.I):
            reason = "motor_fault"
        elif re.search(r"\b(warp|धागा)\b", sentence, re.I):
            reason = "warp_break"
        elif re.search(r"\b(power|current|bijli|बिजली)\b", sentence, re.I):
            reason = "power_failure"

        card = {
            "title": "Record breakdown?",
            "machine": machine_name or "(tap to select)",
            "reason": reason or "(tap to select)",
            "action": "machine.breakdown",
        }
        return {
            "intent": "machine.breakdown",
            "machine_code": machine_code,
            "reason_code": reason,
            "text": sentence,
            "confidence": 0.85 if machine_code else 0.6,
            "confirmation_card": card,
        }

    # ── job progress ─────────────────────────────────────────────────────────
    if _PROGRESS_WORDS.search(sentence) and numbers:
        metres = numbers[0]
        card = {
            "title": f"Log {metres:.0f} metres?",
            "order": order_code or "(tap to select)",
            "metres": metres,
            "action": "job.progress",
        }
        return {
            "intent": "job.progress",
            "order_code": order_code,
            "quantity_m": metres,
            "text": sentence,
            "confidence": 0.8 if order_code else 0.65,
            "confirmation_card": card,
        }

    # ── yarn receipt ─────────────────────────────────────────────────────────
    if _RECEIVE_WORDS.search(sentence) and numbers:
        qty_kg = numbers[0]
        card = {
            "title": f"Receive {qty_kg:.0f} kg?",
            "quantity_kg": qty_kg,
            "order": order_code,
            "action": "inventory.receive",
        }
        return {
            "intent": "inventory.receive",
            "order_code": order_code,
            "quantity_kg": qty_kg,
            "text": sentence,
            "confidence": 0.75,
            "confirmation_card": card,
        }

    # ── shift handover ────────────────────────────────────────────────────────
    if _HANDOVER_WORDS.search(sentence):
        card = {
            "title": "End shift & hand over?",
            "machine": machine_code,
            "action": "job.handover",
        }
        return {
            "intent": "job.handover",
            "machine_code": machine_code,
            "text": sentence,
            "confidence": 0.75,
            "confirmation_card": card,
        }

    # ── unknown ───────────────────────────────────────────────────────────────
    return {
        "intent": "unknown",
        "text": sentence,
        "confidence": 0.0,
        "confirmation_card": {
            "title": "Couldn't understand",
            "hint": "Try: 'loom 2 breakdown' or '200 metres done on ORD-104'",
        },
    }
