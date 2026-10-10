"""Scan resolution service.

Prefix rules:
  YB-*    → yarn_batch
  ROLL-*  → roll
  ORD-*   → order
  EMP-*   → worker
  else    → machine code lookup (SP/WV/DY/FN prefix)
"""
from __future__ import annotations
import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError


_MACHINE_PREFIX_STAGE = {"SP": "spinning", "WV": "weaving", "DY": "dyeing", "FN": "finishing"}


def resolve(session: Session, code: str, user: dict) -> dict:
    code = code.strip().upper()
    role = user.get("role", "")

    if code.startswith("YB-"):
        return _resolve_batch(session, code, role)
    elif code.startswith("ROLL-"):
        return _resolve_roll(session, code, role)
    elif code.startswith("ORD-"):
        return _resolve_order(session, code, role)
    elif code.startswith("EMP-"):
        return _resolve_worker(session, code, role)
    else:
        prefix = code[:2].upper()
        if prefix in _MACHINE_PREFIX_STAGE:
            return _resolve_machine(session, code, role)
        raise AppError("NOT_FOUND", f"Unknown scan code: {code}")


def _resolve_batch(session: Session, code: str, role: str) -> dict:
    from app.models.materials import YarnBatch
    row = session.scalar(select(YarnBatch).where(YarnBatch.code == code))
    if row is None:
        raise AppError("NOT_FOUND", f"Yarn batch {code} not found")
    actions = _batch_actions(row.status, role)
    return {
        "type": "yarn_batch",
        "id": str(row.id),
        "code": row.code,
        "status": row.status,
        "yarn_type_id": str(row.yarn_type_id),
        "supplier_id": str(row.supplier_id),
        "received_g": row.received_g,
        "location": row.location,
        "allowed_actions": actions,
    }


def _resolve_roll(session: Session, code: str, role: str) -> dict:
    from app.models.quality import Roll
    row = session.scalar(select(Roll).where(Roll.code == code))
    if row is None:
        raise AppError("NOT_FOUND", f"Roll {code} not found")
    actions = _roll_actions(row.status, role)
    return {
        "type": "roll",
        "id": str(row.id),
        "code": row.code,
        "status": row.status,
        "order_id": str(row.order_id),
        "length_cm": row.length_cm,
        "shelf_location": row.shelf_location,
        "allowed_actions": actions,
    }


def _resolve_order(session: Session, code: str, role: str) -> dict:
    from app.models.sales import Order
    row = session.scalar(select(Order).where(Order.code == code))
    if row is None:
        raise AppError("NOT_FOUND", f"Order {code} not found")
    actions = _order_actions(row.status, role)
    return {
        "type": "order",
        "id": str(row.id),
        "code": row.code,
        "status": row.status,
        "buyer_id": str(row.buyer_id),
        "fabric_type_id": str(row.fabric_type_id),
        "quantity_cm": row.quantity_cm,
        "due_date": row.due_date.isoformat() if row.due_date else None,
        "allowed_actions": actions,
    }


def _resolve_worker(session: Session, code: str, role: str) -> dict:
    from app.models.workforce import Worker
    row = session.scalar(select(Worker).where(Worker.code == code))
    if row is None:
        raise AppError("NOT_FOUND", f"Worker {code} not found")
    actions = _worker_actions(role)
    return {
        "type": "worker",
        "id": str(row.id),
        "code": row.code,
        "name": row.name,
        "skill_stages": row.skill_stages or [],
        "is_active": row.is_active,
        "allowed_actions": actions,
    }


def _resolve_machine(session: Session, code: str, role: str) -> dict:
    from app.models.production import Machine
    row = session.scalar(select(Machine).where(Machine.code == code))
    if row is None:
        raise AppError("NOT_FOUND", f"Machine {code} not found")
    actions = _machine_actions(row.status, role)
    return {
        "type": "machine",
        "id": str(row.id),
        "code": row.code,
        "stage": row.stage,
        "status": row.status,
        "floor_x": row.floor_x,
        "floor_y": row.floor_y,
        "current_job_id": str(row.current_job_id) if row.current_job_id else None,
        "allowed_actions": actions,
    }


# ---------------------------------------------------------------------------
# allowed_actions per entity type, state, and role
# ---------------------------------------------------------------------------

def _batch_actions(status: str, role: str) -> list[str]:
    acts = []
    if status == "active" and role in ("owner", "manager", "storekeeper"):
        acts += ["issue", "return", "adjust", "print_label"]
    if role in ("owner", "manager", "storekeeper"):
        acts.append("view_detail")
    return acts


def _roll_actions(status: str, role: str) -> list[str]:
    acts = ["view_detail"]
    if status == "pending_qc" and role in ("owner", "manager", "qc_inspector"):
        acts.append("inspect")
    if status == "passed" and role in ("owner", "manager", "dispatch", "qc_inspector"):
        acts.append("print_label")
    if status == "passed" and role in ("owner", "manager", "dispatch"):
        acts.append("dispatch")
    return acts


def _order_actions(status: str, role: str) -> list[str]:
    acts = ["view_detail"]
    if status == "draft" and role in ("owner", "manager"):
        acts.append("confirm")
    if status in ("draft", "confirmed") and role in ("owner", "manager"):
        acts.append("cancel")
    if role in ("owner", "manager", "storekeeper", "qc_inspector", "dispatch"):
        acts.append("print_label")
    return acts


def _worker_actions(role: str) -> list[str]:
    acts = ["view_detail"]
    if role in ("owner", "manager"):
        acts += ["edit", "assign_shift"]
    return acts


def _machine_actions(status: str, role: str) -> list[str]:
    acts = ["view_detail"]
    if status == "idle" and role in ("owner", "manager"):
        acts.append("assign_job")
    if status == "running" and role in ("owner", "manager", "operator"):
        acts += ["log_progress", "breakdown"]
    if status == "breakdown" and role in ("owner", "manager"):
        acts.append("mark_repaired")
    return acts
