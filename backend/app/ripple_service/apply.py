from __future__ import annotations

import datetime as dt
import uuid
from collections.abc import Mapping, Sequence
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import events
from app.core.audit import audit
from app.core.errors import AppError
from app.core.time import now
from app.models.identity import MillSettings, User
from app.models.materials import PurchaseOrder, PurchaseOrderLine
from app.models.ripple import RippleEvent, RippleFix
from app.models.workforce import ShiftAssignment
from app.ripple.fixes import apply_actions_virtually, find_fixes
from app.ripple.forecast import forecast
from app.services import interfaces

from . import engine_runner
from .state_loader import load_mill_state


def _actor_id(actor: Mapping[str, Any] | object) -> uuid.UUID | None:
    raw = actor.get("id") if isinstance(actor, Mapping) else getattr(actor, "id", None)
    return uuid.UUID(str(raw)) if raw else None


def _uuid(value: object) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def _enum_value(value: object) -> str:
    raw = getattr(value, "value", None)
    return raw if isinstance(raw, str) else str(value)


def _event_and_fix(
    session: Session, ripple_event_id: uuid.UUID, fix_id: uuid.UUID
) -> tuple[RippleEvent, RippleFix]:
    event = session.scalar(select(RippleEvent).where(RippleEvent.id == ripple_event_id).with_for_update())
    if event is None:
        raise AppError("NOT_FOUND", "Ripple event not found.")
    if _enum_value(event.status) != "open":
        raise AppError("INVALID_STATE", "Only an open Ripple event can be changed.")
    fix = session.scalar(
        select(RippleFix).where(RippleFix.id == fix_id, RippleFix.ripple_event_id == event.id)
    )
    if fix is None:
        raise AppError("NOT_FOUND", "Ripple fix not found for this event.")
    return event, fix


def _actions_valid(state, actions: Sequence[Mapping[str, Any]]) -> bool:
    jobs = {job.id: job for job in state.jobs}
    machines = {machine.id: machine for machine in state.machines}
    for action in actions:
        fn = action.get("fn")
        args = action.get("args", {})
        if fn in {"assign_job", "split_job"}:
            job = jobs.get(str(args.get("job_id")))
            if job is None or job.status in {"done", "cancelled"}:
                return False
            target_ids = (
                (str(args.get("machine_id")),)
                if fn == "assign_job"
                else tuple(str(item) for item in args.get("machine_ids", ()))
            )
            if not target_ids:
                return False
            for target_id in target_ids:
                machine = machines.get(target_id)
                if (
                    machine is None
                    or machine.status in {"breakdown", "maintenance", "offline"}
                    or machine.stage != job.stage
                    or machine.unit != job.unit
                    or (machine.capabilities is not None and job.fabric_type_id not in machine.capabilities)
                ):
                    return False
        elif fn == "assign_overtime":
            machine = machines.get(str(args.get("machine_id")))
            if machine is None or machine.status in {"breakdown", "maintenance", "offline"}:
                return False
        elif fn == "swap_jobs":
            first = jobs.get(str(args.get("first_job_id")))
            second = jobs.get(str(args.get("second_job_id")))
            if first is None or second is None or first.machine_id != second.machine_id:
                return False
            if first.status in {"done", "cancelled"} or second.status in {"done", "cancelled"}:
                return False
        elif fn not in {"expedite_yarn"}:
            return False
    return True


def _fresh_fixes(event: RippleEvent, state) -> list[dict]:
    baseline = forecast(state)
    params = event.params or {}
    trigger = {
        "kind": _enum_value(event.trigger_kind),
        "machine_id": params.get("machine_id"),
        "ref": params.get("machine_id") or params.get("yarn_type_id") or params.get("order_id"),
        "affected_order_ids": tuple(
            str(item["order_id"])
            for item in (event.affected_orders or [])
            if isinstance(item, Mapping) and item.get("order_id")
        ),
    }
    return [item.to_dict() for item in find_fixes(state, baseline, trigger, k=3)]


def _validate_stale(event: RippleEvent, fix: RippleFix, state) -> None:
    actions = tuple(fix.actions or ())
    if not _actions_valid(state, actions):
        raise AppError(
            "STALE_SNAPSHOT",
            "The floor changed — Ripple recalculated the available fixes.",
            details={"recomputed_fixes": _fresh_fixes(event, state)},
        )
    result = forecast(apply_actions_virtually(state, actions))
    late_after = sum(1 for order in result.orders if order.slack_minutes is None or order.slack_minutes < 0)
    stored_late_after = max(0, fix.orders_total - fix.orders_on_time)
    if late_after > stored_late_after:
        raise AppError(
            "STALE_SNAPSHOT",
            "The floor changed — Ripple recalculated the available fixes.",
            details={"recomputed_fixes": _fresh_fixes(event, state)},
        )


def _split_quantities(state, job_id: str, machine_ids: Sequence[str]) -> list[int]:
    job = next(item for item in state.jobs if item.id == job_id)
    machines = {item.id: item for item in state.machines}
    rates = [
        machines[machine_id].speeds.get(job.fabric_type_id, (machines[machine_id].default_speed_per_hour, 0))[
            0
        ]
        for machine_id in machine_ids
    ]
    total_rate = max(1, sum(rates))
    first = max(1, job.remaining_qty * rates[0] // total_rate)
    return [first, job.remaining_qty - first]


def _execute_actions(
    session: Session,
    event: RippleEvent,
    fix: RippleFix,
    actor_id: uuid.UUID | None,
    state,
) -> tuple[set[uuid.UUID], list[dict[str, Any]]]:
    reason = f"ripple:{event.code}:fix{fix.rank}"
    touched_machines: set[uuid.UUID] = set()
    operator_notices: list[dict[str, Any]] = []
    for action in fix.actions or ():
        fn = action.get("fn")
        args = action.get("args", {})
        if fn == "assign_job":
            machine_id = _uuid(args["machine_id"])
            interfaces.assign_job(
                session,
                _uuid(args["job_id"]),
                machine_id,
                int(args["queue_position"]) if args.get("queue_position") is not None else None,
                actor_id,
                reason,
            )
            touched_machines.add(machine_id)
            job = next(item for item in state.jobs if item.id == str(args["job_id"]))
            machine = next(item for item in state.machines if item.id == str(args["machine_id"]))
            operator_notices.append(
                {
                    "machine_id": machine_id,
                    "job": job.code,
                    "qty": job.remaining_qty,
                    "machine": machine.code,
                    "from_time": max(state.now, machine.available_from).isoformat(),
                }
            )
        elif fn == "assign_overtime":
            machine_id = _uuid(args["machine_id"])
            interfaces.assign_overtime(
                session,
                machine_id,
                dt.date.fromisoformat(str(args["date"])),
                str(args.get("shift_code", "C")),
                _uuid(args["worker_id"]) if args.get("worker_id") else None,
                actor_id,
                reason,
            )
            touched_machines.add(machine_id)
        elif fn == "split_job":
            machine_ids = [str(item) for item in args.get("machine_ids", ())]
            parts = _split_quantities(state, str(args["job_id"]), machine_ids)
            new_ids = interfaces.split_job(session, _uuid(args["job_id"]), parts, actor_id, reason)
            original = next(item for item in state.jobs if item.id == str(args["job_id"]))
            for part_index, (child_id, target_machine_id) in enumerate(
                zip(new_ids, machine_ids, strict=True)
            ):
                interfaces.assign_job(session, child_id, _uuid(target_machine_id), 1, actor_id, reason)
                touched_machines.add(_uuid(target_machine_id))
                machine = next(item for item in state.machines if item.id == target_machine_id)
                operator_notices.append(
                    {
                        "machine_id": _uuid(target_machine_id),
                        "job": original.code,
                        "qty": parts[part_index],
                        "machine": machine.code,
                        "from_time": max(state.now, machine.available_from).isoformat(),
                    }
                )
        elif fn == "swap_jobs":
            first_id = str(args["first_job_id"])
            second_id = str(args["second_job_id"])
            first = next(item for item in state.jobs if item.id == first_id)
            machine_id = _uuid(first.machine_id)
            queued = sorted(
                (item for item in state.jobs if item.machine_id == first.machine_id),
                key=lambda item: (item.queue_position or 10**9, item.code),
            )
            ordered = [item.id for item in queued]
            first_index, second_index = ordered.index(first_id), ordered.index(second_id)
            ordered[first_index], ordered[second_index] = ordered[second_index], ordered[first_index]
            interfaces.reorder_queue(session, machine_id, [_uuid(item) for item in ordered], actor_id, reason)
            touched_machines.add(machine_id)
        elif fn == "expedite_yarn":
            po_id = args.get("po_id")
            if po_id is None:
                po_id = session.scalar(
                    select(PurchaseOrder.id)
                    .join(PurchaseOrderLine, PurchaseOrderLine.po_id == PurchaseOrder.id)
                    .where(
                        PurchaseOrderLine.yarn_type_id == _uuid(args["yarn_type_id"]),
                        PurchaseOrder.status.in_(("sent", "partly_received")),
                    )
                    .order_by(PurchaseOrder.expected_date)
                    .limit(1)
                )
            if po_id is None:
                raise AppError("INVALID_STATE", "No open purchase order can be expedited.")
            needed = dt.datetime.fromisoformat(str(args["date_needed"]))
            interfaces.expedite_purchase(session, _uuid(po_id), needed.date(), actor_id, reason)
    return touched_machines, operator_notices


def _notify_operators(
    session: Session,
    notices: list[dict[str, Any]],
    event: RippleEvent,
    timezone_name: str,
) -> None:
    if not notices:
        return
    machine_ids = {notice["machine_id"] for notice in notices}
    local_today = now().astimezone(ZoneInfo(timezone_name)).date()
    rows = session.execute(
        select(User.id, ShiftAssignment.machine_id)
        .join(ShiftAssignment, ShiftAssignment.worker_id == User.worker_id)
        .where(
            ShiftAssignment.machine_id.in_(machine_ids),
            ShiftAssignment.date.in_((local_today, local_today + dt.timedelta(days=1))),
        )
    )
    users_by_machine: dict[uuid.UUID, set[uuid.UUID]] = {}
    for user_id, machine_id in rows:
        users_by_machine.setdefault(machine_id, set()).add(user_id)
    for notice in notices:
        for user_id in users_by_machine.get(notice["machine_id"], set()):
            interfaces.notify(
                session,
                user_id=user_id,
                type="ripple",
                title_key="ripple.notify.new_job",
                params={
                    "ripple_code": event.code,
                    "job": notice["job"],
                    "qty": notice["qty"],
                    "machine": notice["machine"],
                    "from_time": notice["from_time"],
                },
                link="/w/jobs",
            )


def apply_fix(
    session: Session,
    ripple_event_id: uuid.UUID,
    fix_id: uuid.UUID,
    expected_state_version: int,
    actor: Mapping[str, Any] | object,
) -> RippleEvent:
    event, fix = _event_and_fix(session, ripple_event_id, fix_id)
    settings = session.scalar(select(MillSettings).limit(1).with_for_update())
    if settings is None:
        raise AppError("INVALID_STATE", "Mill settings are required before applying a Ripple fix.")
    state = load_mill_state(session)
    if settings.state_version != expected_state_version:
        _validate_stale(event, fix, state)
    actor_id = _actor_id(actor)
    before = {"status": _enum_value(event.status), "resolved_fix_id": None}
    _, notices = _execute_actions(session, event, fix, actor_id, state)
    stamp = now()
    fix.applied_at = stamp
    fix.applied_by = actor_id
    event.status = "resolved"
    event.resolved_fix_id = fix.id
    event.resolved_by = actor_id
    event.resolved_at = stamp
    event.updated_at = stamp
    audit(
        session,
        actor_id,
        "ripple.fix_applied",
        "ripple_event",
        str(event.id),
        before=before,
        after={"status": "resolved", "resolved_fix_id": str(fix.id)},
    )
    events.publish(
        session,
        "ripple.resolved",
        {"ripple_event_id": str(event.id), "code": event.code, "fix_id": str(fix.id)},
        actor_id,
    )
    _notify_operators(session, notices, event, state.settings.timezone)
    engine_runner.recompute(session)
    return event


def dismiss_event(
    session: Session,
    ripple_event_id: uuid.UUID,
    reason: str,
    actor: Mapping[str, Any] | object,
) -> RippleEvent:
    reason = reason.strip()
    if not reason:
        raise AppError("VALIDATION_ERROR", "A dismissal reason is required.", status=400)
    event = session.scalar(select(RippleEvent).where(RippleEvent.id == ripple_event_id).with_for_update())
    if event is None:
        raise AppError("NOT_FOUND", "Ripple event not found.")
    if _enum_value(event.status) != "open":
        raise AppError("INVALID_STATE", "Only an open Ripple event can be dismissed.")
    actor_id = _actor_id(actor)
    stamp = now()
    before = {"status": _enum_value(event.status)}
    event.status = "dismissed"
    event.params = {**(event.params or {}), "dismiss_reason": reason}
    event.resolved_by = actor_id
    event.resolved_at = stamp
    event.updated_at = stamp
    audit(
        session,
        actor_id,
        "ripple.dismissed",
        "ripple_event",
        str(event.id),
        before=before,
        after={"status": "dismissed", "reason": reason},
    )
    events.publish(
        session,
        "ripple.dismissed",
        {"ripple_event_id": str(event.id), "code": event.code, "reason": reason},
        actor_id,
    )
    return event
