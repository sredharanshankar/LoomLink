"""Master-data CRUD service: suppliers, yarn types, buyers, fabric types,
route templates, machines, workers, shifts, users.

All write paths: single DB transaction (caller holds), audit_log for sensitive
rows, domain event via app.core.events.publish().
"""
from __future__ import annotations
import re
import uuid
import datetime as dt
from typing import Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.ids import next_code
from app.core import time as app_time
from app.core import events as ev
from app.core.audit import audit


_GSTIN_RE = re.compile(
    r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
)
_PHONE_RE = re.compile(r"^(\+91)?[6-9][0-9]{9}$")

_STAGE_PREFIX = {"SP": "spinning", "WV": "weaving", "DY": "dyeing", "FN": "finishing"}
_FLOOR_W, _FLOOR_H = 12, 8


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _validate_gstin(value: str | None) -> None:
    if value and not _GSTIN_RE.match(value):
        raise AppError("VALIDATION_ERROR", f"Invalid GSTIN: {value}")


def _validate_phone(value: str | None) -> None:
    if value and not _PHONE_RE.match(value):
        raise AppError("VALIDATION_ERROR", f"Invalid phone number: {value}")


def _actor(user: dict) -> uuid.UUID | None:
    raw = user.get("id")
    return uuid.UUID(str(raw)) if raw else None


# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------

def list_suppliers(
    session: Session,
    *,
    active_only: bool = True,
    page: int = 1,
    size: int = 50,
) -> tuple[list, int]:
    from app.models.materials import Supplier
    q = select(Supplier)
    if active_only:
        q = q.where(Supplier.is_active.is_(True))
    total = session.scalar(select(func.count()).select_from(q.subquery()))
    rows = session.scalars(q.order_by(Supplier.code).offset((page - 1) * size).limit(size)).all()
    return list(rows), total or 0


def get_supplier(session: Session, supplier_id: uuid.UUID) -> Any:
    from app.models.materials import Supplier
    row = session.get(Supplier, supplier_id)
    if row is None:
        raise AppError("NOT_FOUND", f"Supplier {supplier_id} not found")
    return row


def create_supplier(session: Session, data: dict, user: dict) -> Any:
    from app.models.materials import Supplier, SupplierYarnType
    _validate_gstin(data.get("gstin"))
    _validate_phone(data.get("phone"))
    now = app_time.now()
    code = next_code(session, "supplier")
    row = Supplier(
        id=uuid.uuid4(),
        code=code,
        name=data["name"],
        contact_person=data.get("contact_person"),
        phone=data.get("phone"),
        email=data.get("email"),
        address=data.get("address"),
        gstin=data.get("gstin"),
        payment_terms_days=data.get("payment_terms_days", 30),
        notes=data.get("notes"),
        is_active=True,
        created_at=now,
    )
    session.add(row)
    session.flush()
    for yt_id in data.get("yarn_type_ids", []):
        session.add(SupplierYarnType(
            id=uuid.uuid4(),
            supplier_id=row.id,
            yarn_type_id=uuid.UUID(str(yt_id)),
            created_at=now,
        ))
    ev.publish(session, "supplier.created", {"supplier_id": str(row.id), "code": code}, _actor(user))
    return row


def update_supplier(session: Session, supplier_id: uuid.UUID, data: dict, user: dict) -> Any:
    from app.models.materials import Supplier, SupplierYarnType
    from sqlalchemy import text
    row = session.get(Supplier, supplier_id)
    if row is None:
        raise AppError("NOT_FOUND", f"Supplier {supplier_id} not found")
    _validate_gstin(data.get("gstin", row.gstin))
    _validate_phone(data.get("phone", row.phone))
    before = {"name": row.name, "gstin": row.gstin, "is_active": row.is_active}
    for k, v in data.items():
        if k == "yarn_type_ids":
            continue
        if hasattr(row, k):
            setattr(row, k, v)
    row.updated_at = app_time.now()
    if "yarn_type_ids" in data:
        session.execute(
            text("DELETE FROM supplier_yarn_types WHERE supplier_id = :sid"),
            {"sid": row.id},
        )
        now = app_time.now()
        for yt_id in data["yarn_type_ids"]:
            session.add(SupplierYarnType(
                id=uuid.uuid4(),
                supplier_id=row.id,
                yarn_type_id=uuid.UUID(str(yt_id)),
                created_at=now,
            ))
    after = {"name": row.name, "gstin": row.gstin, "is_active": row.is_active}
    audit(session, _actor(user), "supplier.updated", "supplier", str(row.id), before, after)
    ev.publish(session, "supplier.updated", {"supplier_id": str(row.id)}, _actor(user))
    return row


def supplier_yarn_types(session: Session, supplier_id: uuid.UUID) -> list:
    from app.models.materials import SupplierYarnType, YarnType
    rows = session.scalars(
        select(YarnType)
        .join(SupplierYarnType, SupplierYarnType.yarn_type_id == YarnType.id)
        .where(SupplierYarnType.supplier_id == supplier_id)
        .order_by(YarnType.code)
    ).all()
    return list(rows)


# ---------------------------------------------------------------------------
# Yarn Types
# ---------------------------------------------------------------------------

def list_yarn_types(
    session: Session,
    *,
    active_only: bool = True,
    page: int = 1,
    size: int = 50,
) -> tuple[list, int]:
    from app.models.materials import YarnType
    q = select(YarnType)
    if active_only:
        q = q.where(YarnType.is_active.is_(True))
    total = session.scalar(select(func.count()).select_from(q.subquery()))
    rows = session.scalars(q.order_by(YarnType.code).offset((page - 1) * size).limit(size)).all()
    return list(rows), total or 0


def get_yarn_type(session: Session, yarn_type_id: uuid.UUID) -> Any:
    from app.models.materials import YarnType
    row = session.get(YarnType, yarn_type_id)
    if row is None:
        raise AppError("NOT_FOUND", f"YarnType {yarn_type_id} not found")
    return row


def create_yarn_type(session: Session, data: dict, user: dict) -> Any:
    from app.models.materials import YarnType
    now = app_time.now()
    row = YarnType(
        id=uuid.uuid4(),
        code=data["code"],
        material=data["material"],
        count_label=data["count_label"],
        colour=data["colour"],
        colour_hex=data.get("colour_hex"),
        reorder_level_g=data.get("reorder_level_g", 0),
        standard_rate_paise_per_kg=data.get("standard_rate_paise_per_kg", 0),
        is_active=True,
        created_at=now,
    )
    session.add(row)
    session.flush()
    ev.publish(session, "yarn_type.created", {"yarn_type_id": str(row.id), "code": row.code}, _actor(user))
    return row


def update_yarn_type(session: Session, yarn_type_id: uuid.UUID, data: dict, user: dict) -> Any:
    from app.models.materials import YarnType
    row = session.get(YarnType, yarn_type_id)
    if row is None:
        raise AppError("NOT_FOUND", f"YarnType {yarn_type_id} not found")
    for k, v in data.items():
        if hasattr(row, k):
            setattr(row, k, v)
    row.updated_at = app_time.now()
    ev.publish(session, "yarn_type.updated", {"yarn_type_id": str(row.id)}, _actor(user))
    return row


# ---------------------------------------------------------------------------
# Buyers
# ---------------------------------------------------------------------------

def list_buyers(
    session: Session,
    *,
    active_only: bool = True,
    page: int = 1,
    size: int = 50,
) -> tuple[list, int]:
    from app.models.sales import Buyer
    q = select(Buyer)
    if active_only:
        q = q.where(Buyer.is_active.is_(True))
    total = session.scalar(select(func.count()).select_from(q.subquery()))
    rows = session.scalars(q.order_by(Buyer.code).offset((page - 1) * size).limit(size)).all()
    return list(rows), total or 0


def get_buyer(session: Session, buyer_id: uuid.UUID) -> Any:
    from app.models.sales import Buyer
    row = session.get(Buyer, buyer_id)
    if row is None:
        raise AppError("NOT_FOUND", f"Buyer {buyer_id} not found")
    return row


def create_buyer(session: Session, data: dict, user: dict) -> Any:
    from app.models.sales import Buyer
    _validate_gstin(data.get("gstin"))
    _validate_phone(data.get("phone"))
    _validate_phone(data.get("whatsapp"))
    now = app_time.now()
    code = next_code(session, "buyer")
    row = Buyer(
        id=uuid.uuid4(),
        code=code,
        name=data["name"],
        contact_person=data.get("contact_person"),
        phone=data.get("phone"),
        whatsapp=data.get("whatsapp"),
        email=data.get("email"),
        gstin=data.get("gstin"),
        state_code=data.get("state_code"),
        address=data.get("address"),
        payment_terms_days=data.get("payment_terms_days", 30),
        default_late_penalty_paise_per_day=data.get("default_late_penalty_paise_per_day", 0),
        is_active=True,
        created_at=now,
    )
    session.add(row)
    session.flush()
    audit(session, _actor(user), "buyer.created", "buyer", str(row.id), None, {"code": code})
    ev.publish(session, "buyer.created", {"buyer_id": str(row.id), "code": code}, _actor(user))
    return row


def update_buyer(session: Session, buyer_id: uuid.UUID, data: dict, user: dict) -> Any:
    from app.models.sales import Buyer
    row = session.get(Buyer, buyer_id)
    if row is None:
        raise AppError("NOT_FOUND", f"Buyer {buyer_id} not found")
    _validate_gstin(data.get("gstin", row.gstin))
    _validate_phone(data.get("phone", row.phone))
    _validate_phone(data.get("whatsapp", row.whatsapp))
    before = {"name": row.name, "gstin": row.gstin}
    for k, v in data.items():
        if hasattr(row, k):
            setattr(row, k, v)
    row.updated_at = app_time.now()
    after = {"name": row.name, "gstin": row.gstin}
    audit(session, _actor(user), "buyer.updated", "buyer", str(row.id), before, after)
    ev.publish(session, "buyer.updated", {"buyer_id": str(row.id)}, _actor(user))
    return row


# ---------------------------------------------------------------------------
# Fabric Types
# ---------------------------------------------------------------------------

def list_fabric_types(
    session: Session,
    *,
    active_only: bool = True,
    page: int = 1,
    size: int = 50,
) -> tuple[list, int]:
    from app.models.sales import FabricType
    q = select(FabricType)
    if active_only:
        q = q.where(FabricType.is_active.is_(True))
    total = session.scalar(select(func.count()).select_from(q.subquery()))
    rows = session.scalars(q.order_by(FabricType.code).offset((page - 1) * size).limit(size)).all()
    return list(rows), total or 0


def get_fabric_type(session: Session, fabric_type_id: uuid.UUID) -> Any:
    from app.models.sales import FabricType
    row = session.get(FabricType, fabric_type_id)
    if row is None:
        raise AppError("NOT_FOUND", f"FabricType {fabric_type_id} not found")
    return row


def create_fabric_type(session: Session, data: dict, user: dict) -> Any:
    from app.models.sales import FabricType
    if data.get("yarn_g_per_100m", 0) <= 0:
        raise AppError("VALIDATION_ERROR", "yarn_g_per_100m must be > 0")
    now = app_time.now()
    row = FabricType(
        id=uuid.uuid4(),
        code=data["code"],
        name=data["name"],
        construction=data.get("construction"),
        width_cm=data["width_cm"],
        gsm=data.get("gsm"),
        colour=data["colour"],
        yarn_type_id=uuid.UUID(str(data["yarn_type_id"])),
        yarn_g_per_100m=data["yarn_g_per_100m"],
        route_template_id=uuid.UUID(str(data["route_template_id"])) if data.get("route_template_id") else None,
        hsn_code=data.get("hsn_code", "5208"),
        default_price_paise_per_m=data.get("default_price_paise_per_m", 0),
        gst_bp=data.get("gst_bp", 500),
        is_active=True,
        created_at=now,
    )
    session.add(row)
    session.flush()
    ev.publish(session, "fabric_type.created", {"fabric_type_id": str(row.id), "code": row.code}, _actor(user))
    return row


def update_fabric_type(session: Session, fabric_type_id: uuid.UUID, data: dict, user: dict) -> Any:
    from app.models.sales import FabricType
    row = session.get(FabricType, fabric_type_id)
    if row is None:
        raise AppError("NOT_FOUND", f"FabricType {fabric_type_id} not found")
    if "yarn_g_per_100m" in data and data["yarn_g_per_100m"] <= 0:
        raise AppError("VALIDATION_ERROR", "yarn_g_per_100m must be > 0")
    for k, v in data.items():
        if hasattr(row, k):
            if k in ("yarn_type_id", "route_template_id") and v is not None:
                v = uuid.UUID(str(v))
            setattr(row, k, v)
    row.updated_at = app_time.now()
    ev.publish(session, "fabric_type.updated", {"fabric_type_id": str(row.id)}, _actor(user))
    return row


# ---------------------------------------------------------------------------
# Route Templates
# ---------------------------------------------------------------------------

def list_route_templates(session: Session, *, page: int = 1, size: int = 50) -> tuple[list, int]:
    from app.models.sales import RouteTemplate
    q = select(RouteTemplate)
    total = session.scalar(select(func.count()).select_from(q.subquery()))
    rows = session.scalars(q.order_by(RouteTemplate.name).offset((page - 1) * size).limit(size)).all()
    return list(rows), total or 0


def get_route_template_with_steps(session: Session, template_id: uuid.UUID) -> tuple:
    from app.models.sales import RouteTemplate, RouteStep
    tmpl = session.get(RouteTemplate, template_id)
    if tmpl is None:
        raise AppError("NOT_FOUND", f"RouteTemplate {template_id} not found")
    steps = session.scalars(
        select(RouteStep).where(RouteStep.template_id == template_id).order_by(RouteStep.seq)
    ).all()
    return tmpl, list(steps)


def create_route_template(session: Session, data: dict, user: dict) -> tuple:
    from app.models.sales import RouteTemplate, RouteStep
    now = app_time.now()
    tmpl = RouteTemplate(
        id=uuid.uuid4(),
        name=data["name"],
        description=data.get("description"),
        created_at=now,
    )
    session.add(tmpl)
    session.flush()
    steps = []
    for i, step_data in enumerate(data.get("steps", []), start=1):
        step = RouteStep(
            id=uuid.uuid4(),
            template_id=tmpl.id,
            seq=step_data.get("seq", i),
            stage=step_data["stage"],
            buffer_minutes=step_data.get("buffer_minutes", 0),
            created_at=now,
        )
        session.add(step)
        steps.append(step)
    ev.publish(session, "route_template.created", {"template_id": str(tmpl.id)}, _actor(user))
    return tmpl, steps


# ---------------------------------------------------------------------------
# Machines
# ---------------------------------------------------------------------------

def list_machines(
    session: Session,
    *,
    stage: str | None = None,
    page: int = 1,
    size: int = 50,
) -> tuple[list, int]:
    from app.models.production import Machine
    q = select(Machine)
    if stage:
        q = q.where(Machine.stage == stage)
    total = session.scalar(select(func.count()).select_from(q.subquery()))
    rows = session.scalars(q.order_by(Machine.code).offset((page - 1) * size).limit(size)).all()
    return list(rows), total or 0


def get_machine(session: Session, machine_id: uuid.UUID) -> Any:
    from app.models.production import Machine
    machine = session.get(Machine, machine_id)
    if machine is None:
        raise AppError("NOT_FOUND", f"Machine {machine_id} not found")
    return machine


def get_machine_capabilities(session: Session, machine_id: uuid.UUID) -> list:
    from app.models.production import MachineCapability
    return list(session.scalars(
        select(MachineCapability).where(MachineCapability.machine_id == machine_id)
    ).all())


def create_machine(session: Session, data: dict, user: dict) -> Any:
    from app.models.production import Machine, MachineCapability
    from sqlalchemy import text

    code = data["code"]
    prefix = code[:2].upper()
    if prefix not in _STAGE_PREFIX:
        raise AppError("VALIDATION_ERROR", f"Machine code prefix must be one of: {list(_STAGE_PREFIX)}")
    stage = _STAGE_PREFIX[prefix]
    if data.get("stage") and data["stage"] != stage:
        raise AppError("VALIDATION_ERROR", f"Machine code '{code}' implies stage '{stage}', got '{data['stage']}'")

    fx, fy = int(data.get("floor_x", 1)), int(data.get("floor_y", 1))
    if not (1 <= fx <= _FLOOR_W) or not (1 <= fy <= _FLOOR_H):
        raise AppError("VALIDATION_ERROR", f"floor_x must be 1-{_FLOOR_W}, floor_y must be 1-{_FLOOR_H}")

    existing = session.execute(
        text("SELECT id FROM machines WHERE floor_x = :x AND floor_y = :y LIMIT 1"),
        {"x": fx, "y": fy},
    ).fetchone()
    if existing:
        raise AppError("CONFLICT", f"Floor position ({fx},{fy}) is already occupied")

    now = app_time.now()
    machine = Machine(
        id=uuid.uuid4(),
        code=code,
        stage=stage,
        floor_x=fx,
        floor_y=fy,
        status="idle",
        notes=data.get("notes"),
        created_at=now,
    )
    session.add(machine)
    session.flush()
    for ft_id in data.get("fabric_type_ids", []):
        session.add(MachineCapability(
            id=uuid.uuid4(),
            machine_id=machine.id,
            fabric_type_id=uuid.UUID(str(ft_id)),
            created_at=now,
        ))
    audit(session, _actor(user), "machine.created", "machine", str(machine.id), None, {"code": code, "stage": stage})
    ev.publish(session, "machine.status_changed", {"machine_id": str(machine.id), "status": "idle"}, _actor(user))
    return machine


def update_machine(session: Session, machine_id: uuid.UUID, data: dict, user: dict) -> Any:
    from app.models.production import Machine, MachineCapability
    from sqlalchemy import text
    machine = session.get(Machine, machine_id)
    if machine is None:
        raise AppError("NOT_FOUND", f"Machine {machine_id} not found")
    if "floor_x" in data or "floor_y" in data:
        fx = int(data.get("floor_x", machine.floor_x))
        fy = int(data.get("floor_y", machine.floor_y))
        if not (1 <= fx <= _FLOOR_W) or not (1 <= fy <= _FLOOR_H):
            raise AppError("VALIDATION_ERROR", f"floor_x must be 1-{_FLOOR_W}, floor_y must be 1-{_FLOOR_H}")
        existing = session.execute(
            text("SELECT id FROM machines WHERE floor_x = :x AND floor_y = :y AND id != :mid LIMIT 1"),
            {"x": fx, "y": fy, "mid": machine_id},
        ).fetchone()
        if existing:
            raise AppError("CONFLICT", f"Floor position ({fx},{fy}) is already occupied")
    before = {"status": machine.status, "floor_x": machine.floor_x, "floor_y": machine.floor_y}
    for k, v in data.items():
        if k == "fabric_type_ids":
            continue
        if hasattr(machine, k):
            setattr(machine, k, v)
    machine.updated_at = app_time.now()
    if "fabric_type_ids" in data:
        session.execute(
            text("DELETE FROM machine_capabilities WHERE machine_id = :mid"),
            {"mid": machine_id},
        )
        now = app_time.now()
        for ft_id in data["fabric_type_ids"]:
            session.add(MachineCapability(
                id=uuid.uuid4(),
                machine_id=machine.id,
                fabric_type_id=uuid.UUID(str(ft_id)),
                created_at=now,
            ))
    after = {"status": machine.status, "floor_x": machine.floor_x, "floor_y": machine.floor_y}
    audit(session, _actor(user), "machine.updated", "machine", str(machine.id), before, after)
    ev.publish(session, "machine.status_changed", {"machine_id": str(machine.id), "status": machine.status}, _actor(user))
    return machine


# ---------------------------------------------------------------------------
# Workers
# ---------------------------------------------------------------------------

def list_workers(
    session: Session,
    *,
    active_only: bool = True,
    stage: str | None = None,
    page: int = 1,
    size: int = 50,
) -> tuple[list, int]:
    from app.models.workforce import Worker
    q = select(Worker)
    if active_only:
        q = q.where(Worker.is_active.is_(True))
    if stage:
        q = q.where(Worker.skill_stages.contains([stage]))
    total = session.scalar(select(func.count()).select_from(q.subquery()))
    rows = session.scalars(q.order_by(Worker.code).offset((page - 1) * size).limit(size)).all()
    return list(rows), total or 0


def get_worker(session: Session, worker_id: uuid.UUID) -> Any:
    from app.models.workforce import Worker
    row = session.get(Worker, worker_id)
    if row is None:
        raise AppError("NOT_FOUND", f"Worker {worker_id} not found")
    return row


def create_worker(session: Session, data: dict, user: dict) -> Any:
    from app.models.workforce import Worker
    _validate_phone(data.get("phone"))
    now = app_time.now()
    code = next_code(session, "worker")
    row = Worker(
        id=uuid.uuid4(),
        code=code,
        name=data["name"],
        phone=data.get("phone"),
        department=data.get("department"),
        skill_stages=data.get("skill_stages", []),
        wage_type=data["wage_type"],
        wage_rate_paise=data["wage_rate_paise"],
        piece_rate_paise_per_m=data.get("piece_rate_paise_per_m"),
        default_shift=data.get("default_shift", "A"),
        overtime_willing=data.get("overtime_willing", False),
        joined_on=data.get("joined_on"),
        is_active=True,
        preferred_language=data.get("preferred_language", "en"),
        created_at=now,
    )
    session.add(row)
    session.flush()
    audit(session, _actor(user), "worker.created", "worker", str(row.id), None, {"code": code, "name": row.name})
    ev.publish(session, "worker.created", {"worker_id": str(row.id), "code": code}, _actor(user))
    return row


def update_worker(session: Session, worker_id: uuid.UUID, data: dict, user: dict) -> Any:
    from app.models.workforce import Worker
    row = session.get(Worker, worker_id)
    if row is None:
        raise AppError("NOT_FOUND", f"Worker {worker_id} not found")
    _validate_phone(data.get("phone", row.phone))
    before = {"name": row.name, "is_active": row.is_active, "wage_rate_paise": row.wage_rate_paise}
    for k, v in data.items():
        if hasattr(row, k):
            setattr(row, k, v)
    row.updated_at = app_time.now()
    after = {"name": row.name, "is_active": row.is_active, "wage_rate_paise": row.wage_rate_paise}
    audit(session, _actor(user), "worker.updated", "worker", str(row.id), before, after)
    ev.publish(session, "worker.updated", {"worker_id": str(row.id)}, _actor(user))
    return row


# ---------------------------------------------------------------------------
# Shifts
# ---------------------------------------------------------------------------

def list_shifts(session: Session) -> list:
    from app.models.workforce import Shift
    return list(session.scalars(select(Shift).order_by(Shift.code)).all())


def get_shift(session: Session, code: str) -> Any:
    from app.models.workforce import Shift
    row = session.get(Shift, code)
    if row is None:
        raise AppError("NOT_FOUND", f"Shift {code} not found")
    return row


def create_shift(session: Session, data: dict, user: dict) -> Any:
    from app.models.workforce import Shift
    now = app_time.now()
    row = Shift(
        code=data["code"],
        name=data["name"],
        start_time=data["start_time"],
        end_time=data["end_time"],
        break_minutes=data.get("break_minutes", 0),
        is_overtime=data.get("is_overtime", False),
        created_at=now,
    )
    session.add(row)
    ev.publish(session, "shift.created", {"code": row.code}, _actor(user))
    return row


# ---------------------------------------------------------------------------
# Users (employee accounts)
# ---------------------------------------------------------------------------

def list_users(session: Session, *, page: int = 1, size: int = 50) -> tuple[list, int]:
    from app.models.identity import User
    q = select(User)
    total = session.scalar(select(func.count()).select_from(q.subquery()))
    rows = session.scalars(q.order_by(User.employee_code).offset((page - 1) * size).limit(size)).all()
    return list(rows), total or 0


def get_user(session: Session, user_id: uuid.UUID) -> Any:
    from app.models.identity import User
    row = session.get(User, user_id)
    if row is None:
        raise AppError("NOT_FOUND", f"User {user_id} not found")
    return row


def create_user(session: Session, data: dict, actor: dict) -> Any:
    from app.models.identity import User
    from app.core.security import hash_password
    _validate_phone(data.get("phone"))
    now = app_time.now()
    worker_id = data.get("worker_id")
    row = User(
        id=uuid.uuid4(),
        employee_code=data["employee_code"],
        name=data["name"],
        email=data.get("email"),
        phone=data.get("phone"),
        role=data["role"],
        worker_id=uuid.UUID(str(worker_id)) if worker_id else None,
        preferred_language=data.get("preferred_language", "en"),
        is_active=True,
        created_at=now,
    )
    if data.get("pin"):
        row.pin_hash = hash_password(str(data["pin"]))
    if data.get("password"):
        row.password_hash = hash_password(data["password"])
    session.add(row)
    session.flush()
    audit(session, _actor(actor), "user.created", "user", str(row.id), None,
          {"employee_code": row.employee_code, "role": row.role})
    return row


def update_user(session: Session, user_id: uuid.UUID, data: dict, actor: dict) -> Any:
    from app.models.identity import User
    from app.core.security import hash_password
    row = session.get(User, user_id)
    if row is None:
        raise AppError("NOT_FOUND", f"User {user_id} not found")
    _validate_phone(data.get("phone", row.phone))
    before = {"role": row.role, "is_active": row.is_active}
    for k, v in data.items():
        if k == "pin":
            row.pin_hash = hash_password(str(v))
        elif k == "password":
            row.password_hash = hash_password(v)
        elif hasattr(row, k):
            setattr(row, k, v)
    row.updated_at = app_time.now()
    after = {"role": row.role, "is_active": row.is_active}
    audit(session, _actor(actor), "user.updated", "user", str(row.id), before, after)
    return row
