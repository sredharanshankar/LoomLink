from fastapi import APIRouter, Depends
from app.deps import require_permission

router = APIRouter()


@router.post("/rolls")
def create_rolls(user=Depends(require_permission("rolls.create"))):
    raise NotImplementedError


@router.get("/rolls")
def list_rolls(user=Depends(require_permission("quality.view"))):
    raise NotImplementedError


@router.get("/rolls/{id}")
def get_roll(id: str, user=Depends(require_permission("quality.view"))):
    raise NotImplementedError


@router.post("/rolls/{id}/inspections")
def inspect_roll(id: str, user=Depends(require_permission("quality.inspect"))):
    raise NotImplementedError


@router.post("/rolls/{id}/rework-complete")
def rework_complete(id: str, user=Depends(require_permission("quality.inspect"))):
    raise NotImplementedError


@router.get("/quality/queues")
def quality_queues(user=Depends(require_permission("quality.view"))):
    raise NotImplementedError


@router.get("/quality/defect-patterns")
def defect_patterns(user=Depends(require_permission("quality.view"))):
    raise NotImplementedError


@router.get("/rolls/{id}/passport")
def roll_passport(id: str, user=Depends(require_permission("rolls.passport"))):
    raise NotImplementedError