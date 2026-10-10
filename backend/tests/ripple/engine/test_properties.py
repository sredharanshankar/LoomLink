from dataclasses import replace
from datetime import UTC, datetime, time, timedelta
from math import ceil
from time import perf_counter

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.ripple.calendar import open_windows
from app.ripple.forecast import forecast
from app.ripple.model import EngineSettings, JobState, MachineState, MillState, OrderState, Window

UTC = UTC
NOW = datetime(2026, 10, 12, 6, tzinfo=UTC)


def engine_settings(*, shifts: tuple[tuple[time, time], ...] = ((time(0), time(0)),)) -> EngineSettings:
    return EngineSettings(
        timezone="UTC",
        regular_shifts=shifts,
        qc_buffer_minutes=0,
        dispatch_buffer_minutes=0,
        horizon_days=10,
    )


def machine(
    code: str, stage: str = "weaving", *, speed: int = 600, available: datetime = NOW
) -> MachineState:
    return MachineState(
        code,
        code,
        stage,
        "g" if stage == "spinning" else "cm",
        "idle",
        available,
        speed,
        {},
        None,
        10_000,
    )


def order(index: int, *, due: datetime | None = None) -> OrderState:
    code = f"ORD-{index:03d}"
    return OrderState(
        code,
        code,
        "buyer",
        "Buyer",
        due or NOW + timedelta(days=8),
        "normal",
        0,
        1_000,
        "fabric",
        "yarn",
        0,
        "in_production",
        None,
        0,
        False,
    )


def job(
    index: int,
    order_id: str,
    *,
    stage: str = "weaving",
    machine_id: str | None = "WV-01",
    qty: int = 600,
) -> JobState:
    return JobState(
        f"J-{index:03d}",
        f"J-{index:03d}",
        order_id,
        stage,
        {"spinning": 1, "weaving": 2, "dyeing": 3}.get(stage, 4),
        "g" if stage == "spinning" else "cm",
        "fabric",
        qty,
        "ready",
        machine_id,
        index,
        False,
    )


def mill(
    machines: tuple[MachineState, ...],
    jobs: tuple[JobState, ...],
    orders: tuple[OrderState, ...],
    *,
    configured: EngineSettings | None = None,
    now: datetime = NOW,
) -> MillState:
    return MillState(now, 1, configured or engine_settings(), machines, jobs, orders, ())


@given(st.lists(st.integers(min_value=1, max_value=2_000), min_size=1, max_size=12))
def test_machine_intervals_never_overlap(quantities: list[int]) -> None:
    orders = tuple(order(index) for index in range(len(quantities)))
    jobs = tuple(job(index, orders[index].id, qty=quantity) for index, quantity in enumerate(quantities))

    result = forecast(mill((machine("WV-01"),), jobs, orders))

    timeline = result.machines[0].timeline
    assert all(first.end_at <= second.start_at for first, second in zip(timeline, timeline[1:], strict=False))


@given(st.integers(min_value=1, max_value=2_000))
def test_every_job_starts_after_all_previous_stage_work(qty: int) -> None:
    one_order = order(1)
    machines = (machine("SP-01", "spinning"), machine("WV-01"), machine("DY-01", "dyeing"))
    jobs = (
        job(1, one_order.id, stage="spinning", machine_id="SP-01", qty=qty),
        job(2, one_order.id, stage="weaving", machine_id="WV-01", qty=qty),
        job(3, one_order.id, stage="dyeing", machine_id="DY-01", qty=qty),
    )

    result = forecast(mill(machines, jobs, (one_order,)))
    by_id = {item.job_id: item for item in result.jobs}

    assert by_id["J-002"].start_at >= by_id["J-001"].end_at
    assert by_id["J-003"].start_at >= by_id["J-002"].end_at


@given(
    qty=st.integers(min_value=1, max_value=8_000),
    speed=st.integers(min_value=100, max_value=1_200),
)
def test_scheduled_work_minutes_all_fall_in_open_windows(qty: int, speed: int) -> None:
    configured = engine_settings(shifts=((time(6), time(14)),))
    one_order = order(1)
    one_machine = machine("WV-01", speed=speed)
    state = mill((one_machine,), (job(1, one_order.id, qty=qty),), (one_order,), configured=configured)

    result = forecast(state)
    scheduled = result.jobs[0]
    windows = open_windows(one_machine, configured, state.now, state.now + timedelta(days=10))
    open_minutes = sum(
        max(
            0,
            int(
                (min(window.end, scheduled.end_at) - max(window.start, scheduled.start_at)).total_seconds()
                // 60
            ),
        )
        for window in windows
        if window.end > scheduled.start_at and window.start < scheduled.end_at
    )

    assert open_minutes == ceil(qty * 60 / speed)


@given(st.lists(st.integers(min_value=1, max_value=2_000), min_size=1, max_size=8))
def test_same_input_always_produces_identical_forecast(quantities: list[int]) -> None:
    orders = tuple(order(index) for index in range(len(quantities)))
    jobs = tuple(
        job(index, orders[index].id, machine_id=None, qty=quantity)
        for index, quantity in enumerate(quantities)
    )
    state = mill((machine("WV-01"), machine("WV-02")), jobs, orders)

    assert forecast(state) == forecast(state)


@given(
    earlier=st.integers(min_value=0, max_value=600),
    extra=st.integers(min_value=0, max_value=600),
    qty=st.integers(min_value=1, max_value=2_000),
)
def test_moving_machine_availability_later_never_dispatches_earlier(
    earlier: int, extra: int, qty: int
) -> None:
    one_order = order(1)
    one_job = job(1, one_order.id, qty=qty)
    early_state = mill(
        (machine("WV-01", available=NOW + timedelta(minutes=earlier)),), (one_job,), (one_order,)
    )
    late_state = replace(
        early_state,
        machines=(machine("WV-01", available=NOW + timedelta(minutes=earlier + extra)),),
    )

    early_dispatch = forecast(early_state).orders[0].predicted_dispatch_at
    late_dispatch = forecast(late_state).orders[0].predicted_dispatch_at

    assert late_dispatch >= early_dispatch


@given(qty=st.integers(min_value=1, max_value=8_000), speed=st.integers(min_value=100, max_value=1_200))
def test_adding_overtime_never_makes_dispatch_later(qty: int, speed: int) -> None:
    configured = engine_settings(shifts=((time(6), time(14)),))
    one_order = order(1)
    regular_machine = machine("WV-01", speed=speed)
    state = mill(
        (regular_machine,),
        (job(1, one_order.id, qty=qty),),
        (one_order,),
        configured=configured,
        now=NOW.replace(hour=13),
    )
    overtime = Window(NOW.replace(hour=14), NOW.replace(hour=22))
    overtime_state = replace(state, machines=(replace(regular_machine, overtime_windows=(overtime,)),))

    regular_dispatch = forecast(state).orders[0].predicted_dispatch_at
    overtime_dispatch = forecast(overtime_state).orders[0].predicted_dispatch_at

    assert regular_dispatch is None or (
        overtime_dispatch is not None and overtime_dispatch <= regular_dispatch
    )


@pytest.mark.slow
def test_forecast_50_machines_400_jobs_under_200_ms() -> None:
    machines = tuple(machine(f"WV-{index:02d}", speed=2_000) for index in range(50))
    orders = tuple(order(index) for index in range(400))
    jobs = tuple(
        job(index, orders[index].id, machine_id=machines[index % len(machines)].id, qty=1_000)
        for index in range(400)
    )
    state = mill(machines, jobs, orders)

    started = perf_counter()
    result = forecast(state)
    elapsed = perf_counter() - started

    assert len(result.jobs) == 400
    assert elapsed < 0.2
