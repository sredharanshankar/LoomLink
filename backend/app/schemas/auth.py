from __future__ import annotations
import datetime as dt
from pydantic import BaseModel, field_validator


class LoginRequest(BaseModel):
    employee_code: str
    password: str


class PinLoginRequest(BaseModel):
    employee_code: str
    pin: str

    @field_validator("pin")
    @classmethod
    def validate_pin(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 6:
            raise ValueError("PIN must be exactly 6 digits.")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: dt.datetime
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str