from __future__ import annotations
import datetime as dt
import uuid
from pydantic import BaseModel


class DispatchOut(BaseModel):
    id: uuid.UUID
    code: str
    order_id: uuid.UUID
    dispatched_at: dt.datetime
    vehicle_number: str | None = None
    notes: str | None = None
    created_at: dt.datetime

    model_config = {"from_attributes": True}
