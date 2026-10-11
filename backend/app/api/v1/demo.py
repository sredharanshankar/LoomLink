"""Demo convenience endpoints — only mounted when DEMO_MODE=true."""
from __future__ import annotations
import uuid
import datetime as dt
from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.deps import require_permission, get_db

router = APIRouter()

_DEMO_NOW = dt.datetime(2026, 10, 10, 11, 0, 0, tzinfo=dt.timezone.utc)


def _ts(hour: int, minute: int = 0, day_offset: int = 0) -> dt.datetime:
    base = dt.date(2026, 10, 10) + dt.timedelta(days=day_offset)
    return dt.datetime(base.year, base.month, base.day, hour, minute, 0, tzinfo=dt.timezone.utc)


@router.post("/demo/patch-jobs")
def demo_patch_jobs(
    user=Depends(require_permission("demo.reset")),
    db=Depends(get_db),
):
    """
    Patch live DB to ensure all running machines have a current_job_id set.
    Inserts missing FN-01 finishing job and links it, without wiping any data.
    """
    patched = []

    # Fix FN-01: insert ORD-102-FIN finishing job if not already present
    fn = db.execute(text("SELECT id FROM machines WHERE code='FN-01'")).fetchone()
    ord102 = db.execute(text("SELECT id FROM orders WHERE code='ORD-102'")).fetchone()
    if fn and ord102:
        existing = db.execute(
            text("SELECT id FROM jobs WHERE code='ORD-102-FIN'")
        ).fetchone()
        if not existing:
            fn_jid = str(uuid.uuid4())
            db.execute(text("""
                INSERT INTO jobs (id, code, order_id, stage, seq, unit, planned_qty, produced_qty,
                    waste_qty, machine_id, status, started_at, finished_at, created_at)
                VALUES (:id, :code, :oid, 'finishing', 2, 'cm', 90000, 41000, 0,
                    :mid, 'running', :start, NULL, :now)
            """), {
                "id": fn_jid, "code": "ORD-102-FIN",
                "oid": str(ord102[0]), "mid": str(fn[0]),
                "start": _ts(7), "now": _ts(8, day_offset=-1),
            })
            db.execute(text("""
                UPDATE machines SET status='running', current_job_id=:jid,
                    status_changed_at=:ts WHERE id=:mid
            """), {"mid": str(fn[0]), "jid": fn_jid, "ts": _ts(7)})
            patched.append("FN-01: inserted ORD-102-FIN finishing job")
        else:
            # Job exists but machine may not have current_job_id set
            db.execute(text("""
                UPDATE machines SET current_job_id=:jid, status_changed_at=COALESCE(status_changed_at, :ts)
                WHERE id=:mid AND (current_job_id IS NULL)
            """), {"mid": str(fn[0]), "jid": str(existing[0]), "ts": _ts(7)})
            patched.append("FN-01: linked existing ORD-102-FIN to machine")

    # For all other running machines missing current_job_id, link their latest running job
    orphan_machines = db.execute(text("""
        SELECT m.id, m.code,
               (SELECT j.id FROM jobs j WHERE j.machine_id = m.id AND j.status = 'running'
                ORDER BY j.started_at DESC LIMIT 1) AS latest_job_id
        FROM machines m
        WHERE m.status = 'running' AND m.current_job_id IS NULL
    """)).fetchall()
    for m_row in orphan_machines:
        if m_row.latest_job_id:
            db.execute(text("""
                UPDATE machines SET current_job_id=:jid WHERE id=:mid
            """), {"mid": str(m_row.id), "jid": str(m_row.latest_job_id)})
            patched.append(f"{m_row.code}: linked current_job_id to running job")

    db.commit()
    return {"status": "patched", "changes": patched if patched else ["no changes needed"]}


@router.post("/demo/reset")
def demo_reset(
    user=Depends(require_permission("demo.reset")),
    db=Depends(get_db),
):
    """
    Reset the mill to demo state D 11:00.
    Clears scenario-specific data and re-seeds via scenario_demo.run().
    """
    # Delete in FK-safe order (children before parents)
    for tbl in [
        "ripple_fixes",
        "ripple_snapshots",
        "ripple_events",
        "leak_entries",
        "machine_events",
        "job_operator_sessions",
        "job_progress_logs",
        "job_material_consumption",
        "wip_lots",
        "jobs",
        "inspection_defects",
        "inspections",
        "rolls",
        "dispatch_items",
        "dispatches",
        "invoice_lines",
        "invoices",
        "payment_allocations",
        "payments_received",
        "stock_reservations",
        "stock_movements",
        "yarn_batches",
        "order_status_history",
        "orders",
        "attendance",
        "domain_events",
    ]:
        db.execute(text(f"DELETE FROM {tbl}"))

    # Reset all machines to idle
    db.execute(text("""
        UPDATE machines SET status = 'idle', current_job_id = NULL,
            status_changed_at = NOW(), updated_at = NOW()
    """))
    db.commit()

    # Re-run scenario seed
    from app.seed import scenario_demo
    scenario_demo.run(db)
    db.commit()

    return {"status": "reset", "message": "Mill reset to demo state D 11:00"}


@router.post("/demo/seed-rolls")
def demo_seed_rolls(
    user=Depends(require_permission("demo.reset")),
    db=Depends(get_db),
):
    """
    Create 3 pending-QC rolls from the FN-01 finishing job so the QC inspector
    has something to inspect in the demo.
    """
    from app.core.time import now as app_now

    fn_job = db.execute(text("SELECT id, order_id FROM jobs WHERE code='ORD-102-FIN'")).fetchone()
    if not fn_job:
        return {"status": "skipped", "reason": "ORD-102-FIN job not found — run /demo/patch-jobs first"}

    now = app_now()
    created = []
    for i, length_cm in enumerate([5000, 4800, 5200]):
        roll_id = str(uuid.uuid4())
        code = f"ROL-DEMO-{i+1:02d}"
        # skip if already exists
        existing = db.execute(text("SELECT id FROM rolls WHERE code = :code"), {"code": code}).fetchone()
        if existing:
            created.append(f"{code} (already exists)")
            continue
        db.execute(text("""
            INSERT INTO rolls (id, code, order_id, finishing_job_id, length_cm, status, created_at)
            VALUES (:id, :code, :oid, :jid, :lcm, 'pending_qc', :now)
        """), {
            "id": roll_id, "code": code,
            "oid": str(fn_job[1]),
            "jid": str(fn_job[0]),
            "lcm": length_cm, "now": now,
        })
        created.append(code)

    db.commit()
    return {"status": "seeded", "rolls": created}
