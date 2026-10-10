from fastapi import APIRouter, Depends
from app.deps import require_permission

router = APIRouter()


@router.get("/dispatch/finished-stock")
def finished_stock(user=Depends(require_permission("dispatch.view"))):
    raise NotImplementedError


@router.get("/dispatch/aged-stock")
def aged_stock(user=Depends(require_permission("dispatch.view"))):
    raise NotImplementedError


@router.get("/dispatches")
def list_dispatches(user=Depends(require_permission("dispatch.view"))):
    raise NotImplementedError


@router.post("/dispatches")
def create_dispatch(user=Depends(require_permission("dispatch.manage"))):
    raise NotImplementedError


@router.get("/dispatches/{id}")
def get_dispatch(id: str, user=Depends(require_permission("dispatch.view"))):
    raise NotImplementedError


@router.post("/dispatches/{id}/scan")
def scan_dispatch(id: str, user=Depends(require_permission("dispatch.manage"))):
    raise NotImplementedError


@router.delete("/dispatches/{id}/items/{roll_id}")
def remove_dispatch_item(id: str, roll_id: str, user=Depends(require_permission("dispatch.manage"))):
    raise NotImplementedError


@router.post("/dispatches/{id}/confirm")
def confirm_dispatch(id: str, user=Depends(require_permission("dispatch.manage"))):
    raise NotImplementedError


@router.post("/dispatches/{id}/status")
def update_dispatch_status(id: str, user=Depends(require_permission("dispatch.manage"))):
    raise NotImplementedError


@router.get("/dispatches/{id}/packing-list.pdf")
def packing_list(id: str, user=Depends(require_permission("dispatch.view"))):
    raise NotImplementedError