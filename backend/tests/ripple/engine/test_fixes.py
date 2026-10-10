from datetime import UTC, datetime, time, timedelta

from app.ripple.fixes import apply_actions_virtually, find_fixes
from app.ripple.forecast import forecast
from app.ripple.model import EngineSettings, JobState, MachineState, MillState, OrderState

UTC = UTC
NOW = datetime(2026, 10, 12, 6, tzinfo=UTC)


def mini_mill() -> MillState:
    settings = EngineSettings(
        timezone="UTC",
        regular_shifts=((time(0), time(0)),),
        qc_buffer_minutes=0,
        dispatch_buffer_minutes=0,
        health_amber_minutes=300,
        horizon_days=3,
    )
    machines = (
        MachineState("WV-01", "WV-01", "weaving", "cm", "idle", NOW, 600, {}, None, 45_000),
        MachineState(
            "WV-02", "WV-02", "weaving", "cm", "breakdown", NOW + timedelta(hours=8), 600, {}, None, 45_000
        ),
    )
    order = OrderState(
        "ORD-104",
        "ORD-104",
        "buyer",
        "Buyer",
        NOW + timedelta(hours=4),
        "high",
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
    job = JobState("J104", "J104", "ORD-104", "weaving", 1, "cm", "fabric-a", 600, "ready", "WV-02", 1, False)
    return MillState(NOW, 1, settings, machines, (job,), (order,), ())


def test_apply_actions_virtually_reassigns_without_mutating_state() -> None:
    state = mini_mill()
    actions = ({"fn": "assign_job", "args": {"job_id": "J104", "machine_id": "WV-01", "queue_position": 1}},)

    changed = apply_actions_virtually(state, actions)

    assert state.jobs[0].machine_id == "WV-02"
    assert changed.jobs[0].machine_id == "WV-01"
    assert forecast(changed).orders[0].health != "red"


def test_find_fixes_returns_ranked_serialisable_reassignment_with_outcome() -> None:
    state = mini_mill()
    baseline = forecast(state)

    fixes = find_fixes(
        state,
        baseline,
        {"kind": "breakdown", "machine_id": "WV-02", "affected_order_ids": ("ORD-104",)},
        k=3,
    )

    assert fixes
    assert fixes[0].outcome.orders_late_after == 0
    assert any(action["fn"] == "assign_job" for action in fixes[0].actions)
    assert fixes == tuple(sorted(fixes, key=lambda item: item.rank_key))
    assert fixes[0].to_dict()["actions"][0]["fn"] in {"assign_job", "split_job", "assign_overtime"}


def test_fix_ranking_matches_reassign_overtime_split_story_shape() -> None:
    now = NOW.replace(hour=11)
    settings = EngineSettings(
        timezone="UTC",
        regular_shifts=((time(6), time(14)), (time(14), time(22))),
        qc_buffer_minutes=0,
        dispatch_buffer_minutes=0,
        horizon_days=3,
    )
    machines = (
        MachineState(
            "WV-01", "WV-01", "weaving", "cm", "running", now, 20_000, {}, frozenset({"fa", "fb"}), 45_000
        ),
        MachineState(
            "WV-02",
            "WV-02",
            "weaving",
            "cm",
            "breakdown",
            now + timedelta(hours=6),
            10_000,
            {},
            frozenset({"fa", "fb"}),
            45_000,
        ),
        MachineState(
            "WV-03",
            "WV-03",
            "weaving",
            "cm",
            "idle",
            now.replace(hour=18),
            10_000,
            {},
            frozenset({"fb"}),
            45_000,
        ),
    )

    def story_order(code: str, due: datetime, fabric: str) -> OrderState:
        return OrderState(
            code,
            code,
            "buyer",
            "Buyer",
            due,
            "high" if code == "ORD-104" else "normal",
            500_000,
            100_000,
            fabric,
            "cotton",
            0,
            "in_production",
            None,
            0,
            False,
        )

    orders = (
        story_order("ORD-104", now.replace(hour=22), "fa"),
        story_order("ORD-107", (now + timedelta(days=1)).replace(hour=6, minute=10), "fb"),
        story_order("ORD-109", now + timedelta(days=2), "fa"),
    )
    jobs = (
        JobState("J109", "J109", "ORD-109", "weaving", 1, "cm", "fa", 30_000, "running", "WV-01", 1, True),
        JobState("J104", "J104", "ORD-104", "weaving", 1, "cm", "fa", 70_000, "ready", "WV-02", 1, False),
        JobState("J107", "J107", "ORD-107", "weaving", 1, "cm", "fb", 54_000, "ready", "WV-02", 2, False),
    )
    state = MillState(now, 1, settings, machines, jobs, orders, ())
    baseline = forecast(state)

    fixes = find_fixes(
        state,
        baseline,
        {
            "kind": "breakdown",
            "machine_id": "WV-02",
            "affected_order_ids": ("ORD-104", "ORD-107"),
        },
        k=3,
    )

    assert [tuple(action["fn"] for action in fix.actions) for fix in fixes] == [
        ("assign_job", "assign_overtime"),
        ("assign_job", "split_job"),
        ("assign_job",),
    ], [fix.to_dict() for fix in fixes]
    assert fixes[0].outcome.orders_on_time == 3
    assert fixes[1].outcome.orders_on_time == 3
    assert fixes[1].outcome.extra_cost_paise > fixes[0].outcome.extra_cost_paise
    assert fixes[2].outcome.orders_on_time == 2
