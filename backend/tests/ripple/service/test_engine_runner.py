from __future__ import annotations

import datetime as dt
import threading
import time

from sqlalchemy import func, select

from app.models.identity import MillSettings
from app.models.ripple import RippleEvent, RippleFix, RippleSnapshot
from app.ripple.model import EngineSettings, JobState, MachineState, MillState, OrderState
from app.ripple_service import engine_runner

NOW = dt.datetime(2026, 10, 12, 6, tzinfo=dt.UTC)


def _state(*, broken: bool, version: int = 1) -> MillState:
    settings = EngineSettings(
        timezone="UTC",
        regular_shifts=((dt.time(0), dt.time(0)),),
        qc_buffer_minutes=0,
        dispatch_buffer_minutes=0,
        health_amber_minutes=300,
        horizon_days=3,
    )
    machines = (
        MachineState("WV-01", "WV-01", "weaving", "cm", "idle", NOW, 600, {}, None, 45_000),
        MachineState(
            "WV-02",
            "WV-02",
            "weaving",
            "cm",
            "breakdown" if broken else "idle",
            NOW + dt.timedelta(hours=8) if broken else NOW,
            600,
            {},
            None,
            45_000,
        ),
    )
    order = OrderState(
        "ORD-104",
        "ORD-104",
        "buyer",
        "Buyer",
        NOW + dt.timedelta(hours=4),
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
    job = JobState(
        "J104",
        "J104",
        "ORD-104",
        "weaving",
        1,
        "cm",
        "fabric-a",
        600,
        "blocked" if broken else "ready",
        "WV-02",
        1,
        False,
    )
    return MillState(NOW, version, settings, machines, (job,), (order,), ())


def _settings(version: int = 1) -> MillSettings:
    return MillSettings(
        id=1,
        mill_name="Everest",
        timezone="UTC",
        state_version=version,
        created_at=NOW,
    )


def test_recompute_skips_unchanged_version_without_trigger(db_session, monkeypatch) -> None:
    """Catches redundant snapshots when no production state changed."""
    db_session.add(_settings())
    db_session.flush()
    monkeypatch.setattr(engine_runner, "load_mill_state", lambda session: _state(broken=False))
    monkeypatch.setattr(engine_runner.events, "publish", lambda *args, **kwargs: None)

    first = engine_runner.recompute(db_session)
    second = engine_runner.recompute(db_session)

    assert second.id == first.id
    assert db_session.scalar(select(func.count()).select_from(RippleSnapshot)) == 1


def test_breakdown_creates_deduped_ripple_event_with_fixes(db_session, monkeypatch) -> None:
    """Catches missing breakdown cards, missing fixes, and duplicate open cards."""
    db_session.add(_settings())
    db_session.flush()
    states = iter((_state(broken=False), _state(broken=True), _state(broken=True)))
    monkeypatch.setattr(engine_runner, "load_mill_state", lambda session: next(states))
    published: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        engine_runner.events,
        "publish",
        lambda session, event_type, payload, actor_id=None: published.append((event_type, payload)),
    )
    monkeypatch.setattr(engine_runner.interfaces, "notify", lambda *args, **kwargs: None)
    trigger = {
        "id": 42,
        "type": "machine.status_changed",
        "payload": {"machine_id": "WV-02", "to": "breakdown", "reason_code": "MOTOR_FAULT"},
    }

    engine_runner.recompute(db_session)
    engine_runner.recompute(db_session, trigger)
    engine_runner.recompute(db_session, trigger)

    events = list(db_session.scalars(select(RippleEvent)))
    assert len(events) == 1
    assert events[0].trigger_kind == "breakdown"
    assert events[0].affected_orders[0]["order_id"] == "ORD-104"
    assert events[0].at_risk_paise > 0
    assert db_session.scalar(select(func.count()).select_from(RippleFix)) > 0
    assert any(event_type == "forecast.updated" for event_type, _ in published)
    assert any(event_type == "ripple.created" for event_type, _ in published)


def test_debouncer_coalesces_ten_rapid_events_into_one_recompute() -> None:
    """Catches per-event recomputation that defeats the configured debounce window."""
    calls: list[dict] = []
    completed = threading.Event()

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def commit(self) -> None:
            return None

    def run(session, event):
        calls.append(event)
        completed.set()

    debouncer = engine_runner.EventDebouncer(
        debounce_ms=30,
        session_factory=Session,
        recompute_fn=run,
    )
    try:
        for index in range(10):
            debouncer.enqueue({"type": "job.progress", "payload": {"index": index}})
        assert completed.wait(1)
        time.sleep(0.08)
        assert len(calls) == 1
        assert calls[0]["payload"]["index"] == 9
    finally:
        debouncer.stop()


def test_repaired_machine_auto_resolves_unapplied_breakdown(db_session, monkeypatch) -> None:
    """Catches breakdown cards remaining open after the machine is repaired."""
    db_session.add(_settings())
    event = RippleEvent(
        code="RPL-261012-01",
        trigger_kind="breakdown",
        title_key="ripple.event.breakdown",
        params={"trigger_ref": "machine_id:WV-02"},
        affected_orders=[],
        at_risk_paise=0,
        status="open",
        created_at=NOW,
    )
    db_session.add(event)
    db_session.flush()
    monkeypatch.setattr(engine_runner, "load_mill_state", lambda session: _state(broken=False))
    published: list[str] = []
    monkeypatch.setattr(
        engine_runner.events,
        "publish",
        lambda session, event_type, payload, actor_id=None: published.append(event_type),
    )

    engine_runner.recompute(
        db_session,
        {
            "type": "machine.status_changed",
            "payload": {"machine_id": "WV-02", "from": "breakdown", "to": "idle"},
        },
    )

    assert event.status == "resolved"
    assert event.params["resolution_note"] == "machine repaired"
    assert "ripple.resolved" in published
