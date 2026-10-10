from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, Query

from app.deps import get_db, require_permission
import app.services.master_data as md
import app.services.production as prod_svc

router = APIRouter()


# ---------------------------------------------------------------------------
# Machines
# ---------------------------------------------------------------------------

@router.get("/machines")
def list_machines(
    stage: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user=Depends(require_permission("production.view")),
    db=Depends(get_db),
):
    items, total = md.list_machines(db, stage=stage, page=page, size=size)
    caps_map = {str(m.id): md.get_machine_capabilities(db, m.id) for m in items}
    return {
        "items": [_machine_out(m, caps_map.get(str(m.id), [])) for m in items],
        "total": total, "page": page, "size": size,
    }


@router.post("/machines", status_code=201)
def create_machine(
    body: dict,
    user=Depends(require_permission("machines.manage")),
    db=Depends(get_db),
):
    machine = md.create_machine(db, body, user)
    db.commit()
    caps = md.get_machine_capabilities(db, machine.id)
    return _machine_out(machine, caps)


@router.get("/machines/{id}")
def get_machine(
    id: uuid.UUID,
    user=Depends(require_permission("production.view")),
    db=Depends(get_db),
):
    machine = md.get_machine(db, id)
    caps = md.get_machine_capabilities(db, id)
    return _machine_out(machine, caps)


@router.patch("/machines/{id}")
def update_machine(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("machines.manage")),
    db=Depends(get_db),
):
    machine = md.update_machine(db, id, body, user)
    db.commit()
    caps = md.get_machine_capabilities(db, id)
    return _machine_out(machine, caps)


@router.get("/machines/{id}/events")
def machine_events(
    id: uuid.UUID,
    user=Depends(require_permission("production.view")),
    db=Depends(get_db),
):
    from sqlalchemy import text
    rows = db.execute(
        text(
            "SELECT kind, note, estimated_repair_minutes, created_at FROM machine_events "
            "WHERE machine_id = :mid ORDER BY created_at DESC LIMIT 100"
        ),
        {"mid": id},
    ).fetchall()
    return {"items": [{"kind": r[0], "note": r[1],
                        "estimated_repair_minutes": r[2],
                        "created_at": r[3].isoformat()} for r in rows]}


# ---------------------------------------------------------------------------
# Production floor / jobs
# ---------------------------------------------------------------------------

@router.get("/production/floor")
def floor_map(
    user=Depends(require_permission("production.view")),
    db=Depends(get_db),
):
    return {"machines": prod_svc.get_floor_map(db)}


@router.get("/production/today")
def today_output(
    user=Depends(require_permission("production.view")),
    db=Depends(get_db),
):
    return {"items": prod_svc.get_today_output(db)}


@router.get("/jobs")
def list_jobs(
    order_id: uuid.UUID | None = Query(None),
    machine_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    stage: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user=Depends(require_permission("production.view")),
    db=Depends(get_db),
):
    filters = {
        "order_id": order_id, "machine_id": machine_id,
        "status": status, "stage": stage,
        "page": page, "size": size,
    }
    items, total = prod_svc.list_jobs(db, filters)
    return {"items": items, "total": total, "page": page, "size": size}


@router.get("/jobs/{id}")
def get_job(
    id: uuid.UUID,
    user=Depends(require_permission("production.view")),
    db=Depends(get_db),
):
    return prod_svc.get_job(db, id)


@router.post("/jobs/{id}/assign")
def assign_job(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("production.plan")),
    db=Depends(get_db),
):
    result = prod_svc.assign_job(db, id, body, user)
    db.commit()
    return result


@router.post("/jobs/reorder")
def reorder_jobs(
    body: dict,
    user=Depends(require_permission("production.plan")),
    db=Depends(get_db),
):
    machine_id = uuid.UUID(str(body["machine_id"]))
    job_ids = [uuid.UUID(str(j)) for j in body["job_ids"]]
    result = prod_svc.reorder_queue(db, machine_id, job_ids, user)
    db.commit()
    return result


@router.post("/jobs/{id}/split")
def split_job(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("production.plan")),
    db=Depends(get_db),
):
    result = prod_svc.split_job(db, id, body, user)
    db.commit()
    return {"jobs": result}


@router.post("/jobs/{id}/start")
def start_job(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("production.operate")),
    db=Depends(get_db),
):
    result = prod_svc.start_job(db, id, body, user)
    db.commit()
    return result


@router.post("/jobs/{id}/progress")
def job_progress(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("production.operate")),
    db=Depends(get_db),
):
    result = prod_svc.record_progress(db, id, body, user)
    db.commit()
    return result


@router.post("/jobs/{id}/pause")
def pause_job(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("production.operate")),
    db=Depends(get_db),
):
    result = prod_svc.pause_job(db, id, body, user)
    db.commit()
    return result


@router.post("/jobs/{id}/resume")
def resume_job(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("production.operate")),
    db=Depends(get_db),
):
    result = prod_svc.resume_job(db, id, body, user)
    db.commit()
    return result


@router.post("/jobs/{id}/handover")
def handover_job(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("production.operate")),
    db=Depends(get_db),
):
    result = prod_svc.handover_job(db, id, body, user)
    db.commit()
    return result


@router.post("/jobs/{id}/accept-handover")
def accept_handover(
    id: uuid.UUID,
    user=Depends(require_permission("production.operate")),
    db=Depends(get_db),
):
    result = prod_svc.accept_handover(db, id, user)
    db.commit()
    return result


@router.post("/jobs/{id}/finish")
def finish_job(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("production.operate")),
    db=Depends(get_db),
):
    result = prod_svc.finish_job(db, id, body, user)
    db.commit()
    return result


@router.post("/machines/{id}/breakdown")
def machine_breakdown(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("production.operate")),
    db=Depends(get_db),
):
    result = prod_svc.machine_breakdown(db, id, body, user)
    db.commit()
    return result


@router.post("/machines/{id}/repaired")
def machine_repaired(
    id: uuid.UUID,
    user=Depends(require_permission("production.operate")),
    db=Depends(get_db),
):
    result = prod_svc.machine_repaired(db, id, user)
    db.commit()
    return result


@router.post("/machines/{id}/maintenance")
def machine_maintenance(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("machines.manage")),
    db=Depends(get_db),
):
    result = prod_svc.machine_maintenance(db, id, body, user)
    db.commit()
    return result


# ---------------------------------------------------------------------------
# serializers
# ---------------------------------------------------------------------------

def _machine_out(m, caps) -> dict:
    return {
        "id": str(m.id),
        "code": m.code,
        "name": m.name,
        "stage": m.stage,
        "floor_x": m.floor_x,
        "floor_y": m.floor_y,
        "status": m.status,
        "current_job_id": str(m.current_job_id) if m.current_job_id else None,
        "fabric_type_ids": [str(c.fabric_type_id) for c in caps],
        "created_at": m.created_at.isoformat(),
    }
