from __future__ import annotations
import datetime as dt
import uuid
from pydantic import BaseModel


class SupplierOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    gstin: str | None = None
    payment_terms_days: int
    is_active: bool
    created_at: dt.datetime

    model_config = {"from_attributes": True}
