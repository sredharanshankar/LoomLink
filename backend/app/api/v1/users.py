from fastapi import APIRouter, Depends
from app.deps import require_permission

router = APIRouter()


@router.get("/users")
def list_users(user=Depends(require_permission("users.manage"))):
    raise NotImplementedError


@router.post("/users")
def create_user(user=Depends(require_permission("users.manage"))):
    raise NotImplementedError


@router.patch("/users/{id}")
def update_user(id: str, user=Depends(require_permission("users.manage"))):
    raise NotImplementedError


@router.get("/audit")
def get_audit(user=Depends(require_permission("audit.view"))):
    raise NotImplementedError