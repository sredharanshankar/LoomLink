"""A-M4: Production management service."""
from __future__ import annotations

import uuid
import datetime as dt
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.ids import next_code
from app.core import time as app_time
from app.core import events as ev
from app.core.audit import audit


def _actor(user: dict) -> uuid.UUID | None:
    raw = user.get("sub") or user.get("id")
    return uuid.UUID(str(raw)) if raw else None


def _get_job(session: Session, job_id: uuid.UUID):
    from app.models.production import Job
    job = session.get(Job, job_id)
    if job is None:
        raise AppError("NOT_FOUND", f"Job {job_id} not found")
    return job


def _get_machine(session: Session, machine_id: uuid.UUID):
    from app.models.production import Machine
    machine = session.get(Machine, machine_id)
    if machine is None:
        raise AppError("NOT_FOUND", f"Machine {machine_id} not found")
    return machine


# ---------------------------------------------------------------------------
# assign job
# ---------------------------------------------------------------------------

def assign_job(session: Session, job_id: uuid.UUID, body: dict, user: dict) -> dict:
    from app.models.production import Job, Machine, MachineCapability

    actor_id = _actor(user)
    machine_id = uuid.UUID(str(body["machine_id"]))

    job = _get_job(session, job_id)
    machine = _get_machine(session, machine_id)

    if machine.status == "offline":
        raise AppError("INVALID_STATE", "Machine is offline")
    if machine.stage != job.stage:
        raise AppError("MACHINE_INCOMPATIBLE",
                       f"Machine stage {machine.stage} != job stage {job.stage}")

    # Check capability if machine has capability restrictions
    caps = session.execute(text(
        "SELECT fabric_type_id FROM machine_capabilities WHERE machine_id = :mid"
    ), {"mid": machine_id}).fetchall()

    if caps:
        # Get fabric_type_id from order
        order_row = session.execute(text(
            "SELECT fabric_type_id FROM orders WHERE id = :oid"
        ), {"oid": job.order_id}).fetchone()
        if order_row:
            cap_ids = {str(c.fabric_type_id) for c in caps}
            if str(order_row.fabric_type_id) not in cap_ids:
                raise AppError("MACHINE_INCOMPATIBLE",
                               "Machine cannot handle this fabric type")

    job.machine_id = machine_id
    queue_pos = body.get("queue_position")
    if queue_pos is not None:
        job.queue_position = int(queue_pos)
    job.updated_at = app_time.now()

    ev.publish(session, "job.assigned", {
        "job_id": str(job_id),
        "machine_id": str(machine_id),
    }, actor_id=actor_id)

    return _job_out(job)


# ---------------------------------------------------------------------------
# reorder queue
# ---------------------------------------------------------------------------

def reorder_queue(session: Session, machine_id: uuid.UUID, job_ids: list[uuid.UUID], user: dict) -> dict:
    actor_id = _actor(user)
    now = app_time.now()
    for pos, jid in enumerate(job_ids, start=1):
        session.execute(text(
            "UPDATE jobs SET queue_position = :pos, updated_at = :now WHERE id = :id AND machine_id = :mid"
        ), {"pos": pos, "id": jid, "mid": machine_id, "now": now})

    ev.publish(session, "job.reordered", {
        "machine_id": str(machine_id),
        "job_ids": [str(j) for j in job_ids],
    }, actor_id=actor_id)

    return {"machine_id": str(machine_id), "reordered": len(job_ids)}


# ---------------------------------------------------------------------------
# split job
# ---------------------------------------------------------------------------

def split_job(session: Session, job_id: uuid.UUID, body: dict, user: dict) -> list[dict]:
    from app.models.production import Job

    actor_id = _actor(user)
    job = _get_job(session, job_id)
    parts_qty: list[int] = [int(q) for q in body["parts_qty"]]

    if sum(parts_qty) > job.planned_qty:
        raise AppError("VALIDATION_ERROR", "Sum of parts exceeds planned_qty")

    order_num = int(session.execute(
        text("SELECT code FROM orders WHERE id = :oid"), {"oid": job.order_id}
    ).scalar().split("-")[-1])

    now = app_time.now()
    new_jobs = []
    for qty in parts_qty:
        code = next_code(session, "job", order_no=order_num)
        child = Job(
            id=uuid.uuid4(),
            code=code,
            order_id=job.order_id,
            stage=job.stage,
            seq=job.seq,
            unit=job.unit,
            planned_qty=qty,
            produced_qty=0,
            waste_qty=0,
            machine_id=job.machine_id,
            status="planned",
            split_from_job_id=job_id,
            created_at=now,
        )
        session.add(child)
        new_jobs.append(child)

    # Reduce original job's planned_qty
    job.planned_qty -= sum(parts_qty)
    job.updated_at = now

    session.flush()

    ev.publish(session, "job.split", {
        "parent_job_id": str(job_id),
        "new_job_ids": [str(j.id) for j in new_jobs],
    }, actor_id=actor_id)

    return [_job_out(j) for j in new_jobs]


# ---------------------------------------------------------------------------
# start job
# ---------------------------------------------------------------------------

def start_job(session: Session, job_id: uuid.UUID, body: dict, user: dict) -> dict:
    from app.models.production import Job, Machine, JobOperatorSession
    from app.services.attendance import is_worker_on_shift

    actor_id = _actor(user)
    job = _get_job(session, job_id)

    if job.status not in ("planned", "ready", "paused"):
        raise AppError("INVALID_STATE", f"Cannot start job in status {job.status}")

    if job.machine_id is None:
        raise AppError("INVALID_STATE", "Job has no machine assigned")

    machine = _get_machine(session, job.machine_id)
    if machine.status not in ("idle", "changeover"):
        raise AppError("MACHINE_BUSY", f"Machine status: {machine.status}")

    worker_id = uuid.UUID(str(body["worker_id"])) if body.get("worker_id") else None
    if worker_id:
        if not is_worker_on_shift(session, worker_id, app_time.now()):
            raise AppError("NOT_ON_SHIFT", "Worker is not on shift")

    now = app_time.now()
    job.status = "running"
    job.started_at = now
    job.updated_at = now
    if worker_id:
        job.current_operator_id = worker_id

    machine.status = "running"
    machine.current_job_id = job_id
    machine.status_changed_at = now
    machine.updated_at = now

    if worker_id:
        op_session = JobOperatorSession(
            id=uuid.uuid4(),
            job_id=job_id,
            worker_id=worker_id,
            started_at=now,
            created_at=now,
        )
        session.add(op_session)

    ev.publish(session, "job.started", {
        "job_id": str(job_id),
        "machine_id": str(job.machine_id),
        "worker_id": str(worker_id) if worker_id else None,
    }, actor_id=actor_id)

    ev.publish(session, "machine.status_changed", {
        "machine_id": str(job.machine_id),
        "status": "running",
    }, actor_id=actor_id)

    # Update order status to in_production
    session.execute(text("""
        UPDATE orders SET status = 'in_production', updated_at = :now
        WHERE id = :oid AND status = 'confirmed'
    """), {"oid": job.order_id, "now": now})

    return _job_out(job)


# ---------------------------------------------------------------------------
# record progress
# ---------------------------------------------------------------------------

def record_progress(session: Session, job_id: uuid.UUID, body: dict, user: dict) -> dict:
    from app.models.production import Job, JobProgressLog

    actor_id = _actor(user)
    idempotency_key = body.get("idempotency_key")

    if idempotency_key:
        existing = session.execute(text(
            "SELECT id FROM job_progress_logs WHERE idempotency_key = :k LIMIT 1"
        ), {"k": idempotency_key}).fetchone()
        if existing:
            job = _get_job(session, job_id)
            return _job_out(job)

    job = _get_job(session, job_id)
    if job.status != "running":
        raise AppError("INVALID_STATE", f"Job is not running, status: {job.status}")

    now = app_time.now()
    worker_id = uuid.UUID(str(body["worker_id"])) if body.get("worker_id") else None

    if "total_qty" in body:
        total_qty = int(body["total_qty"])
        delta_qty = total_qty - job.produced_qty
    elif "delta_qty" in body:
        delta_qty = int(body["delta_qty"])
        total_qty = job.produced_qty + delta_qty
    else:
        raise AppError("VALIDATION_ERROR", "Provide delta_qty or total_qty")

    if delta_qty < 0:
        raise AppError("VALIDATION_ERROR", "Progress delta must be non-negative")

    log = JobProgressLog(
        id=uuid.uuid4(),
        job_id=job_id,
        worker_id=worker_id,
        delta_qty=delta_qty,
        total_qty=total_qty,
        source=body.get("source", "tap"),
        idempotency_key=idempotency_key,
        created_at=now,
    )
    session.add(log)

    job.produced_qty = total_qty
    job.updated_at = now

    ev.publish(session, "job.progress", {
        "job_id": str(job_id),
        "delta_qty": delta_qty,
        "total_qty": total_qty,
    }, actor_id=actor_id)

    return _job_out(job)


# ---------------------------------------------------------------------------
# pause job
# ---------------------------------------------------------------------------

def pause_job(session: Session, job_id: uuid.UUID, body: dict, user: dict) -> dict:
    from app.models.production import Job, Machine, JobOperatorSession

    actor_id = _actor(user)
    job = _get_job(session, job_id)

    if job.status != "running":
        raise AppError("INVALID_STATE", f"Job is not running")

    now = app_time.now()
    job.status = "paused"
    job.updated_at = now

    if job.machine_id:
        machine = _get_machine(session, job.machine_id)
        machine.status = "idle"
        machine.current_job_id = None
        machine.status_changed_at = now
        machine.updated_at = now

    # Close operator session
    session.execute(text("""
        UPDATE job_operator_sessions SET ended_at = :now, end_reason = 'pause'
        WHERE job_id = :jid AND ended_at IS NULL
    """), {"jid": job_id, "now": now})

    ev.publish(session, "job.paused", {"job_id": str(job_id)}, actor_id=actor_id)
    if job.machine_id:
        ev.publish(session, "machine.status_changed", {
            "machine_id": str(job.machine_id), "status": "idle"
        }, actor_id=actor_id)

    return _job_out(job)


# ---------------------------------------------------------------------------
# resume job
# ---------------------------------------------------------------------------

def resume_job(session: Session, job_id: uuid.UUID, body: dict, user: dict) -> dict:
    from app.models.production import Job, Machine, JobOperatorSession
    from app.services.attendance import is_worker_on_shift

    actor_id = _actor(user)
    job = _get_job(session, job_id)

    if job.status != "paused":
        raise AppError("INVALID_STATE", f"Job is not paused")

    worker_id = uuid.UUID(str(body["worker_id"])) if body.get("worker_id") else None
    if worker_id:
        if not is_worker_on_shift(session, worker_id, app_time.now()):
            raise AppError("NOT_ON_SHIFT", "Worker is not on shift")

    now = app_time.now()
    job.status = "running"
    job.updated_at = now
    if worker_id:
        job.current_operator_id = worker_id

    if job.machine_id:
        machine = _get_machine(session, job.machine_id)
        machine.status = "running"
        machine.current_job_id = job_id
        machine.status_changed_at = now
        machine.updated_at = now

    if worker_id:
        op_session = JobOperatorSession(
            id=uuid.uuid4(),
            job_id=job_id,
            worker_id=worker_id,
            started_at=now,
            created_at=now,
        )
        session.add(op_session)

    ev.publish(session, "job.resumed", {
        "job_id": str(job_id),
        "worker_id": str(worker_id) if worker_id else None,
    }, actor_id=actor_id)
    if job.machine_id:
        ev.publish(session, "machine.status_changed", {
            "machine_id": str(job.machine_id), "status": "running"
        }, actor_id=actor_id)

    return _job_out(job)


# ---------------------------------------------------------------------------
# handover
# ---------------------------------------------------------------------------

def handover_job(session: Session, job_id: uuid.UUID, body: dict, user: dict) -> dict:
    from app.models.production import Job, JobOperatorSession

    actor_id = _actor(user)
    job = _get_job(session, job_id)

    if job.status != "running":
        raise AppError("INVALID_STATE", "Job is not running")

    now = app_time.now()

    # Close current session as handover
    session.execute(text("""
        UPDATE job_operator_sessions SET ended_at = :now, end_reason = 'handover'
        WHERE job_id = :jid AND ended_at IS NULL
    """), {"jid": job_id, "now": now})

    to_worker_id = uuid.UUID(str(body["to_worker_id"])) if body.get("to_worker_id") else None
    if to_worker_id:
        op_session = JobOperatorSession(
            id=uuid.uuid4(),
            job_id=job_id,
            worker_id=to_worker_id,
            started_at=now,
            created_at=now,
        )
        session.add(op_session)
        job.current_operator_id = to_worker_id

    job.updated_at = now

    ev.publish(session, "job.handover", {
        "job_id": str(job_id),
        "from_actor_id": str(actor_id) if actor_id else None,
        "to_worker_id": str(to_worker_id) if to_worker_id else None,
    }, actor_id=actor_id)

    return _job_out(job)


def accept_handover(session: Session, job_id: uuid.UUID, user: dict) -> dict:
    from app.models.production import Job

    actor_id = _actor(user)
    job = _get_job(session, job_id)

    # Just publish the accept event
    ev.publish(session, "job.handover", {
        "job_id": str(job_id),
        "accepted_by": str(actor_id) if actor_id else None,
    }, actor_id=actor_id)

    return _job_out(job)


# ---------------------------------------------------------------------------
# finish job
# ---------------------------------------------------------------------------

def finish_job(session: Session, job_id: uuid.UUID, body: dict, user: dict) -> dict:
    from app.models.production import Job, Machine

    actor_id = _actor(user)
    job = _get_job(session, job_id)

    if job.status not in ("running", "paused"):
        raise AppError("INVALID_STATE", f"Cannot finish job in status {job.status}")

    now = app_time.now()
    final_qty = int(body.get("final_qty", job.produced_qty))
    waste_qty = int(body.get("waste_qty", 0))

    job.status = "done"
    job.finished_at = now
    job.produced_qty = final_qty
    job.waste_qty = waste_qty
    job.updated_at = now

    if job.machine_id:
        machine = _get_machine(session, job.machine_id)
        machine.status = "idle"
        machine.current_job_id = None
        machine.status_changed_at = now
        machine.updated_at = now

    # Close operator sessions
    session.execute(text("""
        UPDATE job_operator_sessions SET ended_at = :now, end_reason = 'finish'
        WHERE job_id = :jid AND ended_at IS NULL
    """), {"jid": job_id, "now": now})

    ev.publish(session, "job.finished", {
        "job_id": str(job_id),
        "final_qty": final_qty,
        "waste_qty": waste_qty,
    }, actor_id=actor_id)

    if job.machine_id:
        ev.publish(session, "machine.status_changed", {
            "machine_id": str(job.machine_id), "status": "idle"
        }, actor_id=actor_id)

    # Check if all jobs done
    pending = session.execute(text("""
        SELECT COUNT(*) FROM jobs
        WHERE order_id = :oid AND status NOT IN ('done', 'cancelled')
    """), {"oid": job.order_id}).scalar()

    if pending == 0:
        session.execute(text("""
            UPDATE orders SET status = 'qc', updated_at = :now
            WHERE id = :oid AND status = 'in_production'
        """), {"oid": job.order_id, "now": now})

    return _job_out(job)


# ---------------------------------------------------------------------------
# machine breakdown / repaired / maintenance
# ---------------------------------------------------------------------------

def machine_breakdown(session: Session, machine_id: uuid.UUID, body: dict, user: dict) -> dict:
    from app.models.production import Machine, MachineEvent

    actor_id = _actor(user)
    machine = _get_machine(session, machine_id)

    now = app_time.now()
    old_status = machine.status

    # Pause any running job
    if machine.current_job_id:
        job = session.get(__import__("app.models.production", fromlist=["Job"]).Job,
                          machine.current_job_id)
        if job and job.status == "running":
            job.status = "paused"
            job.updated_at = now
            session.execute(text("""
                UPDATE job_operator_sessions SET ended_at = :now, end_reason = 'breakdown'
                WHERE job_id = :jid AND ended_at IS NULL
            """), {"jid": machine.current_job_id, "now": now})

    machine.status = "breakdown"
    machine.status_changed_at = now
    machine.current_job_id = None
    machine.updated_at = now

    event = MachineEvent(
        id=uuid.uuid4(),
        machine_id=machine_id,
        kind="breakdown",
        reason_code=body.get("reason_code"),
        note=body.get("note"),
        estimated_repair_minutes=body.get("estimated_repair_minutes"),
        actor_id=actor_id,
        source="app",
        created_at=now,
    )
    session.add(event)

    ev.publish(session, "machine.status_changed", {
        "machine_id": str(machine_id), "status": "breakdown",
        "from_status": old_status,
    }, actor_id=actor_id)

    return _machine_out(machine)


def machine_repaired(session: Session, machine_id: uuid.UUID, user: dict) -> dict:
    from app.models.production import Machine, MachineEvent

    actor_id = _actor(user)
    machine = _get_machine(session, machine_id)

    if machine.status != "breakdown":
        raise AppError("INVALID_STATE", "Machine is not in breakdown status")

    now = app_time.now()
    machine.status = "idle"
    machine.status_changed_at = now
    machine.updated_at = now

    event = MachineEvent(
        id=uuid.uuid4(),
        machine_id=machine_id,
        kind="repaired",
        actor_id=actor_id,
        source="app",
        created_at=now,
    )
    session.add(event)

    ev.publish(session, "machine.status_changed", {
        "machine_id": str(machine_id), "status": "idle",
    }, actor_id=actor_id)

    return _machine_out(machine)


def machine_maintenance(session: Session, machine_id: uuid.UUID, body: dict, user: dict) -> dict:
    from app.models.production import Machine, MachineEvent

    actor_id = _actor(user)
    machine = _get_machine(session, machine_id)

    now = app_time.now()
    if machine.status == "maintenance":
        machine.status = "idle"
        kind = "maintenance_end"
    else:
        machine.status = "maintenance"
        kind = "maintenance_start"
    machine.status_changed_at = now
    machine.updated_at = now

    event = MachineEvent(
        id=uuid.uuid4(),
        machine_id=machine_id,
        kind=kind,
        note=body.get("note"),
        actor_id=actor_id,
        source="app",
        created_at=now,
    )
    session.add(event)

    ev.publish(session, "machine.status_changed", {
        "machine_id": str(machine_id), "status": machine.status,
    }, actor_id=actor_id)

    return _machine_out(machine)


# ---------------------------------------------------------------------------
# floor map + today output
# ---------------------------------------------------------------------------

def get_floor_map(session: Session) -> list[dict]:
    rows = session.execute(text("""
        SELECT m.id, m.code, m.name, m.stage, m.floor_x, m.floor_y,
               m.status, m.current_job_id, m.status_changed_at,
               j.code AS job_code, j.produced_qty, j.planned_qty,
               jos.worker_id AS current_worker_id
        FROM machines m
        LEFT JOIN jobs j ON j.id = m.current_job_id
        LEFT JOIN job_operator_sessions jos ON jos.job_id = m.current_job_id
            AND jos.ended_at IS NULL
        WHERE m.is_active = true
        ORDER BY m.stage, m.code
    """)).fetchall()

    return [
        {
            "id": str(r.id), "code": r.code, "name": r.name,
            "stage": r.stage, "floor_x": r.floor_x, "floor_y": r.floor_y,
            "status": r.status,
            "status_changed_at": r.status_changed_at.isoformat() if r.status_changed_at else None,
            "current_job": {
                "id": str(r.current_job_id),
                "code": r.job_code,
                "produced_qty": r.produced_qty,
                "planned_qty": r.planned_qty,
                "pct": round(100 * r.produced_qty / r.planned_qty, 1) if r.planned_qty else 0,
            } if r.current_job_id else None,
            "current_operator_id": str(r.current_worker_id) if r.current_worker_id else None,
        }
        for r in rows
    ]


def get_today_output(session: Session) -> list[dict]:
    today = app_time.today_local()
    rows = session.execute(text("""
        SELECT m.code AS machine_code, m.stage,
               j.id AS job_id, j.code AS job_code,
               SUM(jpl.delta_qty) AS total_qty,
               jpl.created_at::date AS log_date
        FROM job_progress_logs jpl
        JOIN jobs j ON j.id = jpl.job_id
        JOIN machines m ON m.id = j.machine_id
        WHERE DATE(jpl.created_at AT TIME ZONE 'Asia/Kolkata') = :today
        GROUP BY m.code, m.stage, j.id, j.code, jpl.created_at::date
        ORDER BY m.stage, m.code
    """), {"today": today}).fetchall()

    return [
        {
            "machine_code": r.machine_code, "stage": r.stage,
            "job_id": str(r.job_id), "job_code": r.job_code,
            "total_qty": int(r.total_qty or 0),
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# list/get jobs
# ---------------------------------------------------------------------------

def list_jobs(session: Session, filters: dict | None = None) -> tuple[list[dict], int]:
    filters = filters or {}
    page = int(filters.get("page", 1))
    size = int(filters.get("size", 50))
    offset = (page - 1) * size

    where_clauses = []
    params: dict = {}
    if filters.get("order_id"):
        where_clauses.append("j.order_id = :order_id")
        params["order_id"] = str(filters["order_id"])
    if filters.get("machine_id"):
        where_clauses.append("j.machine_id = :machine_id")
        params["machine_id"] = str(filters["machine_id"])
    if filters.get("status"):
        where_clauses.append("j.status = :status")
        params["status"] = filters["status"]
    if filters.get("stage"):
        where_clauses.append("j.stage = :stage")
        params["stage"] = filters["stage"]

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    total = session.execute(text(f"SELECT COUNT(*) FROM jobs j {where_sql}"), params).scalar() or 0

    rows = session.execute(text(f"""
        SELECT j.id, j.code, j.order_id, j.stage, j.seq, j.unit,
               j.planned_qty, j.produced_qty, j.waste_qty,
               j.machine_id, j.queue_position, j.status,
               j.started_at, j.finished_at, j.created_at,
               o.code AS order_code
        FROM jobs j
        JOIN orders o ON o.id = j.order_id
        {where_sql}
        ORDER BY j.created_at DESC
        LIMIT :limit OFFSET :offset
    """), {**params, "limit": size, "offset": offset}).fetchall()

    items = [_job_row_out(r) for r in rows]
    return items, int(total)


def get_job(session: Session, job_id: uuid.UUID) -> dict:
    job = _get_job(session, job_id)

    progress_logs = session.execute(text("""
        SELECT delta_qty, total_qty, source, created_at, worker_id
        FROM job_progress_logs WHERE job_id = :jid ORDER BY created_at
    """), {"jid": job_id}).fetchall()

    op_sessions = session.execute(text("""
        SELECT worker_id, started_at, ended_at, end_reason
        FROM job_operator_sessions WHERE job_id = :jid ORDER BY started_at
    """), {"jid": job_id}).fetchall()

    result = _job_out(job)
    result["progress_logs"] = [
        {
            "delta_qty": p.delta_qty, "total_qty": p.total_qty,
            "source": p.source, "created_at": p.created_at.isoformat(),
            "worker_id": str(p.worker_id) if p.worker_id else None,
        }
        for p in progress_logs
    ]
    result["operator_sessions"] = [
        {
            "worker_id": str(s.worker_id),
            "started_at": s.started_at.isoformat(),
            "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            "end_reason": s.end_reason,
        }
        for s in op_sessions
    ]
    return result


# ---------------------------------------------------------------------------
# interfaces implementation helpers
# ---------------------------------------------------------------------------

def assign_job_interface(
    session: Session,
    job_id: uuid.UUID,
    machine_id: uuid.UUID,
    queue_position: int | None,
    actor_id: uuid.UUID | None,
    reason: str,
) -> None:
    from app.models.production import Job, Machine

    job = session.get(Job, job_id)
    if job is None:
        raise AppError("NOT_FOUND", f"Job {job_id} not found")
    machine = session.get(Machine, machine_id)
    if machine is None:
        raise AppError("NOT_FOUND", f"Machine {machine_id} not found")

    job.machine_id = machine_id
    if queue_position is not None:
        job.queue_position = queue_position
    job.updated_at = app_time.now()

    ev.publish(session, "job.assigned", {
        "job_id": str(job_id),
        "machine_id": str(machine_id),
        "reason": reason,
    }, actor_id=actor_id)


def reorder_queue_interface(
    session: Session,
    machine_id: uuid.UUID,
    job_ids_in_order: list[uuid.UUID],
    actor_id: uuid.UUID | None,
    reason: str,
) -> None:
    now = app_time.now()
    for pos, jid in enumerate(job_ids_in_order, start=1):
        session.execute(text(
            "UPDATE jobs SET queue_position = :pos, updated_at = :now WHERE id = :id AND machine_id = :mid"
        ), {"pos": pos, "id": jid, "mid": machine_id, "now": now})

    ev.publish(session, "job.reordered", {
        "machine_id": str(machine_id), "reason": reason,
    }, actor_id=actor_id)


def split_job_interface(
    session: Session,
    job_id: uuid.UUID,
    parts_qty: list[int],
    actor_id: uuid.UUID | None,
    reason: str,
) -> list[uuid.UUID]:
    from app.models.production import Job

    job = session.get(Job, job_id)
    if job is None:
        raise AppError("NOT_FOUND", f"Job {job_id} not found")

    order_num = int(session.execute(
        text("SELECT code FROM orders WHERE id = :oid"), {"oid": job.order_id}
    ).scalar().split("-")[-1])

    now = app_time.now()
    new_ids = []
    for qty in parts_qty:
        code = next_code(session, "job", order_no=order_num)
        child = Job(
            id=uuid.uuid4(),
            code=code,
            order_id=job.order_id,
            stage=job.stage,
            seq=job.seq,
            unit=job.unit,
            planned_qty=qty,
            produced_qty=0,
            waste_qty=0,
            machine_id=job.machine_id,
            status="planned",
            split_from_job_id=job_id,
            created_at=now,
        )
        session.add(child)
        new_ids.append(child.id)

    job.planned_qty -= sum(parts_qty)
    job.updated_at = now

    ev.publish(session, "job.split", {
        "parent_job_id": str(job_id), "reason": reason,
        "new_job_ids": [str(i) for i in new_ids],
    }, actor_id=actor_id)

    return new_ids


def record_machine_signal_impl(
    session: Session,
    machine_id: uuid.UUID,
    kind: str,
    params: dict,
    source: str,
) -> None:
    from app.models.production import MachineEvent

    now = app_time.now()
    event = MachineEvent(
        id=uuid.uuid4(),
        machine_id=machine_id,
        kind=kind,
        note=params.get("note"),
        estimated_repair_minutes=params.get("estimated_repair_minutes"),
        source=source,
        created_at=now,
    )
    session.add(event)

    ev.publish(session, "machine.status_changed", {
        "machine_id": str(machine_id), "kind": kind, "source": source,
    })


# ---------------------------------------------------------------------------
# serializers
# ---------------------------------------------------------------------------

def _job_out(job) -> dict:
    return {
        "id": str(job.id),
        "code": job.code,
        "order_id": str(job.order_id),
        "stage": job.stage,
        "seq": job.seq,
        "unit": job.unit,
        "planned_qty": job.planned_qty,
        "produced_qty": job.produced_qty,
        "waste_qty": job.waste_qty,
        "machine_id": str(job.machine_id) if job.machine_id else None,
        "queue_position": job.queue_position,
        "status": job.status,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "created_at": job.created_at.isoformat(),
    }


def _job_row_out(r) -> dict:
    return {
        "id": str(r.id), "code": r.code,
        "order_id": str(r.order_id), "order_code": r.order_code,
        "stage": r.stage, "seq": r.seq, "unit": r.unit,
        "planned_qty": r.planned_qty, "produced_qty": r.produced_qty,
        "waste_qty": r.waste_qty,
        "machine_id": str(r.machine_id) if r.machine_id else None,
        "queue_position": r.queue_position,
        "status": r.status,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        "created_at": r.created_at.isoformat(),
    }


def _machine_out(m) -> dict:
    return {
        "id": str(m.id),
        "code": m.code,
        "stage": m.stage,
        "status": m.status,
        "current_job_id": str(m.current_job_id) if m.current_job_id else None,
    }
