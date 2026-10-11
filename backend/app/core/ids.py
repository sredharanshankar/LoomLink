from __future__ import annotations
import datetime as dt
import threading
from uuid import UUID
from sqlalchemy.orm import Session
from app.core import time as app_time


def next_code(
    session: Session,
    entity: str,
    *,
    at: dt.datetime | None = None,
    order_no: int | None = None,
) -> str:
    """Generate the next human code for an entity using the code_sequences table.

    Uses SELECT ... FOR UPDATE to prevent duplicates under concurrent load.
    Resets per period where the format contains a date component.
    """
    from sqlalchemy import text

    ref_dt = at or app_time.now()
    local_dt = app_time.to_local(ref_dt)
    today = local_dt.date()

    key = _sequence_key(entity, today, order_no)

    # Row-level lock
    row = session.execute(
        text("SELECT last_value FROM code_sequences WHERE prefix = :k FOR UPDATE"),
        {"k": key},
    ).fetchone()

    if row is None:
        # Sync from existing codes so we never collide on restart / first use
        existing_max = _max_existing_seq(session, entity, key)
        session.execute(
            text(
                "INSERT INTO code_sequences (prefix, last_value) VALUES (:k, :v) "
                "ON CONFLICT (prefix) DO UPDATE SET last_value = GREATEST(code_sequences.last_value, :v)"
            ),
            {"k": key, "v": existing_max},
        )
        # Re-acquire lock after insert
        row = session.execute(
            text("SELECT last_value FROM code_sequences WHERE prefix = :k FOR UPDATE"),
            {"k": key},
        ).fetchone()

    current = row[0] if row else 0
    next_val = current + 1

    session.execute(
        text("UPDATE code_sequences SET last_value = :v WHERE prefix = :k"),
        {"v": next_val, "k": key},
    )

    return _format_code(entity, next_val, today, order_no)


def _sequence_key(entity: str, date: dt.date, order_no: int | None) -> str:
    """Build the sequence key (includes period so resets happen automatically)."""
    match entity:
        case "supplier":
            return "SUP"
        case "buyer":
            return "BUY"
        case "worker":
            return "EMP"
        case "yarn_batch":
            yymm = date.strftime("%y%m")
            return f"YB-{yymm}"
        case "purchase_order":
            yymm = date.strftime("%y%m")
            return f"PO-{yymm}"
        case "order":
            return "ORD"
        case "job":
            if order_no is None:
                raise ValueError("order_no required for job codes")
            return f"JOB-{order_no}"
        case "roll":
            if order_no is None:
                raise ValueError("order_no required for roll codes")
            return f"ROLL-{order_no}"
        case "dispatch":
            yymm = date.strftime("%y%m")
            return f"DSP-{yymm}"
        case "invoice":
            from app.core.time import fy_label
            fy = fy_label(date)
            return f"INV-{fy}"
        case "payment":
            yymm = date.strftime("%y%m")
            return f"PAY-{yymm}"
        case "supplier_bill":
            yymm = date.strftime("%y%m")
            return f"SB-{yymm}"
        case "ripple_event":
            yymmdd = date.strftime("%y%m%d")
            return f"RPL-{yymmdd}"
        case _:
            return entity.upper()


def _format_code(entity: str, seq: int, date: dt.date, order_no: int | None) -> str:
    yymm = date.strftime("%y%m")
    yymmdd = date.strftime("%y%m%d")

    match entity:
        case "supplier":
            return f"SUP-{seq:03d}"
        case "buyer":
            return f"BUY-{seq:03d}"
        case "worker":
            return f"EMP-{seq:03d}"
        case "yarn_batch":
            return f"YB-{yymm}-{seq:02d}"
        case "purchase_order":
            return f"PO-{yymm}-{seq:02d}"
        case "order":
            # Starts at 101
            return f"ORD-{100 + seq}"
        case "job":
            stage_seq = f"{seq:02d}"
            return f"JOB-{order_no}-{stage_seq}"
        case "roll":
            return f"ROLL-{order_no}-{seq:02d}"
        case "dispatch":
            return f"DSP-{yymm}-{seq:02d}"
        case "invoice":
            from app.core.time import fy_label
            fy = fy_label(date)
            fy_fmt = f"{fy[:2]}-{fy[2:]}"
            return f"INV-{fy_fmt}-{seq:04d}"
        case "payment":
            return f"PAY-{yymm}-{seq:02d}"
        case "supplier_bill":
            return f"SB-{yymm}-{seq:02d}"
        case "ripple_event":
            return f"RPL-{yymmdd}-{seq:02d}"
        case _:
            return f"{entity.upper()}-{seq:03d}"


def _max_existing_seq(session: Session, entity: str, prefix_key: str) -> int:
    """Read the highest sequence number already in the DB to avoid collisions on first use."""
    # Each query extracts the numeric counter from the code and returns the max.
    try:
        match entity:
            case "yarn_batch" | "purchase_order" | "dispatch" | "payment" | "supplier_bill":
                # Codes: YB-2610-03, PO-2610-01, DSP-2610-01 — last segment is the seq
                table = {
                    "yarn_batch": "yarn_batches",
                    "purchase_order": "purchase_orders",
                    "dispatch": "dispatches",
                    "payment": "payments",
                    "supplier_bill": "supplier_bills",
                }[entity]
                row = session.execute(
                    text(
                        f"SELECT MAX(CAST(split_part(code, '-', 3) AS INTEGER)) "
                        f"FROM {table} WHERE code LIKE :pat"
                    ),
                    {"pat": f"{prefix_key}-%"},
                ).fetchone()
                return int(row[0]) if row and row[0] is not None else 0

            case "supplier":
                row = session.execute(text("SELECT MAX(CAST(split_part(code,'-',2) AS INTEGER)) FROM suppliers")).fetchone()
                return int(row[0]) if row and row[0] is not None else 0
            case "buyer":
                row = session.execute(text("SELECT MAX(CAST(split_part(code,'-',2) AS INTEGER)) FROM buyers")).fetchone()
                return int(row[0]) if row and row[0] is not None else 0
            case "worker":
                row = session.execute(text("SELECT MAX(CAST(split_part(code,'-',2) AS INTEGER)) FROM workers")).fetchone()
                return int(row[0]) if row and row[0] is not None else 0
            case "order":
                # ORD-101 = seq 1 (offset 100)
                row = session.execute(text("SELECT MAX(CAST(split_part(code,'-',2) AS INTEGER)) - 100 FROM orders")).fetchone()
                return max(int(row[0]) if row and row[0] is not None else 0, 0)
            case _:
                return 0
    except Exception:
        return 0
