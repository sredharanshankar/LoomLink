from __future__ import annotations
from fastapi import APIRouter, Depends, Request, Response, Body
from sqlalchemy.orm import Session
from app.deps import get_db, require_permission
from app.core.errors import AppError
from app.core.security import (
    verify_password, verify_pin, create_access_token,
    generate_refresh_token, hash_refresh_token, decode_access_token,
)
from app.core.ratelimit import rate_limit_login
from app.core.time import now
from app.schemas.auth import LoginRequest, PinLoginRequest, TokenResponse, RefreshRequest
from sqlalchemy import text

router = APIRouter()

_COOKIE = "ll_refresh"
_COOKIE_PATH = "/api/v1/auth"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        path=_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_COOKIE, path=_COOKIE_PATH)


def _get_user_by_employee_code(db: Session, code: str):
    return db.execute(
        text("SELECT id, password_hash, pin_hash, role, is_active FROM users WHERE employee_code = :code"),
        {"code": code},
    ).fetchone()


@router.get("/me")
def get_me(user=Depends(require_permission("")), db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT id, employee_code, name, email, phone, role, preferred_language, is_active, last_login_at FROM users WHERE id = :id"),
        {"id": str(user["sub"])},
    ).fetchone()
    if row is None:
        raise AppError("NOT_FOUND", "User not found.")
    return {
        "id": str(row.id), "employee_code": row.employee_code, "name": row.name,
        "email": row.email, "phone": row.phone, "role": row.role,
        "preferred_language": row.preferred_language, "is_active": row.is_active,
        "last_login_at": row.last_login_at.isoformat() if row.last_login_at else None,
    }


@router.patch("/me")
def update_me(body: dict, user=Depends(require_permission("")), db: Session = Depends(get_db)):
    from app.core.time import now as _now
    allowed = {k: v for k, v in body.items() if k in ("name", "email", "phone", "preferred_language")}
    if not allowed:
        raise AppError("VALIDATION_ERROR", "No updatable fields provided.")
    sets = ", ".join(f"{k} = :{k}" for k in allowed)
    allowed["id"] = str(user["sub"])
    allowed["now"] = _now()
    db.execute(text(f"UPDATE users SET {sets}, updated_at = :now WHERE id = :id"), allowed)
    db.commit()
    return {"ok": True}


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    rate_limit_login(request, body.employee_code)
    user = _get_user_by_employee_code(db, body.employee_code)
    if not user or not user.is_active or not verify_password(body.password, user.password_hash):
        raise AppError("UNAUTHENTICATED", "Invalid credentials.")
    access_token, expires_at = create_access_token(str(user.id), user.role)
    raw_rt, hashed_rt = generate_refresh_token()
    db.execute(
        text(
            "INSERT INTO refresh_tokens (user_id, token_hash, expires_at, created_at) "
            "VALUES (:uid, :th, :exp, :now)"
        ),
        {
            "uid": user.id,
            "th": hashed_rt,
            "exp": now().replace(tzinfo=None),
            "now": now().replace(tzinfo=None),
        },
    )
    _set_refresh_cookie(response, raw_rt)
    return TokenResponse(access_token=access_token, refresh_token=raw_rt, expires_at=expires_at)


@router.post("/pin-login", response_model=TokenResponse)
def pin_login(body: PinLoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    rate_limit_login(request, body.employee_code)
    user = _get_user_by_employee_code(db, body.employee_code)
    if not user or not user.is_active or not user.pin_hash or not verify_pin(body.pin, user.pin_hash):
        raise AppError("UNAUTHENTICATED", "Invalid credentials.")
    access_token, expires_at = create_access_token(str(user.id), user.role)
    raw_rt, hashed_rt = generate_refresh_token()
    db.execute(
        text(
            "INSERT INTO refresh_tokens (user_id, token_hash, expires_at, created_at) "
            "VALUES (:uid, :th, :exp, :now)"
        ),
        {
            "uid": user.id,
            "th": hashed_rt,
            "exp": now().replace(tzinfo=None),
            "now": now().replace(tzinfo=None),
        },
    )
    _set_refresh_cookie(response, raw_rt)
    return TokenResponse(access_token=access_token, refresh_token=raw_rt, expires_at=expires_at)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request,
    response: Response,
    body: RefreshRequest | None = Body(default=None),
    db: Session = Depends(get_db),
):
    token = (body.refresh_token if body and body.refresh_token else None) or request.cookies.get(_COOKIE)
    if not token:
        raise AppError("UNAUTHENTICATED", "No refresh token provided.")
    hashed = hash_refresh_token(token)
    row = db.execute(
        text(
            "SELECT rt.id, rt.user_id, rt.expires_at, u.role, u.is_active "
            "FROM refresh_tokens rt JOIN users u ON u.id = rt.user_id "
            "WHERE rt.token_hash = :th AND rt.revoked_at IS NULL"
        ),
        {"th": hashed},
    ).fetchone()
    if not row or not row.is_active:
        raise AppError("UNAUTHENTICATED", "Invalid or expired refresh token.")
    db.execute(
        text("UPDATE refresh_tokens SET revoked_at = :now WHERE id = :id"),
        {"now": now().replace(tzinfo=None), "id": row.id},
    )
    access_token, expires_at = create_access_token(str(row.user_id), row.role)
    raw_rt, hashed_rt = generate_refresh_token()
    db.execute(
        text(
            "INSERT INTO refresh_tokens (user_id, token_hash, expires_at, created_at) "
            "VALUES (:uid, :th, :exp, :now)"
        ),
        {
            "uid": row.user_id,
            "th": hashed_rt,
            "exp": now().replace(tzinfo=None),
            "now": now().replace(tzinfo=None),
        },
    )
    _set_refresh_cookie(response, raw_rt)
    return TokenResponse(access_token=access_token, refresh_token=raw_rt, expires_at=expires_at)


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    body: RefreshRequest | None = Body(default=None),
    db: Session = Depends(get_db),
):
    token = (body.refresh_token if body and body.refresh_token else None) or request.cookies.get(_COOKIE)
    if token:
        hashed = hash_refresh_token(token)
        db.execute(
            text("UPDATE refresh_tokens SET revoked_at = :now WHERE token_hash = :th AND revoked_at IS NULL"),
            {"now": now().replace(tzinfo=None), "th": hashed},
        )
    _clear_refresh_cookie(response)
    return {"ok": True}