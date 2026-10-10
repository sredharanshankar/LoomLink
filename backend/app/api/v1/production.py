from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, Query

from app.deps import get_db, require_permission
import app.services.master_data as md

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
            "SELECT kind, params, created_at FROM machine_events "
            "WHERE machine_id = :mid ORDER BY created_at DESC LIMIT 100"
        ),
        {"mid": id},
    ).fetchall()
    return {"items": [{"kind": r[0], "params": r[1], "created_at": r[2].isoformat()} for r in rows]}


# ---------------------------------------------------------------------------
# Production floor / jobs — implemented in A-M4
# ---------------------------------------------------------------------------

@router.get("/production/floor")
def floor_map(user=Depends(require_permission("production.view"))):
    raise NotImplementedError


@router.get("/production/today")
def today_output(user=Depends(require_permission("production.view"))):
    raise NotImplementedError


@router.get("/jobs")
def list_jobs(user=Depends(require_permission("production.view"))):
    raise NotImplementedError


@router.get("/jobs/{id}")
def get_job(id: str, user=Depends(require_permission("production.view"))):
    raise NotImplementedError


@router.post("/jobs/{id}/assign")
def assign_job(id: str, user=Depends(require_permission("production.plan"))):
    raise NotImplementedError


@router.post("/jobs/reorder")
def reorder_jobs(user=Depends(require_permission("production.plan"))):
    raise NotImplementedError


@router.post("/jobs/{id}/split")
def split_job(id: str, user=Depends(require_permission("production.plan"))):
    raise NotImplementedError


@router.post("/jobs/{id}/start")
def start_job(id: str, user=Depends(require_permission("production.operate"))):
    raise NotImplementedError


@router.post("/jobs/{id}/progress")
def job_progress(id: str, user=Depends(require_permission("production.operate"))):
    raise NotImplementedError


@router.post("/jobs/{id}/pause")
def pause_job(id: str, user=Depends(require_permission("production.operate"))):
    raise NotImplementedError


@router.post("/jobs/{id}/resume")
def resume_job(id: str, user=Depends(require_permission("production.operate"))):
    raise NotImplementedError


@router.post("/jobs/{id}/handover")
def handover_job(id: str, user=Depends(require_permission("production.operate"))):
    raise NotImplementedError


@router.post("/jobs/{id}/accept-handover")
def accept_handover(id: str, user=Depends(require_permission("production.operate"))):
    raise NotImplementedError


@router.post("/jobs/{id}/finish")
def finish_job(id: str, user=Depends(require_permission("production.operate"))):
    raise NotImplementedError


@router.post("/machines/{id}/breakdown")
def machine_breakdown(id: str, user=Depends(require_permission("production.operate"))):
    raise NotImplementedError


@router.post("/machines/{id}/repaired")
def machine_repaired(id: str, user=Depends(require_permission("production.operate"))):
    raise NotImplementedError


@router.post("/machines/{id}/maintenance")
def machine_maintenance(id: str, user=Depends(require_permission("machines.manage"))):
    raise NotImplementedError


# ---------------------------------------------------------------------------
# serializers
# ---------------------------------------------------------------------------

def _machine_out(m, caps) -> dict:
    return {
        "id": str(m.id),
        "code": m.code,
        "stage": m.stage,
        "floor_x": m.floor_x,
        "floor_y": m.floor_y,
        "status": m.status,
        "current_job_id": str(m.current_job_id) if m.current_job_id else None,
        "notes": m.notes,
        "fabric_type_ids": [str(c.fabric_type_id) for c in caps],
        "created_at": m.created_at.isoformat(),
    }
