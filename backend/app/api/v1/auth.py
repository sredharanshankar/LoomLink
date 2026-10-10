from __future__ import annotations
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.deps import get_db
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


def _get_user_by_employee_code(db: Session, code: str):
    return db.execute(
        text("SELECT id, password_hash, pin_hash, role, is_active FROM users WHERE employee_code = :code"),
        {"code": code},
    ).fetchone()


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
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
    return TokenResponse(access_token=access_token, refresh_token=raw_rt, expires_at=expires_at)


@router.post("/pin-login", response_model=TokenResponse)
def pin_login(body: PinLoginRequest, request: Request, db: Session = Depends(get_db)):
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
    return TokenResponse(access_token=access_token, refresh_token=raw_rt, expires_at=expires_at)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    hashed = hash_refresh_token(body.refresh_token)
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
    return TokenResponse(access_token=access_token, refresh_token=raw_rt, expires_at=expires_at)


@router.post("/logout")
def logout(body: RefreshRequest, db: Session = Depends(get_db)):
    hashed = hash_refresh_token(body.refresh_token)
    db.execute(
        text("UPDATE refresh_tokens SET revoked_at = :now WHERE token_hash = :th AND revoked_at IS NULL"),
        {"now": now().replace(tzinfo=None), "th": hashed},
    )
    return {"ok": True}