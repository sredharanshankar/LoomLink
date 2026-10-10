from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import ceil
from typing import Any

from app.ripple.calendar import open_windows
from app.ripple.diff import RippleDiff
from app.ripple.model import JsonMixin, MillState


@dataclass(frozen=True)
class PenaltyRisk(JsonMixin):
    order_code: str
    buyer: str
    late_minutes: int
    days: int
    paise: int


@dataclass(frozen=True)
class AtRisk(JsonMixin):
    total_paise: int
    idle_paise: int
    penalties: tuple[PenaltyRisk, ...]
    assumptions: Mapping[str, Any]


@dataclass(frozen=True)
class FixCost(JsonMixin):
    total_paise: int
    overtime_paise: int
    changeover_paise: int
    expedite_paise: int
    assumptions: Mapping[str, Any]


def late_penalty_days(late_minutes: int, grace: int) -> int:
    if late_minutes <= grace:
        return 0
    return ceil((late_minutes - grace) / 1_440)


def _trigger_value(trigger: object, key: str, default: Any = None) -> Any:
    if isinstance(trigger, Mapping):
        return trigger.get(key, default)
    return getattr(trigger, key, default)


def at_risk(state: MillState, diff: RippleDiff, trigger: object) -> AtRisk:
    idle_paise = 0
    idle_rate = 0
    kind = _trigger_value(trigger, "kind", _trigger_value(trigger, "type"))
    if kind == "breakdown":
        machine_id = _trigger_value(trigger, "machine_id", _trigger_value(trigger, "ref"))
        machine = next(
            (item for item in state.machines if item.id == machine_id or item.code == machine_id), None
        )
        if machine is not None and machine.available_from > state.now:
            windows = open_windows(machine, state.settings, state.now, machine.available_from)
            idle_minutes = sum(int((item.end - item.start).total_seconds() // 60) for item in windows)
            idle_rate = machine.idle_cost_paise_per_hour
            idle_paise = idle_minutes * idle_rate // 60
    order_by_id = {item.id: item for item in state.orders}
    penalties: list[PenaltyRisk] = []
    for changed in diff.orders:
        if not changed.newly_late or changed.after_slack_minutes is None:
            continue
        order = order_by_id.get(changed.order_id)
        if order is None:
            continue
        late_minutes = max(0, -changed.after_slack_minutes)
        days = late_penalty_days(late_minutes, state.settings.penalty_grace_minutes)
        if days == 0:
            continue
        penalties.append(
            PenaltyRisk(
                order_code=order.code,
                buyer=order.buyer_name,
                late_minutes=late_minutes,
                days=days,
                paise=days * order.penalty_paise_per_day,
            )
        )
    penalties.sort(key=lambda item: item.order_code)
    return AtRisk(
        total_paise=idle_paise + sum(item.paise for item in penalties),
        idle_paise=idle_paise,
        penalties=tuple(penalties),
        assumptions={"idle_rate": idle_rate, "grace_minutes": state.settings.penalty_grace_minutes},
    )


def _assignment_changeovers(actions: Sequence[Mapping[str, Any]], state: MillState) -> int:
    jobs = {item.id: item for item in state.jobs}
    machines = {item.id: item for item in state.machines}
    count = 0
    for action in actions:
        fn = action.get("fn")
        args = action.get("args", {})
        job = jobs.get(args.get("job_id"))
        if job is None:
            continue
        if fn == "assign_job":
            targets = (args.get("machine_id"),)
        elif fn == "split_job":
            targets = tuple(args.get("machine_ids", ()))
        else:
            continue
        for target in targets:
            machine = machines.get(target)
            if machine is None or target == job.machine_id:
                continue
            current = sorted(
                (
                    item
                    for item in state.jobs
                    if item.id != job.id
                    and item.machine_id == machine.id
                    and item.status not in {"done", "cancelled"}
                ),
                key=lambda item: (not item.is_running, item.queue_position or 10**9, item.code),
            )
            if (
                fn == "split_job"
                and not current
                or current
                and current[-1].fabric_type_id != job.fabric_type_id
            ):
                count += 1
    return count


def fix_cost(actions: Sequence[Mapping[str, Any]], state: MillState) -> FixCost:
    overtime_count = sum(1 for item in actions if item.get("fn") == "assign_overtime")
    overtime_each = (
        state.settings.overtime_shift_minutes
        * state.settings.overtime_hourly_paise
        * state.settings.overtime_multiplier_bp
        // (60 * 10_000)
    )
    explicit_changeovers = sum(1 for item in actions if item.get("fn") == "changeover")
    inferred_changeovers = _assignment_changeovers(actions, state)
    overtime_paise = overtime_count * overtime_each
    changeover_paise = (explicit_changeovers + inferred_changeovers) * state.settings.changeover_cost_paise
    expedite_paise = 0
    return FixCost(
        total_paise=overtime_paise + changeover_paise + expedite_paise,
        overtime_paise=overtime_paise,
        changeover_paise=changeover_paise,
        expedite_paise=expedite_paise,
        assumptions={
            "overtime_shift_minutes": state.settings.overtime_shift_minutes,
            "overtime_multiplier_bp": state.settings.overtime_multiplier_bp,
            "changeover_paise": state.settings.changeover_cost_paise,
            "expedite_paise": 0,
        },
    )
