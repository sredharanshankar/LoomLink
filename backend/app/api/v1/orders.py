from fastapi import APIRouter, Depends
from app.deps import require_permission

router = APIRouter()


@router.get("/buyers")
def list_buyers(user=Depends(require_permission("buyers.view"))):
    raise NotImplementedError


@router.post("/buyers")
def create_buyer(user=Depends(require_permission("buyers.manage"))):
    raise NotImplementedError


@router.get("/buyers/{id}")
def get_buyer(id: str, user=Depends(require_permission("buyers.view"))):
    raise NotImplementedError


@router.patch("/buyers/{id}")
def update_buyer(id: str, user=Depends(require_permission("buyers.manage"))):
    raise NotImplementedError


@router.get("/buyers/{id}/outstanding")
def buyer_outstanding(id: str, user=Depends(require_permission("finance.view"))):
    raise NotImplementedError


@router.get("/fabric-types")
def list_fabric_types(user=Depends(require_permission("orders.view"))):
    raise NotImplementedError


@router.post("/fabric-types")
def create_fabric_type(user=Depends(require_permission("orders.manage"))):
    raise NotImplementedError


@router.get("/fabric-types/{id}")
def get_fabric_type(id: str, user=Depends(require_permission("orders.view"))):
    raise NotImplementedError


@router.patch("/fabric-types/{id}")
def update_fabric_type(id: str, user=Depends(require_permission("orders.manage"))):
    raise NotImplementedError


@router.get("/route-templates")
def list_route_templates(user=Depends(require_permission("orders.view"))):
    raise NotImplementedError


@router.post("/route-templates")
def create_route_template(user=Depends(require_permission("orders.manage"))):
    raise NotImplementedError


@router.get("/orders")
def list_orders(user=Depends(require_permission("orders.view"))):
    raise NotImplementedError


@router.post("/orders")
def create_order(user=Depends(require_permission("orders.manage"))):
    raise NotImplementedError


@router.get("/orders/lookup")
def lookup_orders(user=Depends(require_permission("orders.lookup"))):
    raise NotImplementedError


@router.get("/orders/{id}")
def get_order(id: str, user=Depends(require_permission("orders.view"))):
    raise NotImplementedError


@router.patch("/orders/{id}")
def update_order(id: str, user=Depends(require_permission("orders.manage"))):
    raise NotImplementedError


@router.post("/orders/feasibility")
def check_feasibility(user=Depends(require_permission("orders.view"))):
    raise NotImplementedError


@router.post("/orders/{id}/confirm")
def confirm_order(id: str, user=Depends(require_permission("orders.manage"))):
    raise NotImplementedError


@router.post("/orders/{id}/cancel")
def cancel_order(id: str, user=Depends(require_permission("orders.manage"))):
    raise NotImplementedError


@router.get("/orders/{id}/timeline")
def order_timeline(id: str, user=Depends(require_permission("orders.view"))):
    raise NotImplementedError