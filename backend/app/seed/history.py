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
    _seed_historical_orders(session)


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
                    "INSERT INTO attendance (id, worker_id, shift_code, date, checked_in_at, checked_out_at, "
                    "overtime_minutes, status, created_at) "
                    "VALUES (:id, :wid, :sc, :d, :ci, :co, :ot, :st, :now)"
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
                "status, tracking_token, dispatch_by, dispatched_at, deleted_at, created_at) "
                "VALUES (:id, :code, :bid, :ftid, :qty, :price, 'dispatched', :tok, :dby, :dat, NULL, :now)"
            ),
            {
                "id": str(order_id), "code": order_code, "bid": str(buyer.id),
                "ftid": str(ft.id), "qty": quantity_cm, "price": price_paise,
                "tok": tracking_token,
                "dby": date + dt.timedelta(days=3),
                "dat": dispatched_at,
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
                    "machine_id, status, started_at, completed_at, created_at) "
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
