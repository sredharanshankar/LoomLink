"""A-M7: Payroll service — wage advances, compute payroll, approve, mark paid, payslip PDF."""
from __future__ import annotations
import uuid
import datetime as dt
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.errors import AppError
from app.core import time as app_time
from app.core import events as ev
from app.core.audit import audit


def _actor(user: dict) -> uuid.UUID | None:
    raw = user.get("sub") or user.get("id")
    return uuid.UUID(str(raw)) if raw else None


# ---------------------------------------------------------------------------
# wage advances
# ---------------------------------------------------------------------------

def list_wage_advances(
    session: Session, worker_id: uuid.UUID | None = None
) -> list[dict]:
    params: dict = {}
    where = ""
    if worker_id:
        where = "WHERE wa.worker_id = :wid"
        params["wid"] = worker_id

    rows = session.execute(text(f"""
        SELECT wa.id, wa.worker_id, w.name AS worker_name,
               wa.amount_paise, wa.date, wa.note, wa.recovered_in_run_id, wa.created_at
        FROM wage_advances wa
        JOIN workers w ON w.id = wa.worker_id
        {where}
        ORDER BY wa.date DESC
    """), params).fetchall()

    return [
        {
            "id": str(r.id), "worker_id": str(r.worker_id), "worker_name": r.worker_name,
            "amount_paise": r.amount_paise, "date": r.date.isoformat(),
            "note": r.note,
            "recovered_in_run_id": str(r.recovered_in_run_id) if r.recovered_in_run_id else None,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


def create_wage_advance(session: Session, body: dict, user: dict) -> dict:
    from app.models.workforce import WageAdvance

    actor_id = _actor(user)
    worker_id = uuid.UUID(str(body["worker_id"]))
    amount_paise = int(body["amount_paise"])

    if amount_paise <= 0:
        raise AppError("VALIDATION_ERROR", "amount_paise must be positive")

    if not session.execute(
        text("SELECT id FROM workers WHERE id = :wid AND is_active = true"),
        {"wid": worker_id},
    ).fetchone():
        raise AppError("NOT_FOUND", "Worker not found or inactive")

    now = app_time.now()
    wa = WageAdvance(
        id=uuid.uuid4(),
        worker_id=worker_id,
        amount_paise=amount_paise,
        date=dt.date.fromisoformat(body["date"]) if body.get("date") else app_time.today_local(),
        note=body.get("note"),
        created_at=now,
    )
    session.add(wa)
    session.flush()

    audit(session, actor_id, "wage_advance", "worker", str(worker_id),
          before=None, after={"amount_paise": amount_paise})

    return {
        "id": str(wa.id), "worker_id": str(wa.worker_id),
        "amount_paise": wa.amount_paise, "date": wa.date.isoformat(),
        "note": wa.note, "created_at": wa.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# payroll run lifecycle
# ---------------------------------------------------------------------------

def list_payroll_runs(session: Session) -> list[dict]:
    rows = session.execute(text("""
        SELECT pr.id, pr.period, pr.status, pr.computed_at, pr.approved_at, pr.created_at,
               COUNT(pl.id) AS line_count,
               COALESCE(SUM(pl.net_paise), 0) AS total_net_paise
        FROM payroll_runs pr
        LEFT JOIN payroll_lines pl ON pl.run_id = pr.id
        GROUP BY pr.id
        ORDER BY pr.period DESC
    """)).fetchall()

    return [
        {
            "id": str(r.id), "period": r.period, "status": r.status,
            "line_count": r.line_count, "total_net_paise": int(r.total_net_paise),
            "computed_at": r.computed_at.isoformat() if r.computed_at else None,
            "approved_at": r.approved_at.isoformat() if r.approved_at else None,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


def get_payroll_run(session: Session, run_id: uuid.UUID) -> dict:
    from app.models.workforce import PayrollRun

    run = session.get(PayrollRun, run_id)
    if run is None:
        raise AppError("NOT_FOUND", f"Payroll run {run_id} not found")

    lines = session.execute(text("""
        SELECT pl.id, pl.worker_id, w.name AS worker_name, w.code AS worker_code,
               pl.days_present, pl.hours_minutes, pl.overtime_minutes,
               pl.piece_cm, pl.gross_paise, pl.deductions_paise, pl.net_paise, pl.paid_at
        FROM payroll_lines pl
        JOIN workers w ON w.id = pl.worker_id
        WHERE pl.run_id = :rid
        ORDER BY w.name
    """), {"rid": run_id}).fetchall()

    return {
        "id": str(run.id), "period": run.period, "status": run.status,
        "computed_at": run.computed_at.isoformat() if run.computed_at else None,
        "approved_at": run.approved_at.isoformat() if run.approved_at else None,
        "created_at": run.created_at.isoformat(),
        "lines": [
            {
                "id": str(l.id), "worker_id": str(l.worker_id),
                "worker_name": l.worker_name, "worker_code": l.worker_code,
                "days_present": l.days_present, "hours_minutes": l.hours_minutes,
                "overtime_minutes": l.overtime_minutes, "piece_cm": l.piece_cm,
                "gross_paise": l.gross_paise, "deductions_paise": l.deductions_paise,
                "net_paise": l.net_paise,
                "paid_at": l.paid_at.isoformat() if l.paid_at else None,
            }
            for l in lines
        ],
    }


def compute_payroll_draft(session: Session, body: dict, user: dict) -> dict:
    """Compute or recompute a payroll run for a given period (YYYY-MM)."""
    from app.models.workforce import PayrollRun, PayrollLine

    actor_id = _actor(user)
    period = body["period"]
    try:
        year_s, month_s = period.split("-")
        year, month = int(year_s), int(month_s)
        dt.date(year, month, 1)
    except (ValueError, AttributeError):
        raise AppError("VALIDATION_ERROR", "period must be YYYY-MM")

    period_start = dt.date(year, month, 1)
    if month == 12:
        period_end = dt.date(year + 1, 1, 1) - dt.timedelta(days=1)
    else:
        period_end = dt.date(year, month + 1, 1) - dt.timedelta(days=1)

    existing_run = session.execute(
        text("SELECT id, status FROM payroll_runs WHERE period = :p"), {"p": period}
    ).fetchone()

    now = app_time.now()
    if existing_run:
        if existing_run.status in ("approved", "paid"):
            raise AppError("INVALID_STATE", f"Payroll for {period} is already {existing_run.status}")
        run_id = existing_run.id
        session.execute(text("""
            UPDATE payroll_runs SET status = 'draft', computed_at = :now, updated_at = :now
            WHERE id = :rid
        """), {"now": now, "rid": run_id})
        session.execute(text("DELETE FROM payroll_lines WHERE run_id = :rid"), {"rid": run_id})
    else:
        run = PayrollRun(
            id=uuid.uuid4(), period=period, status="draft",
            computed_at=now, created_at=now, updated_at=now,
        )
        session.add(run)
        session.flush()
        run_id = run.id

    workers = session.execute(text("""
        SELECT w.id, w.name, w.code, w.wage_type, w.wage_rate_paise, w.piece_rate_paise_per_m
        FROM workers w WHERE w.is_active = true
    """)).fetchall()

    advances_by_worker: dict[str, int] = {}
    for a in session.execute(text("""
        SELECT worker_id, COALESCE(SUM(amount_paise), 0) AS total
        FROM wage_advances
        WHERE recovered_in_run_id IS NULL AND date <= :period_end
        GROUP BY worker_id
    """), {"period_end": period_end}).fetchall():
        advances_by_worker[str(a.worker_id)] = int(a.total)

    settings_row = session.execute(
        text("SELECT overtime_rate_bp FROM mill_settings LIMIT 1")
    ).fetchone()
    overtime_rate_bp = settings_row.overtime_rate_bp if settings_row else 15000

    working_days_in_period = (period_end - period_start).days + 1

    for w in workers:
        att_rows = session.execute(text("""
            SELECT status, overtime_minutes, check_in_at, check_out_at
            FROM attendance
            WHERE worker_id = :wid AND date >= :from AND date <= :to
              AND status IN ('present', 'late', 'half_day')
        """), {"wid": w.id, "from": period_start, "to": period_end}).fetchall()

        days_present = sum(1 for a in att_rows if a.status in ("present", "late"))
        half_days = sum(1 for a in att_rows if a.status == "half_day")
        total_minutes = sum(
            int((a.check_out_at - a.check_in_at).total_seconds() // 60)
            for a in att_rows if a.check_in_at and a.check_out_at
        )
        total_overtime_minutes = sum(a.overtime_minutes or 0 for a in att_rows)

        piece_cm = 0
        if w.wage_type == "piece":
            p_row = session.execute(text("""
                SELECT COALESCE(SUM(jp.qty_produced_cm), 0) AS total_cm
                FROM job_progress jp
                WHERE jp.operator_id = :wid
                  AND jp.recorded_at >= :from_dt AND jp.recorded_at <= :to_dt
            """), {
                "wid": w.id,
                "from_dt": dt.datetime.combine(period_start, dt.time.min).replace(tzinfo=dt.timezone.utc),
                "to_dt": dt.datetime.combine(period_end, dt.time.max).replace(tzinfo=dt.timezone.utc),
            }).fetchone()
            piece_cm = int(p_row.total_cm) if p_row else 0

        if w.wage_type == "daily":
            gross_paise = (days_present + half_days // 2) * int(w.wage_rate_paise)
        elif w.wage_type == "monthly":
            gross_paise = int(w.wage_rate_paise) * (days_present + half_days // 2) // max(working_days_in_period, 1)
        elif w.wage_type == "piece":
            gross_paise = int(w.piece_rate_paise_per_m or 0) * piece_cm // 100
        else:
            gross_paise = 0

        if total_overtime_minutes > 0 and w.wage_type in ("daily", "monthly"):
            if w.wage_type == "daily":
                base_hourly_paise = int(w.wage_rate_paise) // 8
            else:
                base_hourly_paise = int(w.wage_rate_paise) // (working_days_in_period * 8)
            ot_paise = base_hourly_paise * total_overtime_minutes * overtime_rate_bp // (60 * 10000)
            gross_paise += ot_paise

        deductions_paise = advances_by_worker.get(str(w.id), 0)
        net_paise = max(0, gross_paise - deductions_paise)

        pl = PayrollLine(
            id=uuid.uuid4(), run_id=run_id, worker_id=w.id,
            days_present=days_present + half_days // 2,
            hours_minutes=total_minutes, overtime_minutes=total_overtime_minutes,
            piece_cm=piece_cm, gross_paise=gross_paise,
            deductions_paise=deductions_paise, net_paise=net_paise,
            created_at=now,
        )
        session.add(pl)

    session.flush()

    ev.publish(session, "payroll.computed", {
        "run_id": str(run_id), "period": period, "worker_count": len(workers)
    }, actor_id=actor_id)

    return get_payroll_run(session, run_id)


def approve_payroll(session: Session, run_id: uuid.UUID, user: dict) -> dict:
    from app.models.workforce import PayrollRun

    actor_id = _actor(user)
    run = session.get(PayrollRun, run_id)
    if run is None:
        raise AppError("NOT_FOUND", f"Payroll run {run_id} not found")
    if run.status != "draft":
        raise AppError("INVALID_STATE", f"Run is {run.status}, not draft")

    now = app_time.now()
    run.status = "approved"
    run.approved_by = actor_id
    run.approved_at = now
    run.updated_at = now

    audit(session, actor_id, "approve_payroll", "payroll_run", str(run_id),
          before={"status": "draft"}, after={"status": "approved"})
    ev.publish(session, "payroll.approved", {"run_id": str(run_id), "period": run.period},
               actor_id=actor_id)

    return get_payroll_run(session, run_id)


def mark_paid(session: Session, run_id: uuid.UUID, user: dict) -> dict:
    from app.models.workforce import PayrollRun

    actor_id = _actor(user)
    run = session.get(PayrollRun, run_id)
    if run is None:
        raise AppError("NOT_FOUND", f"Payroll run {run_id} not found")
    if run.status != "approved":
        raise AppError("INVALID_STATE", f"Run is {run.status}, not approved")

    now = app_time.now()
    run.status = "paid"
    run.updated_at = now

    session.execute(text("""
        UPDATE payroll_lines SET paid_at = :now WHERE run_id = :rid AND paid_at IS NULL
    """), {"now": now, "rid": run_id})

    # Recover outstanding advances for workers in this run
    session.execute(text("""
        UPDATE wage_advances SET recovered_in_run_id = :rid
        WHERE worker_id IN (SELECT worker_id FROM payroll_lines WHERE run_id = :rid)
          AND recovered_in_run_id IS NULL
          AND date <= (
              SELECT (CONCAT(period, '-01'))::date + INTERVAL '1 month' - INTERVAL '1 day'
              FROM payroll_runs WHERE id = :rid
          )
    """), {"rid": run_id})

    audit(session, actor_id, "mark_paid", "payroll_run", str(run_id),
          before={"status": "approved"}, after={"status": "paid"})
    ev.publish(session, "payroll.paid", {"run_id": str(run_id), "period": run.period},
               actor_id=actor_id)

    return get_payroll_run(session, run_id)


def get_payslip_data(session: Session, run_id: uuid.UUID, worker_id: uuid.UUID) -> dict:
    from app.models.workforce import PayrollRun

    run = session.get(PayrollRun, run_id)
    if run is None:
        raise AppError("NOT_FOUND", f"Payroll run {run_id} not found")

    line = session.execute(text("""
        SELECT pl.id, w.name, w.code, w.department,
               pl.days_present, pl.hours_minutes, pl.overtime_minutes,
               pl.piece_cm, pl.gross_paise, pl.deductions_paise, pl.net_paise, pl.paid_at
        FROM payroll_lines pl
        JOIN workers w ON w.id = pl.worker_id
        WHERE pl.run_id = :rid AND pl.worker_id = :wid
    """), {"rid": run_id, "wid": worker_id}).fetchone()
    if line is None:
        raise AppError("NOT_FOUND", "Payslip not found for this worker in this run")

    mill_row = session.execute(
        text("SELECT name, address_line1, gstin FROM mill_settings LIMIT 1")
    ).fetchone()

    advances = session.execute(text("""
        SELECT amount_paise, date, note FROM wage_advances
        WHERE worker_id = :wid AND recovered_in_run_id = :rid
        ORDER BY date
    """), {"wid": worker_id, "rid": run_id}).fetchall()

    return {
        "period": run.period,
        "mill_name": mill_row.name if mill_row else "Mill",
        "mill_address": mill_row.address_line1 if mill_row else "",
        "mill_gstin": mill_row.gstin if mill_row else "",
        "worker_name": line.name,
        "worker_code": line.code,
        "worker_department": line.department,
        "days_present": line.days_present,
        "hours_minutes": line.hours_minutes,
        "overtime_minutes": line.overtime_minutes,
        "piece_cm": line.piece_cm,
        "gross_paise": line.gross_paise,
        "advances": [
            {"amount_paise": a.amount_paise, "date": a.date.isoformat(), "note": a.note}
            for a in advances
        ],
        "deductions_paise": line.deductions_paise,
        "net_paise": line.net_paise,
        "paid_at": line.paid_at.isoformat() if line.paid_at else None,
    }
