from __future__ import annotations
import datetime as dt
import uuid
from pydantic import BaseModel


class BuyerOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    contact_person: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    email: str | None = None
    payment_terms_days: int
    is_active: bool
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class FabricTypeOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    construction: str | None = None
    width_cm: int
    gsm: int | None = None
    colour: str
    yarn_type_id: uuid.UUID
    default_price_paise_per_m: int
    is_active: bool
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: uuid.UUID
    code: str
    buyer_id: uuid.UUID
    fabric_type_id: uuid.UUID
    quantity_cm: int
    price_paise_per_m: int
    due_date: dt.date
    status: str
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class JobOut(BaseModel):
    id: uuid.UUID
    code: str
    order_id: uuid.UUID
    stage: str
    status: str
    qty_cm: int
    created_at: dt.datetime

    model_config = {"from_attributes": True}
