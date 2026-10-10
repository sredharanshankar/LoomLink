from __future__ import annotations
import datetime as dt
import uuid
from pydantic import BaseModel


class InspectionOut(BaseModel):
    id: uuid.UUID
    roll_id: uuid.UUID
    inspector_id: uuid.UUID
    result: str
    defect_count: int
    passed_length_cm: int
    notes: str | None = None
    inspected_at: dt.datetime

    model_config = {"from_attributes": True}
