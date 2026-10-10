from fastapi import APIRouter, Depends
from app.deps import require_permission

router = APIRouter()


@router.get("/machines")
def list_machines(user=Depends(require_permission("production.view"))):
    raise NotImplementedError


@router.post("/machines")
def create_machine(user=Depends(require_permission("machines.manage"))):
    raise NotImplementedError


@router.get("/machines/{id}")
def get_machine(id: str, user=Depends(require_permission("production.view"))):
    raise NotImplementedError


@router.patch("/machines/{id}")
def update_machine(id: str, user=Depends(require_permission("machines.manage"))):
    raise NotImplementedError


@router.get("/machines/{id}/events")
def machine_events(id: str, user=Depends(require_permission("production.view"))):
    raise NotImplementedError


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