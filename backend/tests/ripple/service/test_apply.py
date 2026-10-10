from __future__ import annotations

import datetime as dt
import uuid

import pytest

from app.core.errors import AppError
from app.models.identity import MillSettings
from app.models.ripple import RippleEvent, RippleFix, RippleSnapshot
from app.ripple.model import EngineSettings, JobState, MachineState, MillState, OrderState
from app.ripple_service import apply as apply_service

NOW = dt.datetime(2026, 10, 12, 6, tzinfo=dt.UTC)


def _state(*, version: int = 1, job_status: str = "ready", target_status: str = "idle") -> MillState:
    job_id = "10000000-0000-0000-0000-000000000001"
    source_id = "20000000-0000-0000-0000-000000000001"
    target_id = "20000000-0000-0000-0000-000000000002"
    order_id = "30000000-0000-0000-0000-000000000001"
    settings = EngineSettings(
        timezone="UTC",
        regular_shifts=((dt.time(0), dt.time(0)),),
        qc_buffer_minutes=0,
        dispatch_buffer_minutes=0,
        horizon_days=3,
    )
    machines = (
        MachineState(
            source_id,
            "WV-02",
            "weaving",
            "cm",
            "breakdown",
            NOW + dt.timedelta(hours=8),
            600,
            {},
            None,
            45_000,
        ),
        MachineState(target_id, "WV-01", "weaving", "cm", target_status, NOW, 600, {}, None, 45_000),
    )
    job = JobState(
        job_id, "JOB-104-WV", order_id, "weaving", 1, "cm", "fabric-a", 600, job_status, source_id, 1, False
    )
    order = OrderState(
        order_id,
        "ORD-104",
        "buyer",
        "Buyer",
        NOW + dt.timedelta(hours=4),
        "high",
        0,
        600,
        "fabric-a",
        "cotton",
        0,
        "in_production",
        None,
        0,
        False,
    )
    return MillState(NOW, version, settings, machines, (job,), (order,), ())


def _records(db_session, *, version: int = 1) -> tuple[RippleEvent, RippleFix]:
    settings = MillSettings(id=1, mill_name="Everest", timezone="UTC", state_version=version, created_at=NOW)
    snapshot = RippleSnapshot(
        state_version=1,
        computed_at=NOW,
        forecast={},
        created_at=NOW,
    )
    event = RippleEvent(
        id=uuid.uuid4(),
        code="RPL-261012-01",
        trigger_kind="breakdown",
        title_key="ripple.event.breakdown",
        params={
            "trigger_ref": "machine_id:20000000-0000-0000-0000-000000000001",
            "machine_id": "20000000-0000-0000-0000-000000000001",
        },
        affected_orders=[{"order_id": "30000000-0000-0000-0000-000000000001"}],
        at_risk_paise=100,
        status="open",
        snapshot_id=snapshot.id,
        created_at=NOW,
    )
    fix = RippleFix(
        id=uuid.uuid4(),
        ripple_event_id=event.id,
        rank=1,
        kind="reassign",
        title_key="ripple.fix.reassign",
        actions=[
            {
                "fn": "assign_job",
                "args": {
                    "job_id": "10000000-0000-0000-0000-000000000001",
                    "machine_id": "20000000-0000-0000-0000-000000000002",
                    "queue_position": 1,
                },
            }
        ],
        orders_on_time=1,
        orders_total=1,
        total_late_minutes=0,
        extra_cost_paise=0,
        changes_count=1,
        created_at=NOW,
    )
    db_session.add_all([settings, snapshot, event, fix])
    db_session.flush()
    return event, fix


def test_apply_fix_calls_a_interface_and_resolves_event(db_session, monkeypatch) -> None:
    """Catches bypassing the A interface or leaving an applied Ripple open."""
    event, fix = _records(db_session)
    db_session.expire_all()
    moved: dict[str, object] = {}

    def assign_job(session, job_id, machine_id, queue_position, actor_id, reason):
        moved.update(job_id=job_id, machine_id=machine_id, queue_position=queue_position, reason=reason)

    monkeypatch.setattr(apply_service.interfaces, "assign_job", assign_job)
    monkeypatch.setattr(apply_service, "load_mill_state", lambda session: _state())
    monkeypatch.setattr(apply_service.interfaces, "notify", lambda *args, **kwargs: None)
    monkeypatch.setattr(apply_service.events, "publish", lambda *args, **kwargs: None)
    monkeypatch.setattr(apply_service.engine_runner, "recompute", lambda *args, **kwargs: None)
    audited: list[str] = []
    monkeypatch.setattr(
        apply_service, "audit", lambda session, actor_id, action, *args, **kwargs: audited.append(action)
    )
    actor = {"id": "40000000-0000-0000-0000-000000000001", "role": "manager"}

    result = apply_service.apply_fix(db_session, event.id, fix.id, 1, actor)

    assert moved["machine_id"] == uuid.UUID("20000000-0000-0000-0000-000000000002")
    assert moved["reason"] == "ripple:RPL-261012-01:fix1"
    assert result.status == "resolved"
    assert result.resolved_fix_id == fix.id
    assert fix.applied_by == uuid.UUID(actor["id"])
    assert audited == ["ripple.fix_applied"]


def test_stale_but_valid_fix_is_applied(db_session, monkeypatch) -> None:
    """Catches rejecting a still-safe fix solely because the global version advanced."""
    event, fix = _records(db_session, version=2)
    called: list[uuid.UUID] = []
    monkeypatch.setattr(apply_service, "load_mill_state", lambda session: _state(version=2))
    monkeypatch.setattr(
        apply_service.interfaces, "assign_job", lambda session, job_id, *args, **kwargs: called.append(job_id)
    )
    monkeypatch.setattr(apply_service.interfaces, "notify", lambda *args, **kwargs: None)
    monkeypatch.setattr(apply_service.events, "publish", lambda *args, **kwargs: None)
    monkeypatch.setattr(apply_service.engine_runner, "recompute", lambda *args, **kwargs: None)
    monkeypatch.setattr(apply_service, "audit", lambda *args, **kwargs: None)

    result = apply_service.apply_fix(db_session, event.id, fix.id, 1, {"id": None, "role": "manager"})

    assert result.status == "resolved"
    assert called == [uuid.UUID("10000000-0000-0000-0000-000000000001")]


def test_stale_invalid_fix_returns_recomputed_fixes(db_session, monkeypatch) -> None:
    """Catches applying a stale action to a completed job or unavailable machine."""
    event, fix = _records(db_session, version=2)
    stale = _state(version=2, job_status="done", target_status="breakdown")
    monkeypatch.setattr(apply_service, "load_mill_state", lambda session: stale)

    with pytest.raises(AppError) as caught:
        apply_service.apply_fix(db_session, event.id, fix.id, 1, {"id": None, "role": "manager"})

    assert caught.value.code == "STALE_SNAPSHOT"
    assert "recomputed_fixes" in caught.value.details
    assert event.status == "open"


def test_dismiss_requires_reason_and_publishes(db_session, monkeypatch) -> None:
    """Catches silent dismissals without an operator-entered reason."""
    event, _ = _records(db_session)
    db_session.expire_all()
    published: list[str] = []
    monkeypatch.setattr(
        apply_service.events,
        "publish",
        lambda session, event_type, payload, actor_id=None: published.append(event_type),
    )
    audited: list[str] = []
    monkeypatch.setattr(
        apply_service, "audit", lambda session, actor_id, action, *args, **kwargs: audited.append(action)
    )

    with pytest.raises(AppError) as caught:
        apply_service.dismiss_event(db_session, event.id, "  ", {"id": None, "role": "manager"})
    assert caught.value.code == "VALIDATION_ERROR"

    result = apply_service.dismiss_event(
        db_session, event.id, "Handled during planned maintenance", {"id": None, "role": "manager"}
    )
    assert result.status == "dismissed"
    assert result.params["dismiss_reason"] == "Handled during planned maintenance"
    assert published == ["ripple.dismissed"]
    assert audited == ["ripple.dismissed"]
