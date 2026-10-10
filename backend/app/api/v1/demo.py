"""Demo convenience endpoints — only mounted when DEMO_MODE=true."""
from fastapi import APIRouter, Depends
from app.deps import require_permission

router = APIRouter()


@router.post("/demo/reset")
def demo_reset(user=Depends(require_permission("demo.reset"))):
    raise NotImplementedError