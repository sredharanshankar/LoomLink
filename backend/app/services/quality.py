"""A-M5: Quality control service — rolls, inspections, defect patterns, passport."""
from __future__ import annotations
import uuid
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


# ---------------------------------------------------------------------------
# create rolls
# ---------------------------------------------------------------------------

def create_rolls(session: Session, body: dict, user: dict) -> list[dict]:
    from app.models.quality import Roll
    from app.models.production import Job

    actor_id = _actor(user)
    finishing_job_id = uuid.UUID(str(body["finishing_job_id"]))
    lengths_cm: list[int] = [int(l) for l in body["lengths_cm"]]
    shelf_location = body.get("shelf_location")

    if not lengths_cm:
        raise AppError("VALIDATION_ERROR", "lengths_cm must not be empty")
    for l in lengths_cm:
        if l <= 0:
            raise AppError("VALIDATION_ERROR", "Each length_cm must be positive")

    job = session.get(Job, finishing_job_id)
    if job is None:
        raise AppError("NOT_FOUND", f"Job {finishing_job_id} not found")
    if job.stage != "finishing":
        raise AppError("VALIDATION_ERROR", "Job must be in finishing stage")

    order_row = session.execute(
        text("SELECT code, fabric_type_id, buyer_id FROM orders WHERE id = :oid"),
        {"oid": job.order_id},
    ).fetchone()
    if order_row is None:
        raise AppError("NOT_FOUND", "Order not found for job")

    now = app_time.now()
    rolls = []

    for length_cm in lengths_cm:
        code = next_code(session, "roll")
        roll = Roll(
            id=uuid.uuid4(),
            code=code,
            order_id=job.order_id,
            finishing_job_id=finishing_job_id,
            length_cm=length_cm,
            shelf_location=shelf_location,
            status="pending_qc",
            created_by=actor_id,
            created_at=now,
        )
        session.add(roll)
        session.flush()

        ev.publish(session, "roll.created", {
            "roll_id": str(roll.id),
            "code": code,
            "order_id": str(job.order_id),
            "length_cm": length_cm,
        }, actor_id=actor_id)

        rolls.append(roll)

    return [
        {
            "id": str(r.id),
            "code": r.code,
            "order_id": str(r.order_id),
            "length_cm": r.length_cm,
            "shelf_location": r.shelf_location,
            "status": r.status,
            "label_url": f"/api/v1/labels/roll/{r.id}.pdf",
            "created_at": r.created_at.isoformat(),
        }
        for r in rolls
    ]


# ---------------------------------------------------------------------------
# list/get rolls
# ---------------------------------------------------------------------------

def list_rolls(session: Session, filters: dict | None = None) -> tuple[list[dict], int]:
    filters = filters or {}
    page = int(filters.get("page", 1))
    size = int(filters.get("size", 50))
    offset = (page - 1) * size

    where_clauses = []
    params: dict = {}
    if filters.get("status"):
        where_clauses.append("r.status = :status")
        params["status"] = filters["status"]
    if filters.get("order_id"):
        where_clauses.append("r.order_id = :order_id")
        params["order_id"] = str(filters["order_id"])

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    total = session.execute(
        text(f"SELECT COUNT(*) FROM rolls r {where_sql}"), params
    ).scalar() or 0

    rows = session.execute(text(f"""
        SELECT r.id, r.code, r.order_id, r.length_cm, r.weight_g,
               r.status, r.shelf_location, r.created_at,
               o.code AS order_code
        FROM rolls r
        JOIN orders o ON o.id = r.order_id
        {where_sql}
        ORDER BY r.created_at DESC
        LIMIT :limit OFFSET :offset
    """), {**params, "limit": size, "offset": offset}).fetchall()

    items = [
        {
            "id": str(r.id), "code": r.code,
            "order_id": str(r.order_id), "order_code": r.order_code,
            "length_cm": r.length_cm, "weight_g": r.weight_g,
            "status": r.status, "shelf_location": r.shelf_location,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
    return items, int(total)


def get_roll(session: Session, roll_id: uuid.UUID) -> dict:
    from app.models.quality import Roll
    roll = session.get(Roll, roll_id)
    if roll is None:
        raise AppError("NOT_FOUND", f"Roll {roll_id} not found")

    inspections = session.execute(text("""
        SELECT i.id, i.decision, i.measured_length_cm, i.notes, i.created_at,
               i.inspector_id
        FROM inspections i WHERE i.roll_id = :rid ORDER BY i.created_at
    """), {"rid": roll_id}).fetchall()

    return {
        "id": str(roll.id), "code": roll.code,
        "order_id": str(roll.order_id),
        "finishing_job_id": str(roll.finishing_job_id) if roll.finishing_job_id else None,
        "length_cm": roll.length_cm, "weight_g": roll.weight_g,
        "status": roll.status, "shelf_location": roll.shelf_location,
        "created_at": roll.created_at.isoformat(),
        "inspections": [
            {
                "id": str(i.id), "decision": i.decision,
                "measured_length_cm": i.measured_length_cm,
                "notes": i.notes, "created_at": i.created_at.isoformat(),
                "inspector_id": str(i.inspector_id) if i.inspector_id else None,
            }
            for i in inspections
        ],
    }


# ---------------------------------------------------------------------------
# inspect roll
# ---------------------------------------------------------------------------

def inspect_roll(session: Session, roll_id: uuid.UUID, body: dict, user: dict) -> dict:
    from app.models.quality import Roll, Inspection, InspectionDefect

    actor_id = _actor(user)
    roll = session.get(Roll, roll_id)
    if roll is None:
        raise AppError("NOT_FOUND", f"Roll {roll_id} not found")
    if roll.status not in ("pending_qc", "rework"):
        raise AppError("INVALID_STATE", f"Roll status is {roll.status}, cannot inspect")

    decision = body["decision"]
    measured_length_cm = int(body["measured_length_cm"])

    now = app_time.now()
    inspection = Inspection(
        id=uuid.uuid4(),
        roll_id=roll_id,
        inspector_id=actor_id,
        decision=decision,
        measured_length_cm=measured_length_cm,
        notes=body.get("notes"),
        created_at=now,
    )
    session.add(inspection)
    session.flush()

    for d in body.get("defects", []):
        defect = InspectionDefect(
            id=uuid.uuid4(),
            inspection_id=inspection.id,
            defect_code=d["defect_code"],
            position_cm=d.get("position_cm"),
            severity=d["severity"],
            photo_url=d.get("photo_url"),
            created_at=now,
        )
        session.add(defect)

    old_status = roll.status
    roll.status = decision
    roll.updated_at = now

    audit(session, actor_id, "inspect", "roll", str(roll_id),
          before={"status": old_status}, after={"status": decision})

    ev.publish(session, "roll.inspected", {
        "roll_id": str(roll_id),
        "order_id": str(roll.order_id),
        "decision": decision,
        "measured_length_cm": measured_length_cm,
    }, actor_id=actor_id)

    if decision == "passed":
        _check_order_readiness(session, roll.order_id, now)

    return get_roll(session, roll_id)


def _check_order_readiness(session: Session, order_id: uuid.UUID, now) -> None:
    """Move order to 'ready' if passed_cm >= quantity_cm within tolerance."""
    order_row = session.execute(
        text("SELECT quantity_cm, status FROM orders WHERE id = :oid"),
        {"oid": order_id},
    ).fetchone()
    if order_row is None or order_row.status not in ("qc", "in_production"):
        return

    passed_cm = session.execute(text("""
        SELECT COALESCE(SUM(i.measured_length_cm), 0)
        FROM rolls r
        JOIN inspections i ON i.roll_id = r.id
        WHERE r.order_id = :oid AND i.decision = 'passed'
          AND i.id = (
              SELECT id FROM inspections i2 WHERE i2.roll_id = r.id
              ORDER BY created_at DESC LIMIT 1
          )
    """), {"oid": order_id}).scalar() or 0

    settings_row = session.execute(
        text("SELECT order_tolerance_bp FROM mill_settings LIMIT 1")
    ).fetchone()
    tolerance_bp = settings_row.order_tolerance_bp if settings_row else 200

    threshold_cm = order_row.quantity_cm * (10000 - tolerance_bp) // 10000

    if int(passed_cm) >= threshold_cm:
        session.execute(text("""
            UPDATE orders SET status = 'ready', updated_at = :now
            WHERE id = :oid AND status IN ('qc', 'in_production')
        """), {"oid": order_id, "now": now})
        ev.publish(session, "order.status_changed", {
            "order_id": str(order_id), "from": "qc", "to": "ready"
        })


# ---------------------------------------------------------------------------
# rework complete
# ---------------------------------------------------------------------------

def rework_complete(session: Session, roll_id: uuid.UUID, user: dict) -> dict:
    from app.models.quality import Roll

    actor_id = _actor(user)
    roll = session.get(Roll, roll_id)
    if roll is None:
        raise AppError("NOT_FOUND", f"Roll {roll_id} not found")
    if roll.status != "rework":
        raise AppError("INVALID_STATE", f"Roll status is {roll.status}, not rework")

    now = app_time.now()
    roll.status = "pending_qc"
    roll.updated_at = now

    ev.publish(session, "roll.rework_complete", {
        "roll_id": str(roll_id),
        "order_id": str(roll.order_id),
    }, actor_id=actor_id)

    return get_roll(session, roll_id)


# ---------------------------------------------------------------------------
# quality queues
# ---------------------------------------------------------------------------

def get_quality_queues(session: Session) -> dict:
    statuses = ["pending_qc", "passed", "rework", "rejected"]
    result = {}
    for status in statuses:
        rows = session.execute(text("""
            SELECT r.id, r.code, r.order_id, r.length_cm, r.shelf_location,
                   o.code AS order_code
            FROM rolls r JOIN orders o ON o.id = r.order_id
            WHERE r.status = :status
            ORDER BY r.created_at
            LIMIT 50
        """), {"status": status}).fetchall()

        count = session.execute(
            text("SELECT COUNT(*) FROM rolls WHERE status = :s"), {"s": status}
        ).scalar() or 0

        result[status] = {
            "count": int(count),
            "items": [
                {
                    "id": str(r.id), "code": r.code,
                    "order_id": str(r.order_id), "order_code": r.order_code,
                    "length_cm": r.length_cm, "shelf_location": r.shelf_location,
                }
                for r in rows
            ],
        }
    return result


# ---------------------------------------------------------------------------
# defect patterns (Defect Detective)
# ---------------------------------------------------------------------------

def get_defect_patterns(session: Session) -> list[dict]:
    """Flag machines where defect rate >= 2x mill average and >= 3 occurrences."""
    total_inspections = session.execute(
        text("SELECT COUNT(*) FROM inspections")
    ).scalar() or 1

    defect_count = session.execute(
        text("SELECT COUNT(*) FROM inspection_defects")
    ).scalar() or 0

    mill_avg_rate = defect_count / max(int(total_inspections), 1)

    machine_rows = session.execute(text("""
        SELECT m.code AS machine_code, m.id AS machine_id,
               COUNT(id2.id) AS defect_count,
               COUNT(DISTINCT insp.id) AS inspection_count
        FROM machines m
        JOIN jobs j ON j.machine_id = m.id
        JOIN rolls r ON r.finishing_job_id = j.id
        JOIN inspections insp ON insp.roll_id = r.id
        JOIN inspection_defects id2 ON id2.inspection_id = insp.id
        GROUP BY m.id, m.code
        HAVING COUNT(id2.id) >= 3
    """)).fetchall()

    patterns = []
    for row in machine_rows:
        rate = row.defect_count / max(row.inspection_count, 1)
        if rate >= 2 * mill_avg_rate:
            patterns.append({
                "dimension": "machine",
                "ref_id": str(row.machine_id),
                "ref_label": row.machine_code,
                "defect_count": row.defect_count,
                "inspection_count": row.inspection_count,
                "rate": round(rate, 3),
                "mill_avg_rate": round(mill_avg_rate, 3),
            })

    return patterns


# ---------------------------------------------------------------------------
# roll passport
# ---------------------------------------------------------------------------

def get_roll_passport(session: Session, roll_id: uuid.UUID, user: dict) -> dict:
    from app.models.quality import Roll

    roll = session.get(Roll, roll_id)
    if roll is None:
        raise AppError("NOT_FOUND", f"Roll {roll_id} not found")

    inspections = session.execute(text("""
        SELECT i.id, i.decision, i.measured_length_cm, i.notes, i.created_at,
               i.inspector_id
        FROM inspections i WHERE i.roll_id = :rid ORDER BY i.created_at
    """), {"rid": roll_id}).fetchall()

    defects = session.execute(text("""
        SELECT id2.defect_code, id2.severity, id2.position_cm, id2.photo_url,
               insp.created_at AS inspection_at
        FROM inspection_defects id2
        JOIN inspections insp ON insp.id = id2.inspection_id
        WHERE insp.roll_id = :rid ORDER BY insp.created_at, id2.defect_code
    """), {"rid": roll_id}).fetchall()

    job_row = None
    if roll.finishing_job_id:
        job_row = session.execute(text("""
            SELECT j.code, j.stage, j.started_at, j.finished_at,
                   m.code AS machine_code
            FROM jobs j LEFT JOIN machines m ON m.id = j.machine_id
            WHERE j.id = :jid
        """), {"jid": roll.finishing_job_id}).fetchone()

    op_sessions = []
    if roll.finishing_job_id:
        op_sessions_rows = session.execute(text("""
            SELECT jos.worker_id, jos.started_at, jos.ended_at, w.name AS worker_name
            FROM job_operator_sessions jos
            LEFT JOIN workers w ON w.id = jos.worker_id
            WHERE jos.job_id = :jid ORDER BY jos.started_at
        """), {"jid": roll.finishing_job_id}).fetchall()
        op_sessions = op_sessions_rows

    dispatch_row = session.execute(text("""
        SELECT d.code, d.status, d.dispatched_at
        FROM dispatch_items di
        JOIN dispatches d ON d.id = di.dispatch_id
        WHERE di.roll_id = :rid AND d.status != 'cancelled'
        ORDER BY d.dispatched_at NULLS LAST LIMIT 1
    """), {"rid": roll_id}).fetchone()

    passport = {
        "roll_id": str(roll.id),
        "code": roll.code,
        "order_id": str(roll.order_id),
        "length_cm": roll.length_cm,
        "weight_g": roll.weight_g,
        "status": roll.status,
        "shelf_location": roll.shelf_location,
        "created_at": roll.created_at.isoformat(),
        "job": {
            "code": job_row.code if job_row else None,
            "stage": job_row.stage if job_row else None,
            "machine_code": job_row.machine_code if job_row else None,
            "started_at": job_row.started_at.isoformat() if job_row and job_row.started_at else None,
            "finished_at": job_row.finished_at.isoformat() if job_row and job_row.finished_at else None,
        } if job_row else None,
        "operator_sessions": [
            {
                "worker_id": str(s.worker_id), "worker_name": s.worker_name,
                "started_at": s.started_at.isoformat(),
                "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            }
            for s in op_sessions
        ],
        "inspections": [
            {
                "id": str(i.id), "decision": i.decision,
                "measured_length_cm": i.measured_length_cm,
                "notes": i.notes, "created_at": i.created_at.isoformat(),
            }
            for i in inspections
        ],
        "defects": [
            {
                "defect_code": d.defect_code, "severity": d.severity,
                "position_cm": d.position_cm, "photo_url": d.photo_url,
                "inspection_at": d.inspection_at.isoformat(),
            }
            for d in defects
        ],
        "dispatch": {
            "code": dispatch_row.code,
            "status": dispatch_row.status,
            "dispatched_at": dispatch_row.dispatched_at.isoformat() if dispatch_row.dispatched_at else None,
        } if dispatch_row else None,
    }

    from app.core.rbac import has_permission
    if has_permission(user.get("role", ""), "finance.view_costs"):
        try:
            from app.services.finance import get_roll_cost
            passport["cost"] = get_roll_cost(session, roll_id, user)
        except Exception:
            passport["cost"] = None

    return passport
