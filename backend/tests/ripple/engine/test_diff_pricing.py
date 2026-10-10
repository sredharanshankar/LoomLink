from dataclasses import replace
from datetime import UTC, datetime, time, timedelta

import pytest

from app.ripple.diff import ripple_diff
from app.ripple.model import (
    EngineSettings,
    Forecast,
    JobState,
    MachineForecast,
    MachineState,
    MillState,
    OrderForecast,
    OrderState,
    Window,
)
from app.ripple.pricing import at_risk, fix_cost, late_penalty_days

UTC = UTC
NOW = datetime(2026, 10, 12, 6, tzinfo=UTC)


def order_forecast(code: str, slack: int, health: str, *, dispatch_offset: int) -> OrderForecast:
    return OrderForecast(
        order_id=code,
        code=code,
        predicted_dispatch_at=NOW + timedelta(minutes=dispatch_offset),
        due_at=NOW + timedelta(minutes=dispatch_offset + slack),
        slack_minutes=slack,
        health=health,
        confidence_minutes=10,
        bottleneck=None,
    )


def snapshot(*orders: OrderForecast, idle_minutes: int = 60) -> Forecast:
    return Forecast(
        computed_at=NOW,
        state_version=1,
        orders=orders,
        jobs=(),
        machines=(
            MachineForecast(
                machine_id="WV-02",
                timeline=(),
                idle_windows=(Window(NOW, NOW + timedelta(minutes=idle_minutes)),),
            ),
        ),
    )


def mill_state() -> MillState:
    settings = EngineSettings(
        timezone="UTC",
        regular_shifts=((time(6), time(22)),),
        penalty_grace_minutes=240,
    )
    machine = MachineState(
        id="WV-02",
        code="WV-02",
        stage="weaving",
        unit="cm",
        status="breakdown",
        available_from=NOW + timedelta(hours=6),
        default_speed_per_hour=2_000,
        speeds={},
        capabilities=None,
        idle_cost_paise_per_hour=45_000,
    )
    orders = (
        OrderState(
            id="ORD-104",
            code="ORD-104",
            buyer_id="b1",
            buyer_name="Alpha",
            due_at=NOW + timedelta(days=1),
            priority="high",
            penalty_paise_per_day=300_000,
            quantity_cm=70_000,
            fabric_type_id="fa",
            yarn_type_id="ya",
            yarn_needed_remaining_g=0,
            status="in_production",
            promised_date=None,
            rolls_pending_qc=0,
            production_done=False,
        ),
        OrderState(
            id="ORD-107",
            code="ORD-107",
            buyer_id="b2",
            buyer_name="Beta",
            due_at=NOW + timedelta(days=1),
            priority="normal",
            penalty_paise_per_day=500_000,
            quantity_cm=100_000,
            fabric_type_id="fb",
            yarn_type_id="yb",
            yarn_needed_remaining_g=0,
            status="in_production",
            promised_date=None,
            rolls_pending_qc=0,
            production_done=False,
        ),
    )
    return MillState(NOW, 1, settings, (machine,), (), orders, ())


def test_ripple_diff_marks_newly_late_and_threshold_slips_then_sorts_by_after_slack() -> None:
    before = snapshot(
        order_forecast("ORD-104", 120, "amber", dispatch_offset=100),
        order_forecast("ORD-107", 2_000, "green", dispatch_offset=100),
        order_forecast("ORD-109", 2_000, "green", dispatch_offset=100),
        idle_minutes=60,
    )
    after = snapshot(
        order_forecast("ORD-104", -30, "red", dispatch_offset=250),
        order_forecast("ORD-107", 1_900, "green", dispatch_offset=200),
        order_forecast("ORD-109", 1_980, "green", dispatch_offset=120),
        idle_minutes=180,
    )

    result = ripple_diff(before, after, EngineSettings(slip_threshold_minutes=60))

    assert [item.code for item in result.affected_orders] == ["ORD-104", "ORD-107"]
    assert result.affected_orders[0].newly_late is True
    assert result.affected_orders[1].worsened is True
    assert result.affected_orders[1].delta_minutes == 100
    assert result.machine_idle_changes[0].delta_minutes == 120


def test_ripple_diff_does_not_mark_recovery_from_unschedulable_as_worsened() -> None:
    blocked = OrderForecast(
        order_id="ORD-104",
        code="ORD-104",
        predicted_dispatch_at=None,
        due_at=NOW + timedelta(days=1),
        slack_minutes=None,
        health="red",
        confidence_minutes=0,
        bottleneck=None,
    )
    recovered = order_forecast("ORD-104", 300, "amber", dispatch_offset=100)

    result = ripple_diff(snapshot(blocked), snapshot(recovered), EngineSettings())

    assert result.orders[0].worsened is False
    assert result.affected_orders == ()


@pytest.mark.parametrize(
    ("late", "expected"),
    [(239, 0), (240, 0), (241, 1), (1_681, 2)],
)
def test_late_penalty_days_obeys_grace_boundary(late: int, expected: int) -> None:
    assert late_penalty_days(late, 240) == expected


def test_at_risk_combines_open_window_breakdown_idle_and_only_new_lateness() -> None:
    before = snapshot(
        order_forecast("ORD-104", 120, "amber", dispatch_offset=100),
        order_forecast("ORD-107", 60, "amber", dispatch_offset=100),
    )
    after = snapshot(
        order_forecast("ORD-104", -200, "red", dispatch_offset=420),
        order_forecast("ORD-107", -1_680, "red", dispatch_offset=1_840),
    )
    state = mill_state()
    diff = ripple_diff(before, after, state.settings)

    risk = at_risk(state, diff, {"kind": "breakdown", "machine_id": "WV-02"})

    assert risk.idle_paise == 270_000
    assert [(item.order_code, item.days, item.paise) for item in risk.penalties] == [("ORD-107", 1, 500_000)]
    assert risk.total_paise == 770_000
    assert risk.assumptions["grace_minutes"] == 240


def test_fix_cost_prices_overtime_and_new_changeover_and_states_expedite_assumption() -> None:
    state = mill_state()
    actions = [
        {"fn": "assign_overtime", "args": {"machine_id": "WV-02", "date": "2026-10-12", "shift_code": "C"}},
        {"fn": "changeover", "args": {"machine_id": "WV-02"}},
        {"fn": "expedite_yarn", "args": {"yarn_type_id": "cotton"}},
    ]

    cost = fix_cost(actions, state)

    assert cost.total_paise == 210_000
    assert cost.overtime_paise == 120_000
    assert cost.changeover_paise == 90_000
    assert cost.assumptions["expedite_paise"] == 0


def test_fix_cost_prices_each_split_machine_changeover() -> None:
    state = mill_state()
    split_job = JobState(
        "J107", "J107", "ORD-107", "weaving", 1, "cm", "fb", 1_000, "ready", "WV-02", 1, False
    )
    first_machine = replace(state.machines[0], id="WV-01", code="WV-01", status="idle", available_from=NOW)
    third_machine = replace(state.machines[0], id="WV-03", code="WV-03", status="idle", available_from=NOW)
    state = replace(state, machines=(state.machines[0], first_machine, third_machine), jobs=(split_job,))

    cost = fix_cost(
        ({"fn": "split_job", "args": {"job_id": "J107", "machine_ids": ("WV-01", "WV-03")}},),
        state,
    )

    assert cost.changeover_paise == 180_000
