"""A-M10: Users and audit-log router."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.deps import get_db, require_permission
from app.core.errors import AppError
from app.core.time import now

router = APIRouter()


def _user_out(row) -> dict:
    return {
        "id": str(row.id), "employee_code": row.employee_code, "name": row.name,
        "email": row.email, "phone": row.phone, "role": row.role,
        "preferred_language": row.preferred_language, "is_active": row.is_active,
        "worker_id": str(row.worker_id) if row.worker_id else None,
        "buyer_id": str(row.buyer_id) if row.buyer_id else None,
        "created_at": row.created_at.isoformat(),
    }


@router.get("/users")
def list_users(
    role: str | None = Query(None),
    active_only: bool = Query(True),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user=Depends(require_permission("users.manage")),
    db: Session = Depends(get_db),
):
    where = "WHERE 1=1"
    params: dict = {}
    if role:
        where += " AND role = :role"
        params["role"] = role
    if active_only:
        where += " AND is_active = true"
    total = db.execute(text(f"SELECT COUNT(*) FROM users {where}"), params).scalar()
    offset = (page - 1) * size
    params["lim"] = size
    params["off"] = offset
    rows = db.execute(
        text(
            f"SELECT id, employee_code, name, email, phone, role, preferred_language, "
            f"is_active, worker_id, buyer_id, created_at FROM users {where} "
            f"ORDER BY created_at DESC LIMIT :lim OFFSET :off"
        ),
        params,
    ).fetchall()
    return {"items": [_user_out(r) for r in rows], "total": total, "page": page, "size": size}


@router.post("/users", status_code=201)
def create_user(
    body: dict,
    user=Depends(require_permission("users.manage")),
    db: Session = Depends(get_db),
):
    from app.core.security import hash_password, hash_pin

    if not body.get("employee_code") or not body.get("name") or not body.get("role"):
        raise AppError("VALIDATION_ERROR", "employee_code, name, role required.")

    existing = db.execute(
        text("SELECT id FROM users WHERE employee_code = :ec"),
        {"ec": body["employee_code"]},
    ).fetchone()
    if existing:
        raise AppError("DUPLICATE", "employee_code already in use.")

    uid = uuid.uuid4()
    ts = now()
    pw_hash = hash_password(body["password"]) if body.get("password") else None
    pin_hash = hash_pin(body["pin"]) if body.get("pin") else None

    db.execute(
        text(
            "INSERT INTO users (id, employee_code, name, email, phone, role, password_hash, pin_hash, "
            "preferred_language, is_active, worker_id, buyer_id, created_at) "
            "VALUES (:id, :ec, :name, :email, :phone, :role, :pw, :pin, :lang, :active, :wid, :bid, :now)"
        ),
        {
            "id": str(uid), "ec": body["employee_code"], "name": body["name"],
            "email": body.get("email"), "phone": body.get("phone"), "role": body["role"],
            "pw": pw_hash, "pin": pin_hash, "lang": body.get("preferred_language", "en"),
            "active": body.get("is_active", True),
            "wid": str(body["worker_id"]) if body.get("worker_id") else None,
            "bid": str(body["buyer_id"]) if body.get("buyer_id") else None,
            "now": ts,
        },
    )
    db.commit()
    row = db.execute(
        text(
            "SELECT id, employee_code, name, email, phone, role, preferred_language, "
            "is_active, worker_id, buyer_id, created_at FROM users WHERE id = :id"
        ),
        {"id": str(uid)},
    ).fetchone()
    return _user_out(row)


@router.patch("/users/{id}")
def update_user(
    id: uuid.UUID,
    body: dict,
    user=Depends(require_permission("users.manage")),
    db: Session = Depends(get_db),
):
    from app.core.security import hash_password, hash_pin

    allowed_fields = ("name", "email", "phone", "role", "preferred_language", "is_active", "worker_id", "buyer_id")
    updates = {k: v for k, v in body.items() if k in allowed_fields}
    if body.get("password"):
        updates["password_hash"] = hash_password(body["password"])
    if body.get("pin"):
        updates["pin_hash"] = hash_pin(body["pin"])

    if not updates:
        raise AppError("VALIDATION_ERROR", "No updatable fields provided.")

    sets = ", ".join(f"{k} = :{k}" for k in updates)
    updates["id"] = str(id)
    updates["now"] = now()
    db.execute(text(f"UPDATE users SET {sets}, updated_at = :now WHERE id = :id"), updates)
    db.commit()

    row = db.execute(
        text(
            "SELECT id, employee_code, name, email, phone, role, preferred_language, "
            "is_active, worker_id, buyer_id, created_at FROM users WHERE id = :id"
        ),
        {"id": str(id)},
    ).fetchone()
    if row is None:
        raise AppError("NOT_FOUND", f"User {id} not found.")
    return _user_out(row)


@router.get("/audit")
def get_audit(
    entity: str | None = Query(None),
    entity_id: str | None = Query(None),
    actor_id: uuid.UUID | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user=Depends(require_permission("audit.view")),
    db: Session = Depends(get_db),
):
    where = "WHERE 1=1"
    params: dict = {}
    if entity:
        where += " AND entity = :entity"
        params["entity"] = entity
    if entity_id:
        where += " AND entity_id = :entity_id"
        params["entity_id"] = entity_id
    if actor_id:
        where += " AND actor_id = :actor_id"
        params["actor_id"] = str(actor_id)
    if date_from:
        where += " AND created_at >= :df"
        params["df"] = date_from
    if date_to:
        where += " AND created_at <= :dt"
        params["dt"] = date_to

    total = db.execute(text(f"SELECT COUNT(*) FROM audit_log {where}"), params).scalar()
    offset = (page - 1) * size
    params["lim"] = size
    params["off"] = offset
    rows = db.execute(
        text(
            f"SELECT id, actor_id, action, entity, entity_id, before, after, created_at "
            f"FROM audit_log {where} ORDER BY created_at DESC LIMIT :lim OFFSET :off"
        ),
        params,
    ).fetchall()
    return {
        "items": [
            {
                "id": str(r.id), "actor_id": str(r.actor_id) if r.actor_id else None,
                "action": r.action, "entity": r.entity, "entity_id": r.entity_id,
                "before": r.before, "after": r.after,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ],
        "total": total, "page": page, "size": size,
    }
