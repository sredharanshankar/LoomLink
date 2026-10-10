from fastapi import APIRouter, Depends
from app.deps import require_permission

router = APIRouter()


@router.get("/invoices")
def list_invoices(user=Depends(require_permission("finance.view"))):
    raise NotImplementedError


@router.get("/invoices/{id}")
def get_invoice(id: str, user=Depends(require_permission("finance.view"))):
    raise NotImplementedError


@router.get("/invoices/{id}.pdf")
def invoice_pdf(id: str, user=Depends(require_permission("finance.view"))):
    raise NotImplementedError


@router.post("/payments")
def record_payment(user=Depends(require_permission("finance.record_payment"))):
    raise NotImplementedError


@router.get("/supplier-bills")
def list_bills(user=Depends(require_permission("finance.view"))):
    raise NotImplementedError


@router.post("/supplier-bills")
def create_bill(user=Depends(require_permission("finance.manage"))):
    raise NotImplementedError


@router.get("/supplier-bills/{id}")
def get_bill(id: str, user=Depends(require_permission("finance.view"))):
    raise NotImplementedError


@router.post("/supplier-bills/{id}/payments")
def pay_bill(id: str, user=Depends(require_permission("finance.manage"))):
    raise NotImplementedError


@router.get("/expenses")
def list_expenses(user=Depends(require_permission("finance.view"))):
    raise NotImplementedError


@router.post("/expenses")
def create_expense(user=Depends(require_permission("finance.manage"))):
    raise NotImplementedError


@router.get("/finance/orders/{id}/cost")
def order_cost(id: str, user=Depends(require_permission("finance.view_costs"))):
    raise NotImplementedError


@router.get("/finance/rolls/{id}/cost")
def roll_cost(id: str, user=Depends(require_permission("finance.view_costs"))):
    raise NotImplementedError


@router.get("/finance/month-close")
def month_close(user=Depends(require_permission("finance.view"))):
    raise NotImplementedError


@router.get("/finance/receivables")
def receivables(user=Depends(require_permission("finance.view"))):
    raise NotImplementedError


@router.get("/finance/payables")
def payables(user=Depends(require_permission("finance.view"))):
    raise NotImplementedError