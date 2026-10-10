from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.deps import get_db, current_user, require_permission
from app.core.errors import AppError
from app.schemas.settings import MillSettingsRead, MillSettingsUpdate

router = APIRouter()


@router.get("", response_model=MillSettingsRead)
def get_settings(db: Session = Depends(get_db), user=Depends(require_permission("settings.view"))):
    row = db.execute(text("SELECT * FROM mill_settings LIMIT 1")).fetchone()
    if not row:
        raise AppError("NOT_FOUND", "Mill settings not configured.")
    return MillSettingsRead.model_validate(dict(row._mapping))


@router.patch("", response_model=MillSettingsRead)
def update_settings(
    body: MillSettingsUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_permission("settings.edit")),
):
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise AppError("VALIDATION_ERROR", "No fields to update.")
    sets = ", ".join(f"{k} = :{k}" for k in data)
    db.execute(text(f"UPDATE mill_settings SET {sets}"), data)
    row = db.execute(text("SELECT * FROM mill_settings LIMIT 1")).fetchone()
    return MillSettingsRead.model_validate(dict(row._mapping))