"""Machine simulator endpoints — owned by Lane B; only mounted when DEMO_MODE=true."""
from fastapi import APIRouter, Depends
from app.deps import require_permission

router = APIRouter()


@router.post("/simulator/machines/{id}/emit")
def simulator_emit(id: str, user=Depends(require_permission("ripple.manage"))):
    raise NotImplementedError