"""Machine simulator endpoints — owned by Lane B; only mounted when DEMO_MODE=true."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, Body
from sqlalchemy import text
from app.deps import require_permission, get_db
from app.core.errors import AppError

router = APIRouter()


@router.post("/simulator/machines/{id}/emit")
def simulator_emit(
    id: str,
    body: dict = Body(default={}),
    user=Depends(require_permission("ripple.manage")),
    db=Depends(get_db),
):
    """
    Emit a simulated machine event for demo purposes.
    body: { "event": "breakdown" | "repaired" | "progress", "metres": N, "reason_code": "..." }
    """
    event_type = (body.get("event") or "").strip()
    if not event_type:
        raise AppError("VALIDATION_ERROR", "event field required")

    # Resolve machine
    row = db.execute(
        text("SELECT id, code, name, status FROM machines WHERE code = :c OR id::text = :c"),
        {"c": id},
    ).fetchone()
    if not row:
        raise AppError("NOT_FOUND", f"Machine {id} not found")

    machine_id = row[0]
    machine_code = row[1]

    import app.services.production as prod_svc
    actor = {"id": str(user.get("id", uuid.uuid4())), "sub": user.get("sub", "simulator")}
    actor["id"] = actor.get("sub") or str(uuid.uuid4())

    if event_type == "breakdown":
        result = prod_svc.machine_breakdown(db, machine_id, {
            "reason_code": body.get("reason_code", "simulator"),
            "note": body.get("note", "Simulated breakdown"),
            "estimated_repair_minutes": body.get("estimated_repair_minutes", 360),
        }, actor)
        db.commit()
        return {"status": "ok", "event": "breakdown", "machine": machine_code, "result": result}

    elif event_type == "repaired":
        result = prod_svc.machine_repaired(db, machine_id, actor)
        db.commit()
        return {"status": "ok", "event": "repaired", "machine": machine_code, "result": result}

    elif event_type == "progress":
        metres = float(body.get("metres", 0))
        if metres <= 0:
            raise AppError("VALIDATION_ERROR", "metres must be > 0")
        # Find the running job on this machine
        job_row = db.execute(text("""
            SELECT id, produced_qty FROM jobs
            WHERE machine_id = :mid AND status = 'running'
            ORDER BY started_at DESC LIMIT 1
        """), {"mid": str(machine_id)}).fetchone()
        if not job_row:
            raise AppError("NOT_FOUND", f"No running job on machine {machine_code}")
        job_id = job_row[0]
        result = prod_svc.record_progress(db, job_id, {"quantity_cm": int(metres * 100)}, actor)
        db.commit()
        return {"status": "ok", "event": "progress", "machine": machine_code, "metres_added": metres}

    else:
        raise AppError("VALIDATION_ERROR", f"Unknown event type: {event_type}. Use breakdown/repaired/progress")
