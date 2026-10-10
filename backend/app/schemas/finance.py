from __future__ import annotations
import datetime as dt
import uuid
from pydantic import BaseModel


class InvoiceOut(BaseModel):
    id: uuid.UUID
    code: str
    buyer_id: uuid.UUID
    order_id: uuid.UUID
    amount_paise: int
    balance_paise: int
    due_date: dt.date
    status: str
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class PaymentOut(BaseModel):
    id: uuid.UUID
    code: str
    invoice_id: uuid.UUID
    amount_paise: int
    paid_at: dt.datetime
    method: str
    created_at: dt.datetime

    model_config = {"from_attributes": True}
