"""Workers, shifts, attendance, payroll router."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from app.deps import get_db, require_permission
import app.services.master_data as md
import app.services.attendance as att_svc
import app.services.payroll as pay_svc

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
def create_worker(body: dict, user=Depends(require_permission("workers.manage")), db=Depends(get_db)):
    row = md.create_worker(db, body, user)
    db.commit()
    return _worker_out(row)


@router.get("/workers/{id}")
def get_worker(id: uuid.UUID, user=Depends(require_permission("workers.view")), db=Depends(get_db)):
    return _worker_out(md.get_worker(db, id))


@router.patch("/workers/{id}")
def update_worker(id: uuid.UUID, body: dict, user=Depends(require_permission("workers.manage")), db=Depends(get_db)):
    row = md.update_worker(db, id, body, user)
    db.commit()
    return _worker_out(row)


# ---------------------------------------------------------------------------
# Shifts
# ---------------------------------------------------------------------------

@router.get("/shifts")
def list_shifts(user=Depends(require_permission("workers.view")), db=Depends(get_db)):
    return {"items": [_shift_out(r) for r in md.list_shifts(db)]}


@router.post("/shifts", status_code=201)
def create_shift(body: dict, user=Depends(require_permission("workers.manage")), db=Depends(get_db)):
    row = md.create_shift(db, body, user)
    db.commit()
    return _shift_out(row)


# ---------------------------------------------------------------------------
# Shift assignments
# ---------------------------------------------------------------------------

@router.get("/shift-assignments")
def list_assignments(
    worker_id: uuid.UUID | None = Query(None),
    date: str | None = Query(None),
    shift_code: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user=Depends(require_permission("workers.view")),
    db=Depends(get_db),
):
    items, total = att_svc.list_shift_assignments(db, {
        "worker_id": str(worker_id) if worker_id else None,
        "date": date, "shift_code": shift_code,
        "page": page, "size": size,
    })
    return {"items": items, "total": total, "page": page, "size": size}


@router.post("/shift-assignments", status_code=201)
def create_assignment(body: dict, user=Depends(require_permission("attendance.manage")), db=Depends(get_db)):
    result = att_svc.create_shift_assignment(db, body, user)
    db.commit()
    return result


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------

@router.post("/attendance/check-in", status_code=200)
def check_in(body: dict, user=Depends(require_permission("attendance.self")), db=Depends(get_db)):
    result = att_svc.check_in(db, body, user)
    db.commit()
    return result


@router.post("/attendance/check-out", status_code=200)
def check_out(body: dict, user=Depends(require_permission("attendance.self")), db=Depends(get_db)):
    result = att_svc.check_out(db, body, user)
    db.commit()
    return result


@router.get("/attendance")
def list_attendance(
    worker_id: uuid.UUID | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user=Depends(require_permission("attendance.view")),
    db=Depends(get_db),
):
    items, total = att_svc.list_attendance(db, {
        "worker_id": str(worker_id) if worker_id else None,
        "date_from": date_from, "date_to": date_to,
        "status": status, "page": page, "size": size,
    })
    return {"items": items, "total": total, "page": page, "size": size}


@router.patch("/attendance/{id}")
def correct_attendance(
    id: uuid.UUID, body: dict,
    user=Depends(require_permission("attendance.manage")), db=Depends(get_db),
):
    result = att_svc.correct_attendance(db, id, body, user)
    db.commit()
    return result


# ---------------------------------------------------------------------------
# Wage advances
# ---------------------------------------------------------------------------

@router.get("/wage-advances")
def list_advances(
    worker_id: uuid.UUID | None = Query(None),
    user=Depends(require_permission("payroll.manage")),
    db=Depends(get_db),
):
    return {"items": pay_svc.list_wage_advances(db, worker_id=worker_id)}


@router.post("/wage-advances", status_code=201)
def create_advance(body: dict, user=Depends(require_permission("payroll.manage")), db=Depends(get_db)):
    result = pay_svc.create_wage_advance(db, body, user)
    db.commit()
    return result


# ---------------------------------------------------------------------------
# Payroll runs
# ---------------------------------------------------------------------------

@router.get("/payroll/runs")
def list_payroll_runs(user=Depends(require_permission("payroll.view")), db=Depends(get_db)):
    return {"items": pay_svc.list_payroll_runs(db)}


@router.post("/payroll/runs", status_code=201)
def create_payroll_run(body: dict, user=Depends(require_permission("payroll.manage")), db=Depends(get_db)):
    result = pay_svc.compute_payroll_draft(db, body, user)
    db.commit()
    return result


@router.get("/payroll/runs/{id}")
def get_payroll_run(id: uuid.UUID, user=Depends(require_permission("payroll.view")), db=Depends(get_db)):
    return pay_svc.get_payroll_run(db, id)


@router.post("/payroll/runs/{id}/approve")
def approve_payroll(id: uuid.UUID, user=Depends(require_permission("payroll.approve")), db=Depends(get_db)):
    result = pay_svc.approve_payroll(db, id, user)
    db.commit()
    return result


@router.post("/payroll/runs/{id}/mark-paid")
def mark_payroll_paid(id: uuid.UUID, user=Depends(require_permission("payroll.manage")), db=Depends(get_db)):
    result = pay_svc.mark_paid(db, id, user)
    db.commit()
    return result


@router.get("/payroll/runs/{id}/payslips.pdf")
def payslips_pdf(id: uuid.UUID, user=Depends(require_permission("payroll.view")), db=Depends(get_db)):
    from app.pdf import payslip as pdf_mod

    run = pay_svc.get_payroll_run(db, id)
    payslip_list = []
    for l in run["lines"]:
        try:
            pdata = pay_svc.get_payslip_data(db, id, uuid.UUID(l["worker_id"]))
            payslip_list.append(pdata)
        except Exception:
            pass
    pdf_bytes = pdf_mod.generate_batch(payslip_list)
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=payslips-{run['period']}.pdf"},
    )


# ---------------------------------------------------------------------------
# serializers
# ---------------------------------------------------------------------------

def _worker_out(r) -> dict:
    return {
        "id": str(r.id), "code": r.code, "name": r.name, "phone": r.phone,
        "department": r.department, "skill_stages": r.skill_stages or [],
        "wage_type": r.wage_type, "wage_rate_paise": r.wage_rate_paise,
        "piece_rate_paise_per_m": r.piece_rate_paise_per_m,
        "default_shift": r.default_shift, "overtime_willing": r.overtime_willing,
        "joined_on": r.joined_on.isoformat() if r.joined_on else None,
        "is_active": r.is_active, "preferred_language": r.preferred_language,
        "created_at": r.created_at.isoformat(),
    }


def _shift_out(r) -> dict:
    return {
        "code": r.code, "name": r.name,
        "start_time": r.start_time.isoformat(), "end_time": r.end_time.isoformat(),
        "break_minutes": r.break_minutes, "is_overtime": r.is_overtime,
        "created_at": r.created_at.isoformat(),
    }
