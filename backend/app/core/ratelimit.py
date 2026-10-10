from __future__ import annotations
import time
import threading
from collections import deque
from fastapi import Request
from app.core.errors import AppError

_windows: dict[str, deque] = {}
_lock = threading.Lock()


def check_rate_limit(key: str, max_calls: int = 5, window_seconds: int = 60) -> None:
    """In-memory sliding window rate limiter. Raises AppError if exceeded."""
    now = time.monotonic()
    with _lock:
        if key not in _windows:
            _windows[key] = deque()
        dq = _windows[key]
        # Evict old entries
        while dq and dq[0] < now - window_seconds:
            dq.popleft()
        if len(dq) >= max_calls:
            raise AppError("RATE_LIMITED", "Too many requests. Please wait before retrying.")
        dq.append(now)


def rate_limit_login(request: Request, identifier: str) -> None:
    ip = request.client.host if request.client else "unknown"
    key = f"login:{ip}:{identifier}"
    check_rate_limit(key, max_calls=5, window_seconds=60)