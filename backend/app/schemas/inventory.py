from __future__ import annotations
import datetime as dt
import uuid
from pydantic import BaseModel


class YarnTypeOut(BaseModel):
    id: uuid.UUID
    code: str
    material: str
    count_label: str
    colour: str
    colour_hex: str | None = None
    reorder_level_g: int
    standard_rate_paise_per_kg: int
    is_active: bool
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class YarnBatchOut(BaseModel):
    id: uuid.UUID
    code: str
    yarn_type_id: uuid.UUID
    supplier_id: uuid.UUID
    qty_g: int
    remaining_g: int
    rate_paise_per_kg: int
    received_at: dt.datetime

    model_config = {"from_attributes": True}


class StockRowOut(BaseModel):
    yarn_type_id: uuid.UUID
    yarn_type_code: str
    material: str
    colour: str
    total_g: int
    reserved_g: int
    available_g: int
    reorder_level_g: int
    below_reorder: bool
