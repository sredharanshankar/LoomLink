from __future__ import annotations
import os
import secrets
import datetime as dt
import hashlib
import jwt
import bcrypt
from typing import Any
from app.config import get_settings


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def hash_pin(pin: str) -> str:
    return bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()


def verify_pin(pin: str, hashed: str) -> bool:
    return verify_password(pin, hashed)


def create_access_token(user_id: str, role: str) -> tuple[str, dt.datetime]:
    settings = get_settings()
    now = dt.datetime.now(dt.timezone.utc)
    exp = now + dt.timedelta(minutes=settings.access_token_minutes)
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": secrets.token_hex(16),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token, exp


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


def generate_refresh_token() -> tuple[str, str]:
    """Return (raw_token, hashed_token). Store the hash; send the raw."""
    raw = secrets.token_bytes(48).hex()
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def generate_tracking_token() -> str:
    return secrets.token_urlsafe(24)
