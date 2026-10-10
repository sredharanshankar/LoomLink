from __future__ import annotations
from typing import Any
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer_scheme = HTTPBearer(auto_error=False)

PERMISSIONS: dict[str, set[str]] = {
    "owner": {
        "users.manage", "settings.view", "settings.manage", "audit.view",
        "scan.use", "labels.print",
        "suppliers.view", "suppliers.manage",
        "inventory.view", "inventory.manage", "inventory.receive", "inventory.issue", "inventory.adjust",
        "purchasing.manage",
        "buyers.view", "buyers.manage",
        "orders.view", "orders.manage", "orders.lookup",
        "production.view", "production.plan", "production.operate",
        "machines.manage",
        "rolls.create", "quality.view", "quality.inspect", "rolls.passport",
        "dispatch.view", "dispatch.manage",
        "workers.view", "workers.manage",
        "attendance.self", "attendance.view", "attendance.manage",
        "payroll.view", "payroll.manage", "payroll.approve",
        "finance.view", "finance.manage", "finance.record_payment", "finance.view_costs",
        "dashboard.owner",
        "ripple.view", "ripple.manage", "ripple.apply",
        "leak.view",
        "bol.use",
    },
    "manager": {
        "settings.view",
        "scan.use", "labels.print",
        "suppliers.view",
        "inventory.view", "inventory.manage", "inventory.issue", "inventory.adjust",
        "purchasing.manage",
        "buyers.view", "buyers.manage",
        "orders.view", "orders.manage", "orders.lookup",
        "production.view", "production.plan", "production.operate",
        "machines.manage",
        "rolls.create", "quality.view", "rolls.passport",
        "dispatch.view",
        "workers.view", "workers.manage",
        "attendance.self", "attendance.view", "attendance.manage",
        "finance.view_costs",
        "dashboard.owner",
        "ripple.view", "ripple.manage", "ripple.apply",
        "leak.view",
        "bol.use",
    },
    "storekeeper": {
        "scan.use", "labels.print",
        "suppliers.view", "suppliers.manage",
        "inventory.view", "inventory.manage", "inventory.receive", "inventory.issue",
        "purchasing.manage",
        "orders.view", "orders.lookup",
        "production.view",
        "dispatch.view",
        "attendance.self",
        "bol.use",
    },
    "operator": {
        "scan.use",
        "inventory.view",
        "orders.view",
        "production.view", "production.operate",
        "rolls.create",
        "attendance.self",
        "bol.use",
    },
    "qc_inspector": {
        "scan.use", "labels.print",
        "orders.view", "orders.lookup",
        "production.view",
        "quality.view", "quality.inspect", "rolls.passport",
        "dispatch.view",
        "attendance.self",
        "bol.use",
    },
    "dispatch": {
        "scan.use",
        "suppliers.view",
        "buyers.view",
        "orders.view", "orders.lookup",
        "production.view",
        "quality.view", "rolls.passport",
        "dispatch.view", "dispatch.manage",
        "attendance.self",
        "bol.use",
    },
    "accounts": {
        "settings.view",
        "scan.use",
        "suppliers.view", "suppliers.manage",
        "inventory.view",
        "purchasing.manage",
        "buyers.view", "buyers.manage",
        "orders.view", "orders.lookup",
        "workers.view", "workers.manage",
        "attendance.view",
        "payroll.view", "payroll.manage",
        "finance.view", "finance.manage", "finance.record_payment", "finance.view_costs",
        "dashboard.owner",
        "dispatch.view",
        "leak.view",
    },
    "buyer": {
        "buyer.own",
    },
}


def has_permission(user_role: str, perm: str) -> bool:
    return perm in PERMISSIONS.get(user_role, set())


async def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    from app.core.errors import AppError
    from app.core.security import decode_access_token
    import jwt

    if credentials is None:
        raise AppError("UNAUTHENTICATED", "Authentication required.")
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise AppError("UNAUTHENTICATED", "Token expired.")
    except jwt.InvalidTokenError:
        raise AppError("UNAUTHENTICATED", "Invalid token.")
    return payload


def require_permission(*perms: str):
    """FastAPI dependency factory — any-of logic (user needs at least one)."""
    async def _dep(user: dict = Depends(current_user)) -> dict:
        role = user.get("role", "")
        if not any(has_permission(role, p) for p in perms):
            from app.core.errors import AppError
            raise AppError("FORBIDDEN", f"Permission required: {', '.join(perms)}")
        return user
    return _dep


def mask_money(data: dict, user: dict) -> dict:
    """Set money fields to None when caller lacks finance.view permission."""
    role = user.get("role", "")
    if has_permission(role, "finance.view") or has_permission(role, "finance.view_costs"):
        return data
    money_keys = [k for k in data if k.endswith("_paise") or k.endswith("_paise_per_kg")
                  or k.endswith("_paise_per_m") or k.endswith("_paise_per_hour")]
    for k in money_keys:
        data[k] = None
    return data
