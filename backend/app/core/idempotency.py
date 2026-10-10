from __future__ import annotations
import datetime as dt
import json
from functools import wraps
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session


IDEMPOTENCY_TTL_HOURS = 24


async def idempotency_middleware(request: Request, call_next: Callable) -> Response:
    """Middleware stub; actual idempotency is handled via the `idempotent` dependency."""
    return await call_next(request)


class IdempotencyKey:
    """FastAPI dependency that replays responses for duplicate idempotency keys."""

    def __init__(self, request: Request):
        self.key = request.headers.get("Idempotency-Key")
        self.request = request

    async def check(self, db: Session, user_id: str) -> JSONResponse | None:
        if not self.key:
            return None
        from sqlalchemy import text

        endpoint = f"{self.request.method}:{self.request.url.path}"
        row = db.execute(
            text(
                "SELECT status_code, response_body FROM idempotency_keys "
                "WHERE key = :key AND user_id = :uid AND endpoint = :ep"
            ),
            {"key": self.key, "uid": user_id, "ep": endpoint},
        ).fetchone()
        if row:
            return JSONResponse(status_code=row[0], content=json.loads(row[1]))
        return None

    def store(self, db: Session, user_id: str, status_code: int, body: dict) -> None:
        if not self.key:
            return
        from sqlalchemy import text

        endpoint = f"{self.request.method}:{self.request.url.path}"
        expires = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=IDEMPOTENCY_TTL_HOURS)
        db.execute(
            text(
                "INSERT INTO idempotency_keys (key, user_id, endpoint, status_code, response_body, created_at, expires_at) "
                "VALUES (:key, :uid, :ep, :sc, :body, :now, :exp) "
                "ON CONFLICT (key, user_id, endpoint) DO NOTHING"
            ),
            {
                "key": self.key,
                "uid": user_id,
                "ep": endpoint,
                "sc": status_code,
                "body": json.dumps(body),
                "now": dt.datetime.now(dt.timezone.utc),
                "exp": expires,
            },
        )