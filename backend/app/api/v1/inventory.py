from fastapi import APIRouter, Depends
from app.deps import require_permission

router = APIRouter()


@router.get("/suppliers")
def list_suppliers(user=Depends(require_permission("suppliers.view"))):
    raise NotImplementedError


@router.post("/suppliers")
def create_supplier(user=Depends(require_permission("suppliers.manage"))):
    raise NotImplementedError


@router.get("/suppliers/{id}")
def get_supplier(id: str, user=Depends(require_permission("suppliers.view"))):
    raise NotImplementedError


@router.patch("/suppliers/{id}")
def update_supplier(id: str, user=Depends(require_permission("suppliers.manage"))):
    raise NotImplementedError


@router.get("/suppliers/{id}/history")
def supplier_history(id: str, user=Depends(require_permission("suppliers.view"))):
    raise NotImplementedError


@router.get("/yarn-types")
def list_yarn_types(user=Depends(require_permission("inventory.view"))):
    raise NotImplementedError


@router.post("/yarn-types")
def create_yarn_type(user=Depends(require_permission("inventory.manage"))):
    raise NotImplementedError


@router.get("/yarn-types/{id}")
def get_yarn_type(id: str, user=Depends(require_permission("inventory.view"))):
    raise NotImplementedError


@router.patch("/yarn-types/{id}")
def update_yarn_type(id: str, user=Depends(require_permission("inventory.manage"))):
    raise NotImplementedError


@router.get("/inventory/stock")
def get_stock(user=Depends(require_permission("inventory.view"))):
    raise NotImplementedError


@router.get("/inventory/batches")
def list_batches(user=Depends(require_permission("inventory.view"))):
    raise NotImplementedError


@router.get("/inventory/batches/{id}")
def get_batch(id: str, user=Depends(require_permission("inventory.view"))):
    raise NotImplementedError


@router.post("/inventory/receipts")
def receive_stock(user=Depends(require_permission("inventory.receive"))):
    raise NotImplementedError


@router.post("/inventory/issues")
def issue_stock(user=Depends(require_permission("inventory.issue"))):
    raise NotImplementedError


@router.post("/inventory/returns")
def return_stock(user=Depends(require_permission("inventory.issue"))):
    raise NotImplementedError


@router.post("/inventory/adjustments")
def adjust_stock(user=Depends(require_permission("inventory.adjust"))):
    raise NotImplementedError


@router.get("/inventory/alerts")
def inventory_alerts(user=Depends(require_permission("inventory.view"))):
    raise NotImplementedError


@router.get("/inventory/purchase-needs")
def purchase_needs(user=Depends(require_permission("inventory.view"))):
    raise NotImplementedError


@router.get("/purchase-orders")
def list_pos(user=Depends(require_permission("purchasing.manage"))):
    raise NotImplementedError


@router.post("/purchase-orders")
def create_po(user=Depends(require_permission("purchasing.manage"))):
    raise NotImplementedError


@router.get("/purchase-orders/{id}")
def get_po(id: str, user=Depends(require_permission("purchasing.manage"))):
    raise NotImplementedError


@router.patch("/purchase-orders/{id}")
def update_po(id: str, user=Depends(require_permission("purchasing.manage"))):
    raise NotImplementedError