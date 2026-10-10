from __future__ import annotations
import logging
import uuid
from typing import Any
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

_STATUS_MAP: dict[str, int] = {
    "VALIDATION_ERROR": 422,
    "UNAUTHENTICATED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "CONFLICT": 409,
    "INVALID_STATE": 409,
    "INSUFFICIENT_STOCK": 409,
    "MACHINE_BUSY": 409,
    "MACHINE_INCOMPATIBLE": 422,
    "NOT_ON_SHIFT": 403,
    "ROLL_NOT_PASSED": 409,
    "ROLL_ALREADY_DISPATCHED": 409,
    "ROLL_WRONG_ORDER": 409,
    "DUPLICATE_REFERENCE": 409,
    "OVER_ALLOCATION": 409,
    "STALE_SNAPSHOT": 409,
    "RATE_LIMITED": 429,
    "DEMO_ONLY": 403,
    "NOT_IMPLEMENTED": 501,
}


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status or _STATUS_MAP.get(code, 400)
        self.status = self.status_code  # alias for FastAPI response_model
        self.details = details or {}


def _error_body(code: str, message: str, details: dict | None = None) -> dict:
    body: dict = {"code": code, "message": message}
    if details:
        body["details"] = details
    return {"error": body}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status,
            content=_error_body(exc.code, exc.message, exc.details or None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_error_body("VALIDATION_ERROR", "Request validation failed", {"fields": details}),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code_map = {401: "UNAUTHENTICATED", 403: "FORBIDDEN", 404: "NOT_FOUND"}
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(code, str(exc.detail)),
        )

    @app.exception_handler(NotImplementedError)
    async def not_implemented_handler(request: Request, exc: NotImplementedError) -> JSONResponse:
        return JSONResponse(
            status_code=501,
            content=_error_body("NOT_IMPLEMENTED", str(exc) or "This endpoint is not yet implemented."),
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = str(uuid.uuid4())
        logger.exception("Unhandled error [%s]", correlation_id)
        from app.config import get_settings
        prod = get_settings().app_env == "production"
        message = "An unexpected error occurred." if prod else str(exc)
        return JSONResponse(
            status_code=500,
            content=_error_body("INTERNAL_ERROR", message, {"correlation_id": correlation_id}),
        )
