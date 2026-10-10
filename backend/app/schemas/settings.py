from __future__ import annotations
from pydantic import BaseModel, ConfigDict


class MillSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mill_name: str
    gst_number: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    phone: str | None = None
    email: str | None = None
    bank_name: str | None = None
    bank_account: str | None = None
    bank_ifsc: str | None = None


class MillSettingsUpdate(BaseModel):
    mill_name: str | None = None
    gst_number: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    phone: str | None = None
    email: str | None = None
    bank_name: str | None = None
    bank_account: str | None = None
    bank_ifsc: str | None = None