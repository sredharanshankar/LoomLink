from __future__ import annotations
import datetime as dt
import uuid
from pydantic import BaseModel


class MachineOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    stage: str
    is_active: bool
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class RollOut(BaseModel):
    id: uuid.UUID
    code: str
    order_id: uuid.UUID
    job_id: uuid.UUID
    length_cm: int
    status: str
    created_at: dt.datetime

    model_config = {"from_attributes": True}
