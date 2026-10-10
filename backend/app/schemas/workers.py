from __future__ import annotations
import datetime as dt
import uuid
from pydantic import BaseModel


class WorkerOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    role: str
    phone: str | None = None
    is_active: bool
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class AttendanceOut(BaseModel):
    id: uuid.UUID
    worker_id: uuid.UUID
    date: dt.date
    shift_code: str
    status: str
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class PayrollRunOut(BaseModel):
    id: uuid.UUID
    month: str
    status: str
    total_paise: int
    created_at: dt.datetime

    model_config = {"from_attributes": True}
