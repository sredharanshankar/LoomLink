from __future__ import annotations

import datetime as dt
import uuid

from fastapi.testclient import TestClient

from app.core.rbac import current_user
from app.deps import get_db
from app.models.ripple import RippleEvent, RippleFix, RippleSnapshot
from app.ripple_service import queries

NOW = dt.datetime(2026, 10, 12, 6, tzinfo=dt.UTC)
ORDER_ID = uuid.UUID("30000000-0000-0000-0000-000000000001")


def _snapshot(db_session) -> RippleSnapshot:
    row = RippleSnapshot(
        id=uuid.uuid4(),
        state_version=9,
        computed_at=NOW,
        forecast={
            "computed_at": NOW.isoformat(),
            "state_version": 9,
            "is_estimate": True,
            "orders": [
                {
                    "order_id": str(ORDER_ID),
                    "code": "ORD-104",
                    "predicted_dispatch_at": (NOW + dt.timedelta(hours=2)).isoformat(),
                    "due_at": (NOW + dt.timedelta(hours=5)).isoformat(),
                    "slack_minutes": 180,
                    "health": "amber",
                    "confidence_minutes": 30,
                    "bottleneck": None,
                }
            ],
            "jobs": [],
            "machines": [],
        },
        created_at=NOW,
    )
    db_session.add(row)
    db_session.flush()
    return row


def test_health_queries_read_latest_snapshot(db_session) -> None:
    """Catches health interfaces drifting from the latest persisted forecast."""
    _snapshot(db_session)

    health = queries.get_order_health(db_session, ORDER_ID)
    many = queries.get_orders_health(db_session, [ORDER_ID, uuid.uuid4()])

    assert health == {
        "health": "amber",
        "slack_minutes": 180,
        "predicted_dispatch_at": (NOW + dt.timedelta(hours=2)).isoformat(),
        "confidence_minutes": 30,
        "is_estimate": True,
    }
    assert many == {ORDER_ID: health}


def test_ripple_endpoints_return_persisted_forecast_events_and_enforce_apply_permission(
    app, db_session
) -> None:
    """Catches unimplemented read routes and an apply route exposed to operators."""
    snapshot = _snapshot(db_session)
    event = RippleEvent(
        id=uuid.uuid4(),
        code="RPL-261012-01",
        trigger_kind="breakdown",
        title_key="ripple.event.breakdown",
        params={},
        affected_orders=[],
        at_risk_paise=0,
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
        actions=[],
        orders_on_time=1,
        orders_total=1,
        total_late_minutes=0,
        extra_cost_paise=0,
        changes_count=0,
        created_at=NOW,
    )
    db_session.add_all([event, fix])
    db_session.flush()
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app, raise_server_exceptions=False)

    forecast_response = client.get("/api/v1/ripple/forecast")
    health_response = client.get(f"/api/v1/ripple/orders/{ORDER_ID}/health")
    events_response = client.get("/api/v1/ripple/events?status=open")
    detail_response = client.get(f"/api/v1/ripple/events/{event.id}")

    assert forecast_response.status_code == 200
    assert forecast_response.json()["state_version"] == 9
    assert health_response.status_code == 200
    assert health_response.json()["health"] == "amber"
    assert events_response.status_code == 200
    assert events_response.json()["total"] == 1
    assert detail_response.status_code == 200
    assert detail_response.json()["fixes"][0]["rank"] == 1

    app.dependency_overrides[current_user] = lambda: {
        "id": "50000000-0000-0000-0000-000000000001",
        "role": "operator",
    }
    forbidden = client.post(
        f"/api/v1/ripple/events/{event.id}/fixes/{fix.id}/apply",
        json={"expected_state_version": 9},
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"
