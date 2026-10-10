from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import ceil, sqrt

from app.ripple.calendar import InsufficientCapacityError, advance, next_open, open_windows, regular_windows
from app.ripple.health import health_status
from app.ripple.model import (
    Bottleneck,
    Forecast,
    JobForecast,
    JobState,
    MachineForecast,
    MachineState,
    MillState,
    OrderForecast,
    TimelineEntry,
    Window,
)

STAGES = ("spinning", "weaving", "dyeing", "finishing")
PRIORITY = {"rush": 0, "high": 1, "normal": 2}
UNAVAILABLE_STATUSES = {"maintenance", "offline"}


@dataclass
class _MachinePlan:
    machine: MachineState
    windows: tuple[Window, ...]
    free_at: datetime
    last_fabric: str | None
    timeline: list[TimelineEntry]
    busy: list[Window]


@dataclass(frozen=True)
class _Placement:
    machine_id: str
    start_at: datetime
    end_at: datetime
    busy_start: datetime
    waiting_on: str | None
    duration_minutes: int
    cv: float
    constraint_delay: int
    bottleneck: Bottleneck | None


class _YarnLedger:
    def __init__(self, state: MillState, horizon_end: datetime) -> None:
        self._supply: dict[str, list[tuple[datetime, int]]] = {}
        self._allocated: defaultdict[str, int] = defaultdict(int)
        self._order_ready: dict[str, datetime | None] = {}
        self._horizon_end = horizon_end
        for yarn in state.yarn:
            supply = [(state.now, yarn.available_g), *yarn.arrivals]
            self._supply[yarn.yarn_type_id] = sorted(supply, key=lambda item: item[0])

    def allocate(self, state: MillState, order_id: str) -> datetime | None:
        if order_id in self._order_ready:
            return self._order_ready[order_id]
        order = next(item for item in state.orders if item.id == order_id)
        required = max(0, order.yarn_needed_remaining_g)
        target = self._allocated[order.yarn_type_id] + required
        cumulative = 0
        ready: datetime | None = state.now if required == 0 else None
        for at, quantity in self._supply.get(order.yarn_type_id, []):
            if at > self._horizon_end:
                break
            cumulative += quantity
            if cumulative >= target:
                ready = max(state.now, at)
                break
        if ready is not None:
            self._allocated[order.yarn_type_id] = target
        self._order_ready[order_id] = ready
        return ready


def _minutes_between(start: datetime, end: datetime) -> int:
    return int((end - start).total_seconds() // 60)


def _speed(machine: MachineState, fabric_type_id: str) -> tuple[int, int]:
    learned = machine.speeds.get(fabric_type_id)
    if learned is not None and learned[0] > 0:
        return learned
    return machine.default_speed_per_hour, 0


def _compatible(machine: MachineState, job: JobState) -> bool:
    return (
        machine.stage == job.stage
        and machine.unit == job.unit
        and (machine.capabilities is None or job.fabric_type_id in machine.capabilities)
    )


def _last_running_fabric(machine_id: str, jobs: Iterable[JobState]) -> str | None:
    running = sorted(
        (job for job in jobs if job.machine_id == machine_id and job.is_running),
        key=lambda job: job.code,
    )
    return running[0].fabric_type_id if running else None


def _waiting_source(
    now: datetime,
    machine_at: datetime,
    predecessor_at: datetime | None,
    yarn_at: datetime | None,
) -> tuple[datetime, str | None, Bottleneck | None]:
    choices: list[tuple[datetime, int, str | None, Bottleneck | None]] = [
        (now, 0, None, None),
        (machine_at, 1, "machine", None),
    ]
    if predecessor_at is not None:
        choices.append((predecessor_at, 2, "predecessor", None))
    if yarn_at is not None:
        choices.append((yarn_at, 3, "yarn", None))
    at, _, source, bottleneck = max(choices, key=lambda item: (item[0], item[1]))
    if at <= now:
        return now, None, None
    return at, source, bottleneck


def _place(
    state: MillState,
    job: JobState,
    plan: _MachinePlan,
    predecessor_at: datetime | None,
    yarn_at: datetime | None,
) -> _Placement | None:
    machine = plan.machine
    if not _compatible(machine, job) or not plan.windows:
        return None
    binding_at, source, _ = _waiting_source(state.now, plan.free_at, predecessor_at, yarn_at)
    opened = next_open(binding_at, plan.windows)
    if opened is None:
        return None
    waiting_on = "shift" if opened > binding_at else source
    busy_start = opened
    cursor = opened
    try:
        if plan.last_fabric is not None and plan.last_fabric != job.fabric_type_id:
            cursor = advance(cursor, state.settings.changeover_minutes, plan.windows)
        start_at = next_open(cursor, plan.windows)
        if start_at is None:
            return None
        speed, stddev = _speed(machine, job.fabric_type_id)
        if speed <= 0:
            return None
        duration = ceil(job.remaining_qty * 60 / speed)
        end_at = advance(start_at, duration, plan.windows)
    except InsufficientCapacityError:
        return None
    if source == "machine":
        bottleneck = Bottleneck("machine", machine.code)
    elif source == "predecessor":
        previous_index = max(0, STAGES.index(job.stage) - 1)
        bottleneck = Bottleneck("predecessor", STAGES[previous_index])
    elif source == "yarn":
        order = next(item for item in state.orders if item.id == job.order_id)
        bottleneck = Bottleneck("yarn", order.yarn_type_id)
    elif waiting_on == "shift":
        bottleneck = Bottleneck("machine", machine.code)
    else:
        bottleneck = None
    cv = stddev / speed if stddev > 0 else state.settings.default_cv_bp / 10_000
    return _Placement(
        machine_id=machine.id,
        start_at=start_at,
        end_at=end_at,
        busy_start=busy_start,
        waiting_on=waiting_on,
        duration_minutes=duration,
        cv=cv,
        constraint_delay=max(0, _minutes_between(state.now, start_at)),
        bottleneck=bottleneck,
    )


def _subtract_busy(windows: tuple[Window, ...], busy: list[Window]) -> tuple[Window, ...]:
    idle: list[Window] = []
    ordered_busy = sorted(busy, key=lambda item: (item.start, item.end))
    for window in windows:
        cursor = window.start
        for interval in ordered_busy:
            if interval.end <= cursor or interval.start >= window.end:
                continue
            if interval.start > cursor:
                idle.append(Window(cursor, min(interval.start, window.end)))
            cursor = max(cursor, interval.end)
            if cursor >= window.end:
                break
        if cursor < window.end:
            idle.append(Window(cursor, window.end))
    return tuple(idle)


def forecast(state: MillState) -> Forecast:
    horizon_end = state.now + timedelta(days=state.settings.horizon_days)
    order_by_id = {order.id: order for order in state.orders}
    active_jobs = [job for job in state.jobs if job.status not in {"done", "cancelled"}]
    plans: dict[str, _MachinePlan] = {}
    for machine in sorted(state.machines, key=lambda item: item.code):
        windows = open_windows(machine, state.settings, state.now, horizon_end)
        if machine.status in UNAVAILABLE_STATUSES and machine.available_from <= state.now:
            windows = ()
        plans[machine.id] = _MachinePlan(
            machine=machine,
            windows=windows,
            free_at=max(state.now, machine.available_from),
            last_fabric=_last_running_fabric(machine.id, active_jobs),
            timeline=[],
            busy=[],
        )

    results: dict[str, JobForecast] = {}
    placements: dict[str, _Placement] = {}
    yarn = _YarnLedger(state, horizon_end)
    yarn_ready_by_order: dict[str, datetime | None] = {}
    stages_by_order: dict[str, tuple[str, ...]] = {}
    for order in state.orders:
        present = {job.stage for job in state.jobs if job.order_id == order.id and job.status != "cancelled"}
        stages_by_order[order.id] = tuple(stage for stage in STAGES if stage in present)

    def predecessor_end(job: JobState) -> tuple[datetime | None, bool]:
        stage_index = STAGES.index(job.stage)
        previous = [
            stage for stage in stages_by_order.get(job.order_id, ()) if STAGES.index(stage) < stage_index
        ]
        if not previous:
            return None, True
        previous_stage = previous[-1]
        predecessors = [
            item
            for item in state.jobs
            if item.order_id == job.order_id and item.stage == previous_stage and item.status != "cancelled"
        ]
        if not predecessors:
            return None, True
        ends: list[datetime] = []
        for predecessor in predecessors:
            if predecessor.status == "done":
                ends.append(state.now)
            elif predecessor.id in results and results[predecessor.id].end_at is not None:
                ends.append(results[predecessor.id].end_at)  # type: ignore[arg-type]
            else:
                return None, False
        return max(ends), True

    def readiness(job: JobState) -> tuple[datetime | None, datetime | None, bool]:
        predecessor_at, predecessor_ok = predecessor_end(job)
        yarn_at: datetime | None = None
        order_stages = stages_by_order.get(job.order_id, ())
        is_first_stage = bool(order_stages) and job.stage == order_stages[0]
        if is_first_stage:
            if job.order_id not in yarn_ready_by_order:
                yarn_ready_by_order[job.order_id] = yarn.allocate(state, job.order_id)
            yarn_at = yarn_ready_by_order[job.order_id]
            if yarn_at is None:
                return predecessor_at, None, False
        return predecessor_at, yarn_at, predecessor_ok

    def commit(job: JobState, placement: _Placement, virtual: bool) -> None:
        plan = plans[placement.machine_id]
        plan.free_at = placement.end_at
        plan.last_fabric = job.fabric_type_id
        plan.timeline.append(TimelineEntry(job.id, placement.start_at, placement.end_at))
        plan.busy.append(Window(placement.busy_start, placement.end_at))
        placements[job.id] = placement
        results[job.id] = JobForecast(
            job_id=job.id,
            machine_id=placement.machine_id,
            start_at=placement.start_at,
            end_at=placement.end_at,
            waiting_on=placement.waiting_on,
            virtual_assignment=virtual,
        )

    for stage in STAGES:
        stage_jobs = [job for job in active_jobs if job.stage == stage]
        assigned = [job for job in stage_jobs if job.machine_id is not None]
        for machine_id in sorted(plans, key=lambda item: plans[item].machine.code):
            queue = sorted(
                (job for job in assigned if job.machine_id == machine_id),
                key=lambda job: (
                    not job.is_running,
                    job.queue_position if job.queue_position is not None else 10**9,
                    job.code,
                ),
            )
            for job in queue:
                predecessor_at, yarn_at, ready = readiness(job)
                placement = _place(state, job, plans[machine_id], predecessor_at, yarn_at) if ready else None
                if placement is None:
                    is_first = stages_by_order.get(job.order_id, (None,))[0] == stage
                    waiting = "yarn" if yarn_at is None and is_first else "predecessor"
                    results[job.id] = JobForecast(job.id, machine_id, None, None, waiting, False)
                else:
                    commit(job, placement, False)

        unassigned = sorted(
            (job for job in stage_jobs if job.machine_id is None),
            key=lambda job: (
                PRIORITY.get(order_by_id[job.order_id].priority, 2),
                order_by_id[job.order_id].due_at,
                order_by_id[job.order_id].code,
                job.seq,
                job.code,
            ),
        )
        for job in unassigned:
            predecessor_at, yarn_at, ready = readiness(job)
            candidates: list[tuple[datetime, str, _Placement]] = []
            if ready:
                for plan in plans.values():
                    placement = _place(state, job, plan, predecessor_at, yarn_at)
                    if placement is not None:
                        candidates.append((placement.end_at, plan.machine.code, placement))
            if not candidates:
                is_first = stages_by_order.get(job.order_id, (None,))[0] == stage
                waiting = "yarn" if yarn_at is None and is_first else "predecessor"
                results[job.id] = JobForecast(job.id, None, None, None, waiting, True)
            else:
                _, _, chosen = min(candidates, key=lambda item: (item[0], item[1]))
                commit(job, chosen, True)

    for job in state.jobs:
        if job.status == "done":
            results[job.id] = JobForecast(job.id, job.machine_id, state.now, state.now, None, False)
        elif job.status == "cancelled":
            results[job.id] = JobForecast(job.id, job.machine_id, None, None, None, False)

    staff_windows = regular_windows(state.settings, state.now, horizon_end)
    order_results: list[OrderForecast] = []
    for order in sorted(state.orders, key=lambda item: item.code):
        order_jobs = [job for job in state.jobs if job.order_id == order.id and job.status != "cancelled"]
        predicted: datetime | None
        bottleneck: Bottleneck | None = None
        confidence_terms: list[float] = []
        if order.production_done:
            production_end = state.now
        elif not order_jobs:
            production_end = None
            bottleneck = Bottleneck("stage", "production")
        else:
            final_index = max(STAGES.index(job.stage) for job in order_jobs)
            final_jobs = [job for job in order_jobs if STAGES.index(job.stage) == final_index]
            final_ends = [results[job.id].end_at for job in final_jobs]
            production_end = max(final_ends) if final_ends and all(final_ends) else None
            if production_end is None:
                unscheduled = next(
                    (job for job in final_jobs if results[job.id].end_at is None), final_jobs[0]
                )
                if results[unscheduled.id].waiting_on == "yarn":
                    bottleneck = Bottleneck("yarn", order.yarn_type_id)
                else:
                    bottleneck = Bottleneck("stage", unscheduled.stage)
        order_placements = [placements[job.id] for job in order_jobs if job.id in placements]
        confidence_terms.extend((item.duration_minutes * item.cv) ** 2 for item in order_placements)
        if bottleneck is None and order_placements:
            delayed = max(order_placements, key=lambda item: (item.constraint_delay, item.machine_id))
            bottleneck = delayed.bottleneck
        if production_end is None:
            predicted = None
        else:
            try:
                predicted = advance(
                    production_end,
                    state.settings.qc_buffer_minutes + state.settings.dispatch_buffer_minutes,
                    staff_windows,
                )
            except InsufficientCapacityError:
                predicted = None
        slack = None if predicted is None else _minutes_between(predicted, order.due_at)
        order_results.append(
            OrderForecast(
                order_id=order.id,
                code=order.code,
                predicted_dispatch_at=predicted,
                due_at=order.due_at,
                slack_minutes=slack,
                health=health_status(slack, state.settings.health_amber_minutes),
                confidence_minutes=round(sqrt(sum(confidence_terms))),
                bottleneck=bottleneck,
            )
        )

    machine_results = tuple(
        MachineForecast(
            machine_id=plan.machine.id,
            timeline=tuple(sorted(plan.timeline, key=lambda item: (item.start_at, item.job_id))),
            idle_windows=_subtract_busy(plan.windows, plan.busy),
        )
        for plan in sorted(plans.values(), key=lambda item: item.machine.code)
    )
    return Forecast(
        computed_at=state.now,
        state_version=state.version,
        orders=tuple(order_results),
        jobs=tuple(results[job.id] for job in sorted(state.jobs, key=lambda item: item.code)),
        machines=machine_results,
    )
