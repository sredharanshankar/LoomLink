from fastapi import APIRouter, Depends
from app.deps import require_permission

router = APIRouter()


@router.get("/workers")
def list_workers(user=Depends(require_permission("workers.view"))):
    raise NotImplementedError


@router.post("/workers")
def create_worker(user=Depends(require_permission("workers.manage"))):
    raise NotImplementedError


@router.get("/workers/{id}")
def get_worker(id: str, user=Depends(require_permission("workers.view"))):
    raise NotImplementedError


@router.patch("/workers/{id}")
def update_worker(id: str, user=Depends(require_permission("workers.manage"))):
    raise NotImplementedError


@router.get("/shifts")
def list_shifts(user=Depends(require_permission("workers.view"))):
    raise NotImplementedError


@router.post("/shifts")
def create_shift(user=Depends(require_permission("workers.manage"))):
    raise NotImplementedError


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