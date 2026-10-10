import json
from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta

from app.ripple.forecast import forecast
from app.ripple.model import EngineSettings, JobState, MachineState, MillState, OrderState, Window, YarnState

UTC = UTC
NOW = datetime(2026, 10, 12, tzinfo=UTC)


def settings(**changes: object) -> EngineSettings:
    base = EngineSettings(
        timezone="UTC",
        regular_shifts=((time(0), time(0)),),
        qc_buffer_minutes=60,
        dispatch_buffer_minutes=60,
        horizon_days=5,
    )
    return replace(base, **changes)


def machine(
    code: str,
    stage: str,
    *,
    available_from: datetime = NOW,
    speed: int = 600,
    learned: dict[str, tuple[int, int]] | None = None,
    overtime: tuple[Window, ...] = (),
) -> MachineState:
    return MachineState(
        id=code,
        code=code,
        stage=stage,
        unit="g" if stage == "spinning" else "cm",
        status="idle",
        available_from=available_from,
        default_speed_per_hour=speed,
        speeds=learned or {},
        capabilities=None,
        idle_cost_paise_per_hour=45_000,
        overtime_windows=overtime,
    )


def order(code: str = "ORD-101", *, yarn_need: int = 0, priority: str = "normal") -> OrderState:
    return OrderState(
        id=code,
        code=code,
        buyer_id="buyer",
        buyer_name="Buyer",
        due_at=NOW + timedelta(days=2),
        priority=priority,
        penalty_paise_per_day=500_000,
        quantity_cm=600,
        fabric_type_id="fabric-a",
        yarn_type_id="cotton",
        yarn_needed_remaining_g=yarn_need,
        status="in_production",
        promised_date=date(2026, 10, 14),
        rolls_pending_qc=0,
        production_done=False,
    )


def job(
    code: str,
    stage: str,
    *,
    machine_id: str | None,
    seq: int,
    qty: int = 600,
    fabric: str = "fabric-a",
    order_id: str = "ORD-101",
    queue: int | None = 1,
    running: bool = False,
) -> JobState:
    return JobState(
        id=code,
        code=code,
        order_id=order_id,
        stage=stage,
        seq=seq,
        unit="g" if stage == "spinning" else "cm",
        fabric_type_id=fabric,
        remaining_qty=qty,
        status="running" if running else "ready",
        machine_id=machine_id,
        queue_position=queue,
        is_running=running,
    )


def state(
    machines: tuple[MachineState, ...],
    jobs: tuple[JobState, ...],
    *,
    orders: tuple[OrderState, ...] | None = None,
    yarn: tuple[YarnState, ...] = (),
    engine_settings: EngineSettings | None = None,
) -> MillState:
    return MillState(
        now=NOW,
        version=7,
        settings=engine_settings or settings(),
        machines=machines,
        jobs=jobs,
        orders=orders or (order(),),
        yarn=yarn,
    )


def test_single_job_forecasts_work_then_qc_and_dispatch_buffers() -> None:
    result = forecast(
        state((machine("WV-01", "weaving"),), (job("J1", "weaving", machine_id="WV-01", seq=1),))
    )

    assert result.jobs[0].start_at == NOW
    assert result.jobs[0].end_at == NOW + timedelta(hours=1)
    assert result.orders[0].predicted_dispatch_at == NOW + timedelta(hours=3)
    assert result.orders[0].slack_minutes == 2_700
    assert result.orders[0].health == "green"
    assert result.to_dict()["computed_at"] == "2026-10-12T00:00:00+00:00"
    assert result.to_dict()["is_estimate"] is True


def test_predecessor_chain_waits_across_three_stages() -> None:
    result = forecast(
        state(
            (
                machine("SP-01", "spinning"),
                machine("WV-01", "weaving"),
                machine("DY-01", "dyeing"),
            ),
            (
                job("SP", "spinning", machine_id="SP-01", seq=1),
                job("WV", "weaving", machine_id="WV-01", seq=2),
                job("DY", "dyeing", machine_id="DY-01", seq=3),
            ),
            yarn=(YarnState("cotton", 1_000, ()),),
        )
    )
    by_id = {item.job_id: item for item in result.jobs}

    assert by_id["WV"].start_at == by_id["SP"].end_at
    assert by_id["DY"].start_at == by_id["WV"].end_at
    assert by_id["WV"].waiting_on == "predecessor"


def test_virtual_assignment_chooses_earliest_finish_then_machine_code() -> None:
    result = forecast(
        state(
            (
                machine("WV-01", "weaving", available_from=NOW + timedelta(hours=2)),
                machine("WV-02", "weaving"),
            ),
            (job("J1", "weaving", machine_id=None, seq=1, queue=None),),
        )
    )

    assert result.jobs[0].machine_id == "WV-02"
    assert result.jobs[0].virtual_assignment is True


def test_changeover_is_added_only_when_fabric_changes() -> None:
    result = forecast(
        state(
            (machine("WV-01", "weaving"),),
            (
                job("J1", "weaving", machine_id="WV-01", seq=1, fabric="fabric-a", running=True),
                job("J2", "weaving", machine_id="WV-01", seq=2, fabric="fabric-a", queue=2),
                job("J3", "weaving", machine_id="WV-01", seq=3, fabric="fabric-b", queue=3),
            ),
        )
    )
    by_id = {item.job_id: item for item in result.jobs}

    assert by_id["J2"].start_at == by_id["J1"].end_at
    assert by_id["J3"].start_at == by_id["J2"].end_at + timedelta(minutes=45)


def test_yarn_shortage_blocks_first_stage_until_arrival() -> None:
    arrival = NOW + timedelta(hours=5)
    result = forecast(
        state(
            (machine("SP-01", "spinning"),),
            (job("SP", "spinning", machine_id="SP-01", seq=1),),
            orders=(order(yarn_need=800),),
            yarn=(YarnState("cotton", 300, ((arrival, 500),)),),
        )
    )

    assert result.jobs[0].start_at == arrival
    assert result.jobs[0].waiting_on == "yarn"


def test_yarn_shortage_without_arrival_is_unschedulable() -> None:
    result = forecast(
        state(
            (machine("SP-01", "spinning"),),
            (job("SP", "spinning", machine_id="SP-01", seq=1),),
            orders=(order(yarn_need=800),),
            yarn=(YarnState("cotton", 300, ()),),
        )
    )

    assert result.jobs[0].end_at is None
    assert result.orders[0].predicted_dispatch_at is None
    assert result.orders[0].health == "red"
    assert result.orders[0].bottleneck.to_dict() == {"kind": "yarn", "ref": "cotton"}


def test_yarn_gates_the_first_route_stage_even_when_route_starts_at_weaving() -> None:
    arrival = NOW + timedelta(hours=4)
    result = forecast(
        state(
            (machine("WV-01", "weaving"),),
            (job("WV", "weaving", machine_id="WV-01", seq=1),),
            orders=(order(yarn_need=800),),
            yarn=(YarnState("cotton", 300, ((arrival, 500),)),),
        )
    )

    assert result.jobs[0].start_at == arrival
    assert result.jobs[0].waiting_on == "yarn"


def test_full_mill_state_to_dict_is_json_safe() -> None:
    value = state(
        (machine("WV-01", "weaving", learned={"fabric-a": (1_200, 120)}),),
        (job("WV", "weaving", machine_id="WV-01", seq=1),),
    )

    encoded = json.dumps(value.to_dict())

    assert '"fabric-a": [1200, 120]' in encoded


def test_breakdown_available_from_delays_assigned_queue() -> None:
    repaired = NOW + timedelta(hours=6)
    result = forecast(
        state(
            (machine("WV-01", "weaving", available_from=repaired),),
            (job("J1", "weaving", machine_id="WV-01", seq=1),),
        )
    )
    assert result.jobs[0].start_at == repaired
    assert result.jobs[0].waiting_on == "machine"


def test_overtime_window_shortens_finish() -> None:
    start = NOW.replace(hour=13)
    regular = settings(regular_shifts=((time(6), time(14)),), qc_buffer_minutes=0, dispatch_buffer_minutes=0)
    base = replace(
        state((), (), engine_settings=regular),
        now=start,
        machines=(machine("WV-01", "weaving", available_from=start, speed=60),),
        jobs=(job("J1", "weaving", machine_id="WV-01", seq=1, qty=120),),
    )
    overtime_machine = replace(
        base.machines[0], overtime_windows=(Window(start.replace(hour=14), start.replace(hour=16)),)
    )

    regular_result = forecast(base)
    overtime_result = forecast(replace(base, machines=(overtime_machine,)))

    assert regular_result.jobs[0].end_at == NOW + timedelta(days=1, hours=7)
    assert overtime_result.jobs[0].end_at == start.replace(hour=15)


def test_learned_speed_overrides_default_and_sets_confidence() -> None:
    result = forecast(
        state(
            (machine("WV-01", "weaving", speed=600, learned={"fabric-a": (1_200, 120)}),),
            (job("J1", "weaving", machine_id="WV-01", seq=1),),
        )
    )

    assert result.jobs[0].end_at == NOW + timedelta(minutes=30)
    assert result.orders[0].confidence_minutes == 3
