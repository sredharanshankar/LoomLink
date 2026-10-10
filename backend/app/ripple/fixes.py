from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, time, timedelta
from itertools import combinations
from typing import Any
from zoneinfo import ZoneInfo

from app.ripple.forecast import forecast
from app.ripple.model import Forecast, JsonMixin, MillState, Window, YarnState
from app.ripple.pricing import fix_cost

Action = Mapping[str, Any]


@dataclass(frozen=True)
class FixOutcome(JsonMixin):
    orders_on_time: int
    orders_total: int
    orders_late_after: int
    total_late_minutes: int
    extra_cost_paise: int
    changes_count: int
    collateral: tuple[str, ...]


@dataclass(frozen=True)
class Fix(JsonMixin):
    kind: str
    actions: tuple[Action, ...]
    title_key: str
    explanation_key: str
    params: Mapping[str, Any]
    outcome: FixOutcome
    rank_key: tuple[Any, ...]


def _parse_date(value: object) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return date.fromisoformat(str(value))


def _overtime_window(state: MillState, action_date: date) -> Window:
    zone = ZoneInfo(state.settings.timezone)
    starts = datetime.combine(action_date, time(22), zone).astimezone(UTC)
    ends = datetime.combine(action_date + timedelta(days=1), time(6), zone).astimezone(UTC)
    return Window(starts, ends)


def apply_actions_virtually(state: MillState, actions: Sequence[Action]) -> MillState:
    jobs = list(state.jobs)
    machines = list(state.machines)
    yarn = list(state.yarn)
    for action in actions:
        fn = action.get("fn")
        args = action.get("args", {})
        if fn == "assign_job":
            jobs = [
                replace(
                    job,
                    machine_id=str(args["machine_id"]),
                    queue_position=int(args.get("queue_position", 1)),
                    status="ready" if job.status == "blocked" else job.status,
                    is_running=False if job.machine_id != args["machine_id"] else job.is_running,
                )
                if job.id == args.get("job_id")
                else job
                for job in jobs
            ]
        elif fn == "assign_overtime":
            window = _overtime_window(state, _parse_date(args["date"]))
            machines = [
                replace(
                    machine,
                    overtime_windows=tuple(
                        sorted((*machine.overtime_windows, window), key=lambda item: item.start)
                    ),
                )
                if machine.id == args.get("machine_id")
                else machine
                for machine in machines
            ]
        elif fn == "split_job":
            index = next(
                (position for position, job in enumerate(jobs) if job.id == args.get("job_id")), None
            )
            if index is None:
                continue
            original = jobs[index]
            machine_ids = tuple(str(item) for item in args.get("machine_ids", ()))
            if len(machine_ids) != 2:
                continue
            machine_by_id = {item.id: item for item in machines}
            first_speed = machine_by_id[machine_ids[0]].speeds.get(
                original.fabric_type_id, (machine_by_id[machine_ids[0]].default_speed_per_hour, 0)
            )[0]
            second_speed = machine_by_id[machine_ids[1]].speeds.get(
                original.fabric_type_id, (machine_by_id[machine_ids[1]].default_speed_per_hour, 0)
            )[0]
            first_qty = max(1, original.remaining_qty * first_speed // max(1, first_speed + second_speed))
            second_qty = original.remaining_qty - first_qty
            if second_qty <= 0:
                continue
            jobs[index] = replace(
                original,
                remaining_qty=first_qty,
                machine_id=machine_ids[0],
                queue_position=1,
                is_running=False,
                status="ready",
            )
            jobs.append(
                replace(
                    original,
                    id=f"{original.id}:split:{machine_ids[1]}",
                    code=f"{original.code}-2",
                    remaining_qty=second_qty,
                    machine_id=machine_ids[1],
                    queue_position=1,
                    is_running=False,
                    status="ready",
                )
            )
        elif fn == "swap_jobs":
            first_id = args.get("first_job_id")
            second_id = args.get("second_job_id")
            first = next((job for job in jobs if job.id == first_id), None)
            second = next((job for job in jobs if job.id == second_id), None)
            if first is not None and second is not None:
                jobs = [
                    replace(job, queue_position=second.queue_position)
                    if job.id == first_id
                    else replace(job, queue_position=first.queue_position)
                    if job.id == second_id
                    else job
                    for job in jobs
                ]
        elif fn == "expedite_yarn":
            yarn_type_id = args.get("yarn_type_id")
            needed = args.get("date_needed")
            if isinstance(needed, str):
                needed_at = datetime.fromisoformat(needed)
                if needed_at.tzinfo is None:
                    needed_at = needed_at.replace(tzinfo=UTC)
            elif isinstance(needed, datetime):
                needed_at = needed
            else:
                needed_at = state.now
            revised: list[YarnState] = []
            for item in yarn:
                if item.yarn_type_id == yarn_type_id and item.arrivals:
                    arrivals = list(item.arrivals)
                    _, quantity = arrivals[0]
                    arrivals[0] = (max(state.now, needed_at), quantity)
                    revised.append(
                        replace(item, arrivals=tuple(sorted(arrivals, key=lambda arrival: arrival[0])))
                    )
                else:
                    revised.append(item)
            yarn = revised
    return replace(state, machines=tuple(machines), jobs=tuple(jobs), yarn=tuple(yarn))


def _trigger_value(trigger: object, key: str, default: Any = None) -> Any:
    if isinstance(trigger, Mapping):
        return trigger.get(key, default)
    return getattr(trigger, key, default)


def _candidate_key(actions: Sequence[Action]) -> str:
    return "|".join(
        f"{action.get('fn')}:{sorted((str(key), str(value)) for key, value in action.get('args', {}).items())}"
        for action in actions
    )


def _compatible_pair(first: Action, second: Action) -> bool:
    first_args = first.get("args", {})
    second_args = second.get("args", {})
    first_job = first_args.get("job_id")
    second_job = second_args.get("job_id")
    job_editors = {"assign_job", "split_job"}
    if (
        first_job is not None
        and first_job == second_job
        and (first.get("fn") in job_editors or second.get("fn") in job_editors)
    ):
        return False
    if (
        first.get("fn") == second.get("fn") == "assign_job"
        and first_args.get("machine_id") == second_args.get("machine_id")
        and first_args.get("queue_position") == second_args.get("queue_position")
    ):
        return False
    if first.get("fn") == second.get("fn") == "assign_overtime":
        return not (
            first_args.get("machine_id") == second_args.get("machine_id")
            and first_args.get("date") == second_args.get("date")
        )
    return _candidate_key((first,)) != _candidate_key((second,))


def _evaluate(
    state: MillState, baseline: Forecast, actions: tuple[Action, ...]
) -> tuple[FixOutcome, tuple[Any, ...]]:
    result = forecast(apply_actions_virtually(state, actions))
    baseline_by_id = {item.order_id: item for item in baseline.orders}
    late = [item for item in result.orders if item.slack_minutes is None or item.slack_minutes < 0]
    collateral = tuple(
        sorted(
            item.code
            for item in result.orders
            if item.order_id in baseline_by_id
            and baseline_by_id[item.order_id].slack_minutes is not None
            and baseline_by_id[item.order_id].slack_minutes >= state.settings.health_amber_minutes
            and (item.slack_minutes is None or item.slack_minutes < state.settings.health_amber_minutes)
        )
    )
    cost = fix_cost(actions, state)
    total_late = sum(
        max(0, -(item.slack_minutes or 0)) if item.slack_minutes is not None else 10**9 for item in late
    )
    outcome = FixOutcome(
        orders_on_time=len(result.orders) - len(late),
        orders_total=len(result.orders),
        orders_late_after=len(late),
        total_late_minutes=total_late,
        extra_cost_paise=cost.total_paise,
        changes_count=len(actions),
        collateral=collateral,
    )
    key = (
        outcome.orders_late_after,
        outcome.total_late_minutes,
        outcome.extra_cost_paise,
        outcome.changes_count,
        len(outcome.collateral),
        _candidate_key(actions),
    )
    return outcome, key


def _candidate_actions(state: MillState, baseline: Forecast, trigger: object) -> list[Action]:
    requested = tuple(_trigger_value(trigger, "affected_order_ids", ()))
    affected = (
        set(requested) if requested else {item.order_id for item in baseline.orders if item.health == "red"}
    )
    broken_id = _trigger_value(trigger, "machine_id", _trigger_value(trigger, "ref"))
    machine_by_id = {item.id: item for item in state.machines}
    candidates: list[Action] = []
    relevant_machines: set[str] = {str(broken_id)} if broken_id is not None else set()
    for job in sorted(state.jobs, key=lambda item: item.code):
        if job.order_id not in affected or job.status in {"done", "cancelled"}:
            continue
        if job.machine_id:
            relevant_machines.add(job.machine_id)
        compatible = sorted(
            (
                machine
                for machine in state.machines
                if machine.stage == job.stage
                and machine.unit == job.unit
                and (machine.capabilities is None or job.fabric_type_id in machine.capabilities)
            ),
            key=lambda item: item.code,
        )
        for machine in compatible:
            if machine.id != job.machine_id and not (
                machine.status in {"offline", "maintenance"} and machine.available_from <= state.now
            ):
                candidates.append(
                    {
                        "fn": "assign_job",
                        "args": {"job_id": job.id, "machine_id": machine.id, "queue_position": 1},
                    }
                )
        usable = [machine for machine in compatible if machine.id != broken_id]
        if len(usable) >= 2 and job.remaining_qty >= 2:
            for pair in combinations(usable[:3], 2):
                candidates.append(
                    {"fn": "split_job", "args": {"job_id": job.id, "machine_ids": (pair[0].id, pair[1].id)}}
                )
        if job.machine_id:
            ahead = sorted(
                (
                    other
                    for other in state.jobs
                    if other.machine_id == job.machine_id
                    and other.order_id not in affected
                    and (other.queue_position or 10**9) < (job.queue_position or 10**9)
                ),
                key=lambda item: (item.queue_position or 10**9, item.code),
            )
            for other in ahead[:1]:
                other_forecast = next(
                    (item for item in baseline.orders if item.order_id == other.order_id), None
                )
                affected_forecast = next(
                    (item for item in baseline.orders if item.order_id == job.order_id), None
                )
                lateness = max(0, -(affected_forecast.slack_minutes or 0)) if affected_forecast else 0
                if other_forecast and (other_forecast.slack_minutes or -1) > lateness:
                    candidates.append(
                        {"fn": "swap_jobs", "args": {"first_job_id": job.id, "second_job_id": other.id}}
                    )
    local_today = state.now.astimezone(ZoneInfo(state.settings.timezone)).date()
    for machine_id in sorted(relevant_machines):
        if machine_id not in machine_by_id:
            continue
        for offset in (0, 1):
            action_date = local_today + timedelta(days=offset)
            window = _overtime_window(state, action_date)
            if machine_id == broken_id and window.start < machine_by_id[machine_id].available_from:
                continue
            candidates.append(
                {
                    "fn": "assign_overtime",
                    "args": {
                        "machine_id": machine_id,
                        "date": action_date.isoformat(),
                        "shift_code": "C",
                    },
                }
            )
    for item in baseline.orders:
        if item.order_id in affected and item.bottleneck is not None and item.bottleneck.kind == "yarn":
            candidates.append(
                {
                    "fn": "expedite_yarn",
                    "args": {"yarn_type_id": item.bottleneck.ref, "date_needed": state.now.isoformat()},
                }
            )
    unique: dict[str, Action] = {}
    for candidate in candidates:
        unique[_candidate_key((candidate,))] = candidate
    return [unique[key] for key in sorted(unique)]


def find_fixes(
    state: MillState,
    baseline: Forecast,
    trigger: object,
    k: int = 3,
) -> tuple[Fix, ...]:
    if k <= 0:
        return ()
    singles = _candidate_actions(state, baseline, trigger)
    scored_singles = sorted(
        ((action, _evaluate(state, baseline, (action,))[1]) for action in singles),
        key=lambda item: item[1],
    )[:10]
    selected_singles = [item[0] for item in scored_singles]
    action_sets: list[tuple[Action, ...]] = [(item,) for item in selected_singles]
    action_sets.extend(
        (first, second)
        for first, second in combinations(selected_singles, 2)
        if _compatible_pair(first, second)
    )
    fixes: list[Fix] = []
    seen_outcomes: set[tuple[Any, ...]] = set()
    evaluated: list[tuple[tuple[Any, ...], tuple[Action, ...], FixOutcome]] = []
    for actions in action_sets:
        outcome, rank_key = _evaluate(state, baseline, actions)
        evaluated.append((rank_key, actions, outcome))
    for rank_key, actions, outcome in sorted(evaluated, key=lambda item: item[0]):
        outcome_key = (
            outcome.orders_late_after,
            outcome.total_late_minutes,
            outcome.extra_cost_paise,
            outcome.changes_count,
            outcome.collateral,
        )
        if outcome_key in seen_outcomes:
            continue
        seen_outcomes.add(outcome_key)
        kinds = tuple(
            dict.fromkeys(str(action.get("fn", "change")).removesuffix("_job") for action in actions)
        )
        kind = "+".join(kinds)
        fixes.append(
            Fix(
                kind=kind,
                actions=actions,
                title_key=f"ripple.fix.{kind.replace('+', '_')}",
                explanation_key="ripple.fix.outcome",
                params={
                    "orders_on_time": outcome.orders_on_time,
                    "orders_total": outcome.orders_total,
                    "extra_cost_paise": outcome.extra_cost_paise,
                },
                outcome=outcome,
                rank_key=rank_key,
            )
        )
        if len(fixes) == k:
            break
    return tuple(fixes)
