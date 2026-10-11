"""A-M10: Seed 14 days of historical production data for the demo mill."""
from __future__ import annotations
import uuid
import datetime as dt
import random
import secrets
from sqlalchemy.orm import Session
from sqlalchemy import text


_TODAY = dt.date(2026, 10, 10)
_DAYS = 14


def _d(offset: int) -> dt.date:
    return _TODAY - dt.timedelta(days=offset)


def _dt(date: dt.date, hour: int, minute: int = 0) -> dt.datetime:
    return dt.datetime(date.year, date.month, date.day, hour % 24, minute % 60, tzinfo=dt.timezone.utc)


def run(session: Session) -> None:
    """Insert 14 days of demo history: attendance + completed orders with jobs."""
    _seed_attendance(session)
    _seed_named_orders(session)
    _seed_historical_orders(session)


# ---------------------------------------------------------------------------
# SEED §7 — specific named historical orders
# ---------------------------------------------------------------------------

def _seed_named_orders(session: Session) -> None:
    """Seed ORD-101, ORD-103, ORD-105, ORD-106 per SEED.md §7."""
    import secrets as _sec

    def _get_buyer(code: str):
        return session.execute(text("SELECT id FROM buyers WHERE code = :c"), {"c": code}).fetchone()

    def _get_fabric(code: str):
        return session.execute(text("SELECT id FROM fabric_types WHERE code = :c"), {"c": code}).fetchone()

    def _get_machine(code: str):
        return session.execute(text("SELECT id FROM machines WHERE code = :c"), {"c": code}).fetchone()

    NAMED = [
        # (code, buyer_code, fabric_code, qty_cm, price_paise_per_m, dispatch_offset, status, paid_paise_fn)
        ("ORD-101", "BUY-004", "FAB-SHT-WHT", 180000, 16000, -9,  "dispatched", "full"),
        ("ORD-103", "BUY-001", "FAB-POP-BLU", 100000, 12500, -5,  "dispatched", "half"),
        ("ORD-105", "BUY-003", "FAB-POP-GRY", 150000,  9800, -3,  "dispatched", "none"),
        ("ORD-106", "BUY-002", "FAB-POP-GRY",  60000,  9800, -12, "dispatched", "none"),
    ]

    for code, buyer_code, fab_code, qty_cm, price, dispatch_off, status, pay in NAMED:
        if session.execute(text("SELECT id FROM orders WHERE code = :c"), {"c": code}).fetchone():
            continue
        buyer = _get_buyer(buyer_code)
        fab = _get_fabric(fab_code)
        if not buyer or not fab:
            continue

        oid = str(uuid.uuid4())
        dispatch_date = _TODAY + dt.timedelta(days=dispatch_off)
        order_date = dispatch_date - dt.timedelta(days=4)
        tok = _sec.token_urlsafe(24)

        session.execute(text("""
            INSERT INTO orders (id, code, buyer_id, fabric_type_id, quantity_cm, price_paise_per_m,
                status, tracking_token, due_date, created_at)
            VALUES (:id, :code, :bid, :ftid, :qty, :price, :st, :tok, :dby, :now)
        """), {
            "id": oid, "code": code, "bid": str(buyer.id), "ftid": str(fab.id),
            "qty": qty_cm, "price": price, "st": status, "tok": tok,
            "dby": dispatch_date,
            "now": _dt(order_date, 8),
        })

        # Jobs: weaving + dyeing + finishing (or spinning first for R2 fabrics)
        stages = ["spinning", "weaving", "dyeing", "finishing"] if fab_code == "FAB-TWL-NVY" else ["weaving", "dyeing", "finishing"]
        for seq, stage in enumerate(stages, start=1):
            jid = str(uuid.uuid4())
            machine = None
            if stage == "weaving":
                machine = _get_machine("WV-01")
            elif stage == "dyeing":
                machine = _get_machine("DY-01")
            elif stage == "finishing":
                machine = _get_machine("FN-01")
            elif stage == "spinning":
                machine = _get_machine("SP-01")
            session.execute(text("""
                INSERT INTO jobs (id, code, order_id, stage, seq, unit, planned_qty, produced_qty, waste_qty,
                    machine_id, status, started_at, finished_at, created_at)
                VALUES (:id, :code, :oid, :stage, :seq, 'cm', :qty, :pqty, :wqty,
                    :mid, 'completed', :start, :end, :now)
            """), {
                "id": jid, "code": f"{code}-{stage[:3].upper()}",
                "oid": oid, "stage": stage, "seq": seq, "qty": qty_cm,
                "pqty": qty_cm - qty_cm // 100,
                "wqty": qty_cm // 200,
                "mid": str(machine[0]) if machine else None,
                "start": _dt(order_date + dt.timedelta(days=seq - 1), 8),
                "end": _dt(order_date + dt.timedelta(days=seq), 16),
                "now": _dt(order_date, 8),
            })

        # Invoice
        inv_id = str(uuid.uuid4())
        total_paise = qty_cm * price // 100  # qty_cm in cm, price per m, so /100
        paid_paise = total_paise if pay == "full" else (total_paise // 2 if pay == "half" else 0)
        inv_code = f"INV-{code[4:]}"  # INV-101 etc.
        # Map pay status to invoice status values the schema uses
        inv_status = "paid" if pay == "full" else ("issued" if pay == "half" else "issued")
        gst_bp = 500  # 5% GST
        gst_paise = total_paise * gst_bp // 10000
        session.execute(text("""
            INSERT INTO invoices (id, number, buyer_id, order_id, issue_date, due_date,
                subtotal_paise, gst_bp, gst_paise, total_paise, amount_paid_paise, status, created_at)
            VALUES (:id, :num, :bid, :oid, :iss, :due,
                :sub, :gstbp, :gst, :total, :paid, :st, :now)
        """), {
            "id": inv_id, "num": inv_code, "bid": str(buyer.id), "oid": oid,
            "iss": dispatch_date,
            "due": dispatch_date + dt.timedelta(days=30),
            "sub": total_paise, "gstbp": gst_bp, "gst": gst_paise,
            "total": total_paise + gst_paise,
            "paid": paid_paise,
            "st": inv_status,
            "now": _dt(dispatch_date, 16),
        })


# ---------------------------------------------------------------------------
# Attendance history
# ---------------------------------------------------------------------------

def _seed_attendance(session: Session) -> None:
    workers = session.execute(text("SELECT id, default_shift FROM workers LIMIT 12")).fetchall()
    shift_rows = session.execute(text("SELECT code, start_time, end_time FROM shifts")).fetchall()
    shifts = {r.code: r for r in shift_rows}

    for day_offset in range(1, _DAYS + 1):
        date = _d(day_offset)
        if date.weekday() == 6:  # skip Sundays
            continue

        for w in workers:
            shift_code = w.default_shift or "A"
            shift = shifts.get(shift_code)
            if shift is None:
                continue

            if random.random() < 0.10:  # 90% attendance rate
                continue

            existing = session.execute(
                text("SELECT id FROM attendance WHERE worker_id = :wid AND date = :d"),
                {"wid": str(w.id), "d": date},
            ).fetchone()
            if existing:
                continue

            sh, sm = [int(x) for x in str(shift.start_time)[:5].split(":")]
            eh, em = [int(x) for x in str(shift.end_time)[:5].split(":")]
            late_min = random.choice([0, 0, 0, 5, 8, 12])
            ot_min = 60 if random.random() < 0.15 else 0
            status = "late" if late_min > 10 else "present"

            ci = _dt(date, sh, sm + late_min)
            end_date = date if eh > sh else date + dt.timedelta(days=1)
            co = _dt(end_date, eh, em + ot_min)

            session.execute(
                text(
                    "INSERT INTO attendance (id, worker_id, shift_code, date, check_in_at, check_out_at, "
                    "overtime_minutes, status, source, created_at) "
                    "VALUES (:id, :wid, :sc, :d, :ci, :co, :ot, :st, 'seed', :now)"
                ),
                {
                    "id": str(uuid.uuid4()), "wid": str(w.id), "sc": shift_code,
                    "d": date, "ci": ci, "co": co, "ot": ot_min, "st": status,
                    "now": _dt(date, 0),
                },
            )


# ---------------------------------------------------------------------------
# Historical completed orders + jobs
# ---------------------------------------------------------------------------

def _seed_historical_orders(session: Session) -> None:
    buyers = session.execute(text("SELECT id FROM buyers LIMIT 3")).fetchall()
    fabric_types = session.execute(text("SELECT id FROM fabric_types LIMIT 3")).fetchall()
    machines = session.execute(text("SELECT id, stage FROM machines WHERE status != 'offline' LIMIT 8")).fetchall()

    if not buyers or not fabric_types:
        return

    machines_by_stage: dict[str, list] = {}
    for m in machines:
        machines_by_stage.setdefault(m.stage, []).append(m)

    for day_offset in range(_DAYS, 6, -1):
        date = _d(day_offset)
        if date.weekday() == 6:
            continue

        order_code = f"ORD-H{day_offset:02d}"
        exists = session.execute(
            text("SELECT id FROM orders WHERE code = :code"), {"code": order_code}
        ).fetchone()
        if exists:
            continue

        buyer = random.choice(buyers)
        ft = random.choice(fabric_types)
        quantity_cm = random.choice([500000, 750000, 1000000])
        price_paise = random.choice([4500, 5000, 5500])
        order_id = uuid.uuid4()
        tracking_token = secrets.token_urlsafe(24)
        dispatched_at = _dt(date + dt.timedelta(days=2), 15)

        session.execute(
            text(
                "INSERT INTO orders (id, code, buyer_id, fabric_type_id, quantity_cm, price_paise_per_m, "
                "status, tracking_token, due_date, created_at) "
                "VALUES (:id, :code, :bid, :ftid, :qty, :price, 'dispatched', :tok, :dby, :now)"
            ),
            {
                "id": str(order_id), "code": order_code, "bid": str(buyer.id),
                "ftid": str(ft.id), "qty": quantity_cm, "price": price_paise,
                "tok": tracking_token,
                "dby": date + dt.timedelta(days=3),
                "now": _dt(date, 8),
            },
        )

        for seq, stage in enumerate(["weaving", "dyeing", "finishing"], start=1):
            job_id = uuid.uuid4()
            job_code = f"JOB-H{day_offset:02d}-{stage[:3].upper()}"
            ms = machines_by_stage.get(stage, [])
            machine_id = random.choice(ms).id if ms else None
            produced = quantity_cm - random.randint(0, quantity_cm // 50)
            waste = random.randint(0, quantity_cm // 100)

            session.execute(
                text(
                    "INSERT INTO jobs (id, code, order_id, stage, seq, unit, planned_qty, produced_qty, waste_qty, "
                    "machine_id, status, started_at, finished_at, created_at) "
                    "VALUES (:id, :code, :oid, :stage, :seq, 'cm', :qty, :pqty, :wqty, "
                    ":mid, 'completed', :start, :end, :now)"
                ),
                {
                    "id": str(job_id), "code": job_code, "oid": str(order_id),
                    "stage": stage, "seq": seq, "qty": quantity_cm,
                    "pqty": produced, "wqty": waste,
                    "mid": str(machine_id) if machine_id else None,
                    "start": _dt(date, 8 + seq),
                    "end": _dt(date + dt.timedelta(days=1), 6 + seq),
                    "now": _dt(date, 8),
                },
            )
