from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, Query

from app.deps import get_db, require_permission
import app.services.master_data as md

router = APIRouter()


# ---------------------------------------------------------------------------
# Workers
# ---------------------------------------------------------------------------

@router.get("/workers")
def list_workers(
    active_only: bool = Query(True),
    stage: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user=Depends(require_permission("workers.view")),
    db=Depends(get_db),
):
    items, total = md.list_workers(db, active_only=active_only, stage=stage, page=page, size=size)
    return {"items": [_worker_out(r) for r in items], "total": total, "page": page, "size": size}


@router.post("/workers", status_code=201)
def create_worker(
    body: dict,
    user=Depends(require_permission("workers.manage")),
    db=Depends(get_db),
):
    row = md.create_worker(db, body, user)
    db.commit()
    return _worker_out(row)


@router.get("/workers/{id}")
def get_worker(
    id: uuid.UUID,
    user=Depends(require_permission("workers.view")),
    db=Depends(get_db),
):
    return _worker_out(md.get_worker(db, id))


@router.patch("/workers/{id}")
def update_worker(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("workers.manage")),
    db=Depends(get_db),
):
    row = md.update_worker(db, id, body, user)
    db.commit()
    return _worker_out(row)


# ---------------------------------------------------------------------------
# Shifts
# ---------------------------------------------------------------------------

@router.get("/shifts")
def list_shifts(
    user=Depends(require_permission("workers.view")),
    db=Depends(get_db),
):
    return {"items": [_shift_out(r) for r in md.list_shifts(db)]}


@router.post("/shifts", status_code=201)
def create_shift(
    body: dict,
    user=Depends(require_permission("workers.manage")),
    db=Depends(get_db),
):
    row = md.create_shift(db, body, user)
    db.commit()
    return _shift_out(row)


# ---------------------------------------------------------------------------
# Shift assignments, attendance, payroll — implemented in A-M7
# ---------------------------------------------------------------------------

@router.get("/shift-assignments")
def list_assignments(user=Depends(require_permission("workers.view"))):
    raise NotImplementedError


@router.post("/shift-assignments")
def create_assignment(user=Depends(require_permission("attendance.manage"))):
    raise NotImplementedError


@router.post("/attendance/check-in")
def check_in(user=Depends(require_permission("attendance.self"))):
    raise NotImplementedError


@router.post("/attendance/check-out")
def check_out(user=Depends(require_permission("attendance.self"))):
    raise NotImplementedError


@router.get("/attendance")
def list_attendance(user=Depends(require_permission("attendance.view"))):
    raise NotImplementedError


@router.patch("/attendance/{id}")
def correct_attendance(id: str, user=Depends(require_permission("attendance.manage"))):
    raise NotImplementedError


@router.get("/wage-advances")
def list_advances(user=Depends(require_permission("payroll.manage"))):
    raise NotImplementedError


@router.post("/wage-advances")
def create_advance(user=Depends(require_permission("payroll.manage"))):
    raise NotImplementedError


@router.get("/payroll/runs")
def list_payroll_runs(user=Depends(require_permission("payroll.view"))):
    raise NotImplementedError


@router.post("/payroll/runs")
def create_payroll_run(user=Depends(require_permission("payroll.manage"))):
    raise NotImplementedError


@router.get("/payroll/runs/{id}")
def get_payroll_run(id: str, user=Depends(require_permission("payroll.view"))):
    raise NotImplementedError


@router.post("/payroll/runs/{id}/approve")
def approve_payroll(id: str, user=Depends(require_permission("payroll.approve"))):
    raise NotImplementedError


@router.post("/payroll/runs/{id}/mark-paid")
def mark_payroll_paid(id: str, user=Depends(require_permission("payroll.manage"))):
    raise NotImplementedError


@router.get("/payroll/runs/{id}/payslips.pdf")
def payslips_pdf(id: str, user=Depends(require_permission("payroll.view"))):
    raise NotImplementedError


# ---------------------------------------------------------------------------
# serializers
# ---------------------------------------------------------------------------

def _worker_out(r) -> dict:
    return {
        "id": str(r.id),
        "code": r.code,
        "name": r.name,
        "phone": r.phone,
        "department": r.department,
        "skill_stages": r.skill_stages or [],
        "wage_type": r.wage_type,
        "wage_rate_paise": r.wage_rate_paise,
        "piece_rate_paise_per_m": r.piece_rate_paise_per_m,
        "default_shift": r.default_shift,
        "overtime_willing": r.overtime_willing,
        "joined_on": r.joined_on.isoformat() if r.joined_on else None,
        "is_active": r.is_active,
        "preferred_language": r.preferred_language,
        "created_at": r.created_at.isoformat(),
    }


def _shift_out(r) -> dict:
    return {
        "code": r.code,
        "name": r.name,
        "start_time": r.start_time.isoformat(),
        "end_time": r.end_time.isoformat(),
        "break_minutes": r.break_minutes,
        "is_overtime": r.is_overtime,
        "created_at": r.created_at.isoformat(),
    }
