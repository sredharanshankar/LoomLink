"""A-M7: Attendance management service — shift assignments, check-in/out, corrections."""
from __future__ import annotations
import datetime as dt
import uuid
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
# shift assignments
# ---------------------------------------------------------------------------

def create_shift_assignment(session: Session, body: dict, user: dict) -> dict:
    from app.models.workforce import ShiftAssignment

    actor_id = _actor(user)
    worker_id = uuid.UUID(str(body["worker_id"]))
    shift_code = body["shift_code"]
    date_obj = dt.date.fromisoformat(body["date"])

    if not session.execute(
        text("SELECT id FROM workers WHERE id = :wid AND is_active = true"),
        {"wid": worker_id},
    ).fetchone():
        raise AppError("NOT_FOUND", "Worker not found or inactive")

    if not session.execute(
        text("SELECT code FROM shifts WHERE code = :sc"), {"sc": shift_code}
    ).fetchone():
        raise AppError("NOT_FOUND", f"Shift {shift_code} not found")

    existing = session.execute(text("""
        SELECT id FROM shift_assignments
        WHERE worker_id = :wid AND date = :date
    """), {"wid": worker_id, "date": date_obj}).fetchone()
    if existing:
        raise AppError("CONFLICT", "Shift already assigned for this date")

    machine_id = None
    if body.get("machine_id"):
        machine_id = uuid.UUID(str(body["machine_id"]))

    now = app_time.now()
    sa = ShiftAssignment(
        id=uuid.uuid4(),
        worker_id=worker_id,
        shift_code=shift_code,
        date=date_obj,
        machine_id=machine_id,
        is_overtime=bool(body.get("is_overtime", False)),
        approved_by=actor_id,
        created_at=now,
    )
    session.add(sa)
    session.flush()

    return {
        "id": str(sa.id),
        "worker_id": str(sa.worker_id),
        "shift_code": sa.shift_code,
        "date": sa.date.isoformat(),
        "machine_id": str(sa.machine_id) if sa.machine_id else None,
        "is_overtime": sa.is_overtime,
        "created_at": sa.created_at.isoformat(),
    }


def list_shift_assignments(
    session: Session, filters: dict | None = None
) -> tuple[list[dict], int]:
    filters = filters or {}
    page = int(filters.get("page", 1))
    size = int(filters.get("size", 50))
    offset = (page - 1) * size

    where_clauses: list[str] = []
    params: dict = {}
    if filters.get("worker_id"):
        where_clauses.append("sa.worker_id = :worker_id")
        params["worker_id"] = str(filters["worker_id"])
    if filters.get("date"):
        where_clauses.append("sa.date = :date")
        params["date"] = filters["date"]
    if filters.get("shift_code"):
        where_clauses.append("sa.shift_code = :shift_code")
        params["shift_code"] = filters["shift_code"]

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    total = session.execute(
        text(f"SELECT COUNT(*) FROM shift_assignments sa {where_sql}"), params
    ).scalar() or 0

    rows = session.execute(text(f"""
        SELECT sa.id, sa.worker_id, w.name AS worker_name, sa.shift_code,
               sa.date, sa.machine_id, sa.is_overtime, sa.created_at
        FROM shift_assignments sa
        JOIN workers w ON w.id = sa.worker_id
        {where_sql}
        ORDER BY sa.date DESC, w.name
        LIMIT :limit OFFSET :offset
    """), {**params, "limit": size, "offset": offset}).fetchall()

    items = [
        {
            "id": str(r.id), "worker_id": str(r.worker_id), "worker_name": r.worker_name,
            "shift_code": r.shift_code, "date": r.date.isoformat(),
            "machine_id": str(r.machine_id) if r.machine_id else None,
            "is_overtime": r.is_overtime, "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
    return items, int(total)


# ---------------------------------------------------------------------------
# check-in / check-out
# ---------------------------------------------------------------------------

def check_in(session: Session, body: dict, user: dict) -> dict:
    from app.models.workforce import Attendance

    actor_id = _actor(user)
    worker_id = uuid.UUID(str(body["worker_id"]))
    now = app_time.now()
    today = app_time.today_local()

    assignment = session.execute(text("""
        SELECT shift_code FROM shift_assignments
        WHERE worker_id = :wid AND date = :date LIMIT 1
    """), {"wid": worker_id, "date": today}).fetchone()

    if assignment:
        shift_code = assignment.shift_code
    else:
        default_row = session.execute(
            text("SELECT default_shift FROM workers WHERE id = :wid"),
            {"wid": worker_id},
        ).fetchone()
        if default_row is None:
            raise AppError("NOT_FOUND", "Worker not found")
        shift_code = default_row.default_shift

    existing = session.execute(text("""
        SELECT id, status FROM attendance
        WHERE worker_id = :wid AND date = :date AND shift_code = :sc
    """), {"wid": worker_id, "date": today, "sc": shift_code}).fetchone()

    if existing:
        if existing.status in ("present", "late"):
            raise AppError("CONFLICT", "Already checked in for this shift")
        session.execute(text("""
            UPDATE attendance
            SET check_in_at = :now, status = 'present', updated_at = :now
            WHERE id = :aid
        """), {"now": now, "aid": existing.id})
        attendance_id = existing.id
    else:
        shift_row = session.execute(
            text("SELECT start_time FROM shifts WHERE code = :sc"), {"sc": shift_code}
        ).fetchone()
        status = "present"
        if shift_row:
            scheduled_dt = dt.datetime.combine(today, shift_row.start_time).replace(
                tzinfo=dt.timezone.utc
            )
            if now > scheduled_dt + dt.timedelta(minutes=10):
                status = "late"

        att = Attendance(
            id=uuid.uuid4(),
            worker_id=worker_id,
            date=today,
            shift_code=shift_code,
            check_in_at=now,
            status=status,
            source=body.get("source", "app"),
            created_at=now,
        )
        session.add(att)
        session.flush()
        attendance_id = att.id

    ev.publish(session, "attendance.check_in", {
        "worker_id": str(worker_id), "date": today.isoformat(), "shift": shift_code,
    }, actor_id=actor_id)

    return _get_attendance_row(session, attendance_id)


def check_out(session: Session, body: dict, user: dict) -> dict:
    actor_id = _actor(user)
    worker_id = uuid.UUID(str(body["worker_id"]))
    now = app_time.now()
    today = app_time.today_local()

    att_row = session.execute(text("""
        SELECT a.id, a.shift_code, a.check_in_at
        FROM attendance a
        WHERE a.worker_id = :wid AND a.date = :date
          AND a.check_in_at IS NOT NULL AND a.check_out_at IS NULL
        ORDER BY a.check_in_at DESC LIMIT 1
    """), {"wid": worker_id, "date": today}).fetchone()
    if att_row is None:
        raise AppError("NOT_FOUND", "No open check-in found for today")

    shift_row = session.execute(text("""
        SELECT end_time FROM shifts WHERE code = :sc
    """), {"sc": att_row.shift_code}).fetchone()

    overtime_minutes = 0
    if shift_row:
        scheduled_end = dt.datetime.combine(today, shift_row.end_time).replace(
            tzinfo=dt.timezone.utc
        )
        if now > scheduled_end:
            overtime_minutes = int((now - scheduled_end).total_seconds() // 60)

    session.execute(text("""
        UPDATE attendance
        SET check_out_at = :now, overtime_minutes = :ot, updated_at = :now
        WHERE id = :aid
    """), {"now": now, "ot": overtime_minutes, "aid": att_row.id})

    ev.publish(session, "attendance.check_out", {
        "worker_id": str(worker_id), "date": today.isoformat(),
        "overtime_minutes": overtime_minutes,
    }, actor_id=actor_id)

    return _get_attendance_row(session, att_row.id)


def _get_attendance_row(session: Session, attendance_id: uuid.UUID) -> dict:
    row = session.execute(text("""
        SELECT a.id, a.worker_id, w.name AS worker_name,
               a.date, a.shift_code, a.check_in_at, a.check_out_at,
               a.status, a.overtime_minutes, a.source
        FROM attendance a
        JOIN workers w ON w.id = a.worker_id
        WHERE a.id = :aid
    """), {"aid": attendance_id}).fetchone()
    if row is None:
        raise AppError("NOT_FOUND", "Attendance record not found")
    return {
        "id": str(row.id), "worker_id": str(row.worker_id), "worker_name": row.worker_name,
        "date": row.date.isoformat(), "shift_code": row.shift_code,
        "check_in_at": row.check_in_at.isoformat() if row.check_in_at else None,
        "check_out_at": row.check_out_at.isoformat() if row.check_out_at else None,
        "status": row.status, "overtime_minutes": row.overtime_minutes, "source": row.source,
    }


# ---------------------------------------------------------------------------
# list attendance
# ---------------------------------------------------------------------------

def list_attendance(
    session: Session, filters: dict | None = None
) -> tuple[list[dict], int]:
    filters = filters or {}
    page = int(filters.get("page", 1))
    size = int(filters.get("size", 50))
    offset = (page - 1) * size

    where_clauses: list[str] = []
    params: dict = {}
    if filters.get("worker_id"):
        where_clauses.append("a.worker_id = :worker_id")
        params["worker_id"] = str(filters["worker_id"])
    if filters.get("date_from"):
        where_clauses.append("a.date >= :date_from")
        params["date_from"] = filters["date_from"]
    if filters.get("date_to"):
        where_clauses.append("a.date <= :date_to")
        params["date_to"] = filters["date_to"]
    if filters.get("status"):
        where_clauses.append("a.status = :status")
        params["status"] = filters["status"]

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    total = session.execute(
        text(f"SELECT COUNT(*) FROM attendance a {where_sql}"), params
    ).scalar() or 0

    rows = session.execute(text(f"""
        SELECT a.id, a.worker_id, w.name AS worker_name,
               a.date, a.shift_code, a.check_in_at, a.check_out_at,
               a.status, a.overtime_minutes, a.source
        FROM attendance a
        JOIN workers w ON w.id = a.worker_id
        {where_sql}
        ORDER BY a.date DESC, w.name
        LIMIT :limit OFFSET :offset
    """), {**params, "limit": size, "offset": offset}).fetchall()

    items = [
        {
            "id": str(r.id), "worker_id": str(r.worker_id), "worker_name": r.worker_name,
            "date": r.date.isoformat(), "shift_code": r.shift_code,
            "check_in_at": r.check_in_at.isoformat() if r.check_in_at else None,
            "check_out_at": r.check_out_at.isoformat() if r.check_out_at else None,
            "status": r.status, "overtime_minutes": r.overtime_minutes, "source": r.source,
        }
        for r in rows
    ]
    return items, int(total)


# ---------------------------------------------------------------------------
# correct attendance (admin / manager only)
# ---------------------------------------------------------------------------

def correct_attendance(
    session: Session, attendance_id: uuid.UUID, body: dict, user: dict
) -> dict:
    from app.models.workforce import Attendance

    actor_id = _actor(user)
    att = session.get(Attendance, attendance_id)
    if att is None:
        raise AppError("NOT_FOUND", "Attendance record not found")

    before = {
        "check_in_at": att.check_in_at.isoformat() if att.check_in_at else None,
        "check_out_at": att.check_out_at.isoformat() if att.check_out_at else None,
        "status": att.status,
    }
    now = app_time.now()

    if body.get("check_in_at"):
        att.check_in_at = dt.datetime.fromisoformat(body["check_in_at"])
    if body.get("check_out_at"):
        att.check_out_at = dt.datetime.fromisoformat(body["check_out_at"])
    if body.get("status"):
        att.status = body["status"]
    if body.get("overtime_minutes") is not None:
        att.overtime_minutes = int(body["overtime_minutes"])

    att.corrected_by = actor_id
    att.correction_reason = body.get("reason")
    att.source = "corrected"
    att.updated_at = now

    after = {
        "check_in_at": att.check_in_at.isoformat() if att.check_in_at else None,
        "check_out_at": att.check_out_at.isoformat() if att.check_out_at else None,
        "status": att.status,
    }

    audit(session, actor_id, "correct_attendance", "attendance", str(attendance_id),
          before=before, after=after)

    return _get_attendance_row(session, attendance_id)


# ---------------------------------------------------------------------------
# is_worker_on_shift helper (used by production service / interfaces)
# ---------------------------------------------------------------------------

def is_worker_on_shift(session: Session, worker_id: uuid.UUID) -> bool:
    """True if worker has an open check-in today with no check-out."""
    today = app_time.today_local()
    row = session.execute(text("""
        SELECT id FROM attendance
        WHERE worker_id = :wid AND date = :date
          AND check_in_at IS NOT NULL AND check_out_at IS NULL
          AND status IN ('present', 'late')
    """), {"wid": worker_id, "date": today}).fetchone()
    return row is not None
