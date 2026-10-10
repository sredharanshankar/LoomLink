"""SEED §8: live state at D 11:00 — Lane B.

Creates active orders ORD-102, ORD-104, ORD-107, ORD-109, ORD-110, ORD-112
and sets machine/job state so the Ripple WV-02 breakdown demo works.
"""
from __future__ import annotations
import uuid
import secrets
import datetime as dt
from sqlalchemy.orm import Session
from sqlalchemy import text

_TODAY = dt.date(2026, 10, 10)
_DEMO_NOW = dt.datetime(2026, 10, 10, 11, 0, 0, tzinfo=dt.timezone.utc)


def _d(offset: int = 0) -> dt.date:
    return _TODAY + dt.timedelta(days=offset)


def _ts(hour: int, minute: int = 0, day_offset: int = 0) -> dt.datetime:
    base = _TODAY + dt.timedelta(days=day_offset)
    return dt.datetime(base.year, base.month, base.day, hour, minute, 0, tzinfo=dt.timezone.utc)


def run(session: Session) -> None:
    _seed_yarn_inventory(session)
    _seed_active_orders(session)
    _seed_attendance_today(session)


# ---------------------------------------------------------------------------
# Yarn inventory: set stock so blue yarn is below reorder (active alert)
# ---------------------------------------------------------------------------

def _seed_yarn_inventory(session: Session) -> None:
    stock = [
        # (yarn_code, qty_g, batch_code, supplier_code, rate_paise_per_kg)
        ("YT-COT-40S-WHT", 380000, "YB-2610-01", "SUP-001", 21000),
        ("YT-COT-40S-BLU",  78000, "YB-2610-02", "SUP-001", 24500),  # below reorder (120 kg)
        ("YT-PC-240S-GRY", 245000, "YB-2610-03", "SUP-002", 19000),
        ("YT-COT-30S-NVY", 190000, "YB-2610-04", "SUP-002", 26000),
        # Last-month batches for quality defect patterns
        ("YT-COT-40S-BLU",  12000, "YB-2609-11", "SUP-001", 24500),  # defective batch
    ]

    for yarn_code, qty_g, batch_code, sup_code, rate in stock:
        if session.execute(text("SELECT id FROM yarn_batches WHERE code = :c"), {"c": batch_code}).fetchone():
            continue

        yt = session.execute(text("SELECT id FROM yarn_types WHERE code = :c"), {"c": yarn_code}).fetchone()
        sup = session.execute(text("SELECT id FROM suppliers WHERE code = :c"), {"c": sup_code}).fetchone()
        if not yt or not sup:
            continue

        recv_day_offset = -3 if batch_code.startswith("YB-2610") else -15
        bid = str(uuid.uuid4())
        session.execute(text("""
            INSERT INTO yarn_batches (id, code, yarn_type_id, supplier_id, received_g,
                rate_paise_per_kg, received_at, status, created_at)
            VALUES (:id, :code, :ytid, :sid, :qty, :rate, :recv, 'active', :now)
        """), {
            "id": bid, "code": batch_code, "ytid": str(yt[0]), "sid": str(sup[0]),
            "qty": qty_g, "rate": rate,
            "recv": _ts(8, day_offset=recv_day_offset),
            "now": _ts(8),
        })


# ---------------------------------------------------------------------------
# Active orders + jobs at D 11:00
# ---------------------------------------------------------------------------

def _seed_active_orders(session: Session) -> None:
    def buyer(code):
        return session.execute(text("SELECT id FROM buyers WHERE code = :c"), {"c": code}).fetchone()

    def fabric(code):
        return session.execute(text("SELECT id FROM fabric_types WHERE code = :c"), {"c": code}).fetchone()

    def machine(code):
        return session.execute(text("SELECT id FROM machines WHERE code = :c"), {"c": code}).fetchone()

    ORDERS = [
        # code, buyer, fabric, qty_cm, price_ppm, due_offset, status
        ("ORD-102", "BUY-001", "FAB-POP-GRY",  90000,  9800, +1, "in_production"),
        ("ORD-104", "BUY-001", "FAB-POP-BLU", 120000, 12500, +3, "in_production"),
        ("ORD-107", "BUY-002", "FAB-POP-GRY",  80000,  9800, +4, "confirmed"),
        ("ORD-109", "BUY-003", "FAB-SHT-WHT", 150000, 16000, +7, "in_production"),
        ("ORD-110", "BUY-004", "FAB-TWL-NVY", 100000, 18500, +10, "in_production"),
        ("ORD-112", "BUY-001", "FAB-POP-BLU",  60000, 12500, +9, "confirmed"),
    ]

    for code, buyer_code, fab_code, qty_cm, price, due_off, status in ORDERS:
        if session.execute(text("SELECT id FROM orders WHERE code = :c"), {"c": code}).fetchone():
            continue

        b = buyer(buyer_code)
        f = fabric(fab_code)
        if not b or not f:
            continue

        oid = str(uuid.uuid4())
        session.execute(text("""
            INSERT INTO orders (id, code, buyer_id, fabric_type_id, quantity_cm, price_paise_per_m,
                status, tracking_token, due_date, created_at)
            VALUES (:id, :code, :bid, :ftid, :qty, :price, :st, :tok, :dby, :now)
        """), {
            "id": oid, "code": code, "bid": str(b[0]), "ftid": str(f[0]),
            "qty": qty_cm, "price": price, "st": status,
            "tok": secrets.token_urlsafe(24),
            "dby": _d(due_off),
            "now": _ts(8, day_offset=-1),
        })

        # Create jobs per order
        if code == "ORD-102":
            # Weaving active on WV-01, started at 06:00; DY-01 has previous lot
            m = machine("WV-01")
            jid = str(uuid.uuid4())
            session.execute(text("""
                INSERT INTO jobs (id, code, order_id, stage, seq, unit, planned_qty, produced_qty,
                    waste_qty, machine_id, status, started_at, finished_at, created_at)
                VALUES (:id, :code, :oid, 'weaving', 1, 'cm', :qty, :done, 0,
                    :mid, 'running', :start, NULL, :now)
            """), {
                "id": jid, "code": f"{code}-WEV",
                "oid": oid, "qty": qty_cm,
                "done": 55000,
                "mid": str(m[0]) if m else None,
                "start": _ts(6), "now": _ts(8, day_offset=-1),
            })
            # Update WV-01 status to running and link current_job_id
            if m:
                session.execute(text("""
                    UPDATE machines SET status='running', current_job_id=:jid,
                        status_changed_at=:ts WHERE id=:mid
                """), {"mid": str(m[0]), "jid": jid, "ts": _ts(6)})

        elif code == "ORD-104":
            # Weaving on WV-02, 500m done, 700m left
            m = machine("WV-02")
            jid = str(uuid.uuid4())
            session.execute(text("""
                INSERT INTO jobs (id, code, order_id, stage, seq, unit, planned_qty, produced_qty,
                    waste_qty, machine_id, status, started_at, finished_at, created_at)
                VALUES (:id, :code, :oid, 'weaving', 1, 'cm', :qty, :done, 0,
                    :mid, 'running', :start, NULL, :now)
            """), {
                "id": jid, "code": f"{code}-WEV",
                "oid": oid, "qty": qty_cm,
                "done": 50000,
                "mid": str(m[0]) if m else None,
                "start": _ts(6, day_offset=-1), "now": _ts(8, day_offset=-1),
            })
            if m:
                session.execute(text("""
                    UPDATE machines SET status='running', current_job_id=:jid,
                        status_changed_at=:ts WHERE id=:mid
                """), {"mid": str(m[0]), "jid": jid, "ts": _ts(6, day_offset=-1)})
            # Subsequent stages queued
            for seq, stage in [(2, "dyeing"), (3, "finishing")]:
                session.execute(text("""
                    INSERT INTO jobs (id, code, order_id, stage, seq, unit, planned_qty, produced_qty,
                        waste_qty, machine_id, status, started_at, finished_at, created_at)
                    VALUES (:id, :code, :oid, :stage, :seq, 'cm', :qty, 0, 0, NULL, 'queued', NULL, NULL, :now)
                """), {
                    "id": str(uuid.uuid4()), "code": f"{code}-{stage[:3].upper()}",
                    "oid": oid, "stage": stage, "seq": seq, "qty": qty_cm,
                    "now": _ts(8, day_offset=-1),
                })

        elif code == "ORD-107":
            # Confirmed, queued next on WV-02
            session.execute(text("""
                INSERT INTO jobs (id, code, order_id, stage, seq, unit, planned_qty, produced_qty,
                    waste_qty, machine_id, status, started_at, finished_at, created_at)
                VALUES (:id, :code, :oid, 'weaving', 1, 'cm', :qty, 0, 0,
                    (SELECT id FROM machines WHERE code='WV-02'), 'queued', NULL, NULL, :now)
            """), {
                "id": str(uuid.uuid4()), "code": f"{code}-WEV",
                "oid": oid, "qty": qty_cm, "now": _ts(8, day_offset=-1),
            })

        elif code == "ORD-109":
            # Weaving on WV-03
            m = machine("WV-03")
            jid = str(uuid.uuid4())
            session.execute(text("""
                INSERT INTO jobs (id, code, order_id, stage, seq, unit, planned_qty, produced_qty,
                    waste_qty, machine_id, status, started_at, finished_at, created_at)
                VALUES (:id, :code, :oid, 'weaving', 1, 'cm', :qty, :done, 0,
                    :mid, 'running', :start, NULL, :now)
            """), {
                "id": jid, "code": f"{code}-WEV",
                "oid": oid, "qty": qty_cm,
                "done": 22000,
                "mid": str(m[0]) if m else None,
                "start": _ts(20, day_offset=-1), "now": _ts(8, day_offset=-1),
            })
            if m:
                session.execute(text("""
                    UPDATE machines SET status='running', current_job_id=:jid,
                        status_changed_at=:ts WHERE id=:mid
                """), {"mid": str(m[0]), "jid": jid, "ts": _ts(20, day_offset=-1)})

        elif code == "ORD-110":
            # Spinning on SP-01 (route R2)
            m = machine("SP-01")
            jid = str(uuid.uuid4())
            session.execute(text("""
                INSERT INTO jobs (id, code, order_id, stage, seq, unit, planned_qty, produced_qty,
                    waste_qty, machine_id, status, started_at, finished_at, created_at)
                VALUES (:id, :code, :oid, 'spinning', 1, 'cm', :qty, :done, 0,
                    :mid, 'running', :start, NULL, :now)
            """), {
                "id": jid, "code": f"{code}-SPN",
                "oid": oid, "qty": qty_cm,
                "done": 30000,
                "mid": str(m[0]) if m else None,
                "start": _ts(6), "now": _ts(8, day_offset=-1),
            })
            if m:
                session.execute(text("""
                    UPDATE machines SET status='running', current_job_id=:jid,
                        status_changed_at=:ts WHERE id=:mid
                """), {"mid": str(m[0]), "jid": jid, "ts": _ts(6)})

        elif code == "ORD-112":
            # Confirmed but blocked: blue yarn shortage
            pass

    # FN-01: finishing a previous lot (ORD-102 finishing stage)
    fn = machine("FN-01")
    ord102 = session.execute(text("SELECT id FROM orders WHERE code='ORD-102'")).fetchone()
    if fn and ord102:
        fn_jid = str(uuid.uuid4())
        session.execute(text("""
            INSERT INTO jobs (id, code, order_id, stage, seq, unit, planned_qty, produced_qty,
                waste_qty, machine_id, status, started_at, finished_at, created_at)
            VALUES (:id, :code, :oid, 'finishing', 2, 'cm', 90000, 41000, 0,
                :mid, 'running', :start, NULL, :now)
        """), {
            "id": fn_jid, "code": "ORD-102-FIN",
            "oid": str(ord102[0]), "mid": str(fn[0]),
            "start": _ts(7), "now": _ts(8, day_offset=-1),
        })
        session.execute(text("""
            UPDATE machines SET status='running', current_job_id=:jid,
                status_changed_at=:ts WHERE id=:mid
        """), {"mid": str(fn[0]), "jid": fn_jid, "ts": _ts(7)})

    # DY-02 stays idle (for Idle Hunter demo)


# ---------------------------------------------------------------------------
# Attendance today (shift A workers checked in)
# ---------------------------------------------------------------------------

def _seed_attendance_today(session: Session) -> None:
    shift_a_workers = session.execute(text("""
        SELECT id FROM workers WHERE default_shift = 'A' AND is_active = true
    """)).fetchall()

    for w in shift_a_workers:
        if session.execute(
            text("SELECT id FROM attendance WHERE worker_id = :wid AND date = :d"),
            {"wid": str(w[0]), "d": _TODAY},
        ).fetchone():
            continue

        session.execute(text("""
            INSERT INTO attendance (id, worker_id, shift_code, date, check_in_at, check_out_at,
                overtime_minutes, status, source, created_at)
            VALUES (:id, :wid, 'A', :d, :ci, NULL, 0, 'present', 'seed', :now)
        """), {
            "id": str(uuid.uuid4()), "wid": str(w[0]),
            "d": _TODAY, "ci": _ts(6), "now": _ts(6),
        })
