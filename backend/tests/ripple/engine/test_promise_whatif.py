from datetime import UTC, datetime, time, timedelta

from app.ripple.model import EngineSettings, JobState, MachineState, MillState, OrderState, YarnState
from app.ripple.promise import promise_date
from app.ripple.whatif import what_if

UTC = UTC
NOW = datetime(2026, 10, 12, 6, tzinfo=UTC)


def base_state(*, yarn: YarnState | None = None) -> MillState:
    settings = EngineSettings(
        timezone="UTC",
        regular_shifts=((time(0), time(0)),),
        qc_buffer_minutes=60,
        dispatch_buffer_minutes=60,
        horizon_days=7,
    )
    machines = (
        MachineState("SP-01", "SP-01", "spinning", "g", "idle", NOW, 600, {}, None, 10_000),
        MachineState("WV-01", "WV-01", "weaving", "cm", "idle", NOW, 600, {}, None, 45_000),
        MachineState("WV-02", "WV-02", "weaving", "cm", "idle", NOW, 900, {}, None, 45_000),
    )
    existing = OrderState(
        "ORD-100",
        "ORD-100",
        "buyer",
        "Existing Buyer",
        NOW + timedelta(days=3),
        "normal",
        500_000,
        600,
        "fabric-a",
        "cotton",
        0,
        "in_production",
        None,
        0,
        False,
    )
    existing_job = JobState(
        "J100",
        "J100",
        "ORD-100",
        "weaving",
        1,
        "cm",
        "fabric-a",
        600,
        "ready",
        None,
        None,
        False,
    )
    return MillState(NOW, 9, settings, machines, (existing_job,), (existing,), (yarn,) if yarn else ())


def draft(*, yarn_need: int = 0) -> dict[str, object]:
    return {
        "code": "DRAFT-1",
        "buyer_id": "new-buyer",
        "buyer_name": "New Buyer",
        "fabric_type_id": "fabric-a",
        "yarn_type_id": "cotton",
        "quantity_cm": 600,
        "yarn_needed_g": yarn_need,
        "route_stages": ("spinning", "weaving") if yarn_need else ("weaving",),
        "penalty_paise_per_day": 0,
    }


def test_promise_date_returns_same_day_without_yarn_constraint() -> None:
    result = promise_date(base_state(), draft(), "normal")

    assert result.earliest_dispatch_date.isoformat() == "2026-10-12"
    assert result.limiting_factor.startswith("machine:") or result.limiting_factor == "none"
    assert result.suggested_quote_key == "ripple.promise.quote"
    assert result.is_estimate is True


def test_promise_date_reports_yarn_condition_and_later_arrival_date() -> None:
    yarn = YarnState("cotton", 0, ((NOW + timedelta(days=1), 600),))

    result = promise_date(base_state(yarn=yarn), draft(yarn_need=600), "normal")

    assert result.earliest_dispatch_date.isoformat() == "2026-10-13"
    assert result.limiting_factor == "yarn"
    assert result.conditions[0].key == "ripple.promise.if_yarn_arrives"


def test_promise_date_offers_a_yarn_arrival_condition_when_stock_has_no_arrival() -> None:
    result = promise_date(base_state(yarn=YarnState("cotton", 0, ())), draft(yarn_need=600), "normal")

    assert result.earliest_dispatch_date is None
    assert result.limiting_factor == "yarn"
    assert result.conditions[0].params["needed_by"] == "2026-10-12"
    assert result.conditions[0].params["dispatch_date"] == "2026-10-12"


def test_promise_date_handles_no_capacity_within_horizon() -> None:
    state = base_state()
    unavailable = tuple(
        machine
        if machine.stage != "weaving"
        else MachineState(
            machine.id,
            machine.code,
            machine.stage,
            machine.unit,
            "offline",
            NOW,
            machine.default_speed_per_hour,
            machine.speeds,
            machine.capabilities,
            machine.idle_cost_paise_per_hour,
        )
        for machine in state.machines
    )

    unavailable_state = MillState(NOW, 9, state.settings, unavailable, state.jobs, state.orders, state.yarn)
    result = promise_date(unavailable_state, draft(), "normal")

    assert result.earliest_dispatch_date is None
    assert result.limiting_factor == "stage:weaving"


def test_breakdown_what_if_delays_forecast_without_mutating_input() -> None:
    state = base_state()
    original = hash(state)

    result = what_if(state, {"kind": "breakdown", "machine_id": "WV-02", "minutes": 720})

    assert hash(state) == original
    assert result.scenario_kind == "breakdown"
    assert result.after.state_version == state.version
    assert result.risk.idle_paise == 540_000


def test_yarn_delay_what_if_moves_arrival_without_mutating_input() -> None:
    yarn = YarnState("cotton", 0, ((NOW + timedelta(days=1), 600),))
    state = base_state(yarn=yarn)
    original = hash(state)

    result = what_if(state, {"kind": "yarn_delay", "yarn_type_id": "cotton", "days": 2})

    assert hash(state) == original
    assert result.scenario_kind == "yarn_delay"
    assert result.after.orders[0].predicted_dispatch_at is not None


def test_rush_order_what_if_adds_draft_without_mutating_input() -> None:
    state = base_state()
    original = hash(state)

    result = what_if(state, {"kind": "rush_order", "draft": draft()})

    assert hash(state) == original
    assert result.scenario_kind == "rush_order"
    assert len(result.after.orders) == len(result.before.orders) + 1
    assert (
        next(item for item in result.after.orders if item.order_id == "__promise_draft__").code == "DRAFT-1"
    )


def test_absence_what_if_removes_shift_window_from_named_machines() -> None:
    state = base_state()

    result = what_if(
        state,
        {
            "kind": "absence",
            "machine_ids": ("WV-01", "WV-02"),
            "shift": "A",
            "date": "2026-10-12",
        },
    )

    before = next(item for item in result.before.orders if item.order_id == "ORD-100")
    after = next(item for item in result.after.orders if item.order_id == "ORD-100")
    assert after.predicted_dispatch_at > before.predicted_dispatch_at
