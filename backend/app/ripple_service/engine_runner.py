from __future__ import annotations

import datetime as dt
import logging
import threading
import time
from collections.abc import Callable, Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core import events
from app.core.ids import next_code
from app.core.time import now
from app.models.identity import MillSettings
from app.models.ripple import RippleEvent, RippleFix, RippleSnapshot
from app.ripple.diff import ripple_diff
from app.ripple.fixes import find_fixes
from app.ripple.forecast import forecast
from app.ripple.model import (
    Bottleneck,
    Forecast,
    JobForecast,
    MachineForecast,
    OrderForecast,
    TimelineEntry,
    Window,
)
from app.ripple.pricing import at_risk
from app.services import interfaces

from .state_loader import load_mill_state

logger = logging.getLogger(__name__)


def _parse_datetime(value: str | None) -> dt.datetime | None:
    return dt.datetime.fromisoformat(value) if value else None


def _forecast_from_dict(data: Mapping[str, Any]) -> Forecast:
    return Forecast(
        computed_at=dt.datetime.fromisoformat(str(data["computed_at"])),
        state_version=int(data["state_version"]),
        orders=tuple(
            OrderForecast(
                order_id=str(item["order_id"]),
                code=str(item["code"]),
                predicted_dispatch_at=_parse_datetime(item.get("predicted_dispatch_at")),
                due_at=dt.datetime.fromisoformat(str(item["due_at"])),
                slack_minutes=item.get("slack_minutes"),
                health=str(item["health"]),
                confidence_minutes=int(item["confidence_minutes"]),
                bottleneck=(
                    Bottleneck(str(item["bottleneck"]["kind"]), str(item["bottleneck"]["ref"]))
                    if item.get("bottleneck")
                    else None
                ),
            )
            for item in data.get("orders", ())
        ),
        jobs=tuple(
            JobForecast(
                job_id=str(item["job_id"]),
                machine_id=item.get("machine_id"),
                start_at=_parse_datetime(item.get("start_at")),
                end_at=_parse_datetime(item.get("end_at")),
                waiting_on=item.get("waiting_on"),
                virtual_assignment=bool(item.get("virtual_assignment", False)),
            )
            for item in data.get("jobs", ())
        ),
        machines=tuple(
            MachineForecast(
                machine_id=str(item["machine_id"]),
                timeline=tuple(
                    TimelineEntry(
                        str(entry["job_id"]),
                        dt.datetime.fromisoformat(str(entry["start_at"])),
                        dt.datetime.fromisoformat(str(entry["end_at"])),
                    )
                    for entry in item.get("timeline", ())
                ),
                idle_windows=tuple(
                    Window(
                        dt.datetime.fromisoformat(str(window["start"])),
                        dt.datetime.fromisoformat(str(window["end"])),
                    )
                    for window in item.get("idle_windows", ())
                ),
            )
            for item in data.get("machines", ())
        ),
        is_estimate=bool(data.get("is_estimate", True)),
    )


def latest_snapshot(session: Session) -> RippleSnapshot | None:
    return session.scalar(
        select(RippleSnapshot).order_by(RippleSnapshot.computed_at.desc(), RippleSnapshot.id.desc()).limit(1)
    )


def _changed_order_ids(previous: Forecast | None, current: Forecast) -> list[str]:
    if previous is None:
        return [item.order_id for item in current.orders]
    before = {item.order_id: item for item in previous.orders}
    return [
        item.order_id
        for item in current.orders
        if item.order_id not in before
        or before[item.order_id].health != item.health
        or before[item.order_id].predicted_dispatch_at != item.predicted_dispatch_at
    ]


def _trigger_payload(trigger_event: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = trigger_event.get("payload", {})
    return payload if isinstance(payload, Mapping) else {}


def _trigger_ref(trigger_event: Mapping[str, Any]) -> str:
    payload = _trigger_payload(trigger_event)
    for key in ("machine_id", "yarn_type_id", "order_id", "roll_id", "worker_id", "job_id"):
        if payload.get(key) is not None:
            return f"{key}:{payload[key]}"
    return f"event:{trigger_event.get('id', 'unknown')}"


def _trigger_kind(trigger_event: Mapping[str, Any]) -> str:
    event_type = str(trigger_event.get("type", ""))
    payload = _trigger_payload(trigger_event)
    if event_type == "machine.status_changed":
        return "breakdown"
    if event_type.startswith("stock."):
        return "stock_short"
    if event_type.startswith("roll.") and payload.get("decision") == "rework":
        return "qc_rework"
    if event_type == "attendance.changed":
        return "absence"
    if event_type == "order.created" and payload.get("priority") == "rush":
        return "rush_order"
    return "slip"


def _resolve_repaired(session: Session, trigger_event: Mapping[str, Any]) -> None:
    payload = _trigger_payload(trigger_event)
    if trigger_event.get("type") != "machine.status_changed" or payload.get("to") == "breakdown":
        return
    ref = _trigger_ref(trigger_event)
    rows = session.scalars(
        select(RippleEvent).where(RippleEvent.status == "open", RippleEvent.trigger_kind == "breakdown")
    )
    for row in rows:
        if (row.params or {}).get("trigger_ref") != ref or row.resolved_fix_id is not None:
            continue
        row.status = "resolved"
        row.resolved_at = now()
        row.updated_at = row.resolved_at
        row.params = {**(row.params or {}), "resolution_note": "machine repaired"}
        events.publish(session, "ripple.resolved", {"ripple_event_id": str(row.id), "code": row.code})


def _persist_ripple(
    session: Session,
    snapshot: RippleSnapshot,
    state,
    current: Forecast,
    previous: Forecast | None,
    trigger_event: Mapping[str, Any],
) -> RippleEvent | None:
    _resolve_repaired(session, trigger_event)
    payload = _trigger_payload(trigger_event)
    if trigger_event.get("type") == "machine.status_changed" and payload.get("to") != "breakdown":
        return None
    if previous is None:
        return None
    difference = ripple_diff(previous, current, state.settings)
    kind = _trigger_kind(trigger_event)
    affected = difference.affected_orders
    if kind != "breakdown" and not affected:
        return None
    ref = _trigger_ref(trigger_event)
    existing = next(
        (
            row
            for row in session.scalars(select(RippleEvent).where(RippleEvent.status == "open"))
            if (row.params or {}).get("trigger_ref") == ref
        ),
        None,
    )
    if existing is not None and not affected:
        existing.snapshot_id = snapshot.id
        existing.updated_at = now()
        return existing
    trigger = {
        "kind": kind,
        "machine_id": payload.get("machine_id"),
        "ref": payload.get("machine_id") or payload.get("yarn_type_id") or payload.get("order_id"),
        "affected_order_ids": tuple(item.order_id for item in affected),
    }
    risk = at_risk(state, difference, trigger)
    fixes = find_fixes(state, current, trigger, k=3) if affected else ()
    stamp = now()
    row = existing or RippleEvent(
        code=next_code(session, "ripple_event", at=stamp),
        trigger_kind=kind,
        status="open",
        created_at=stamp,
    )
    row.trigger_event_id = int(trigger_event["id"]) if trigger_event.get("id") is not None else None
    row.title_key = f"ripple.event.{kind}"
    row.params = {"trigger_ref": ref, **dict(payload)}
    row.affected_orders = [item.to_dict() for item in affected]
    row.at_risk_paise = risk.total_paise
    row.at_risk_breakdown = risk.to_dict()
    row.snapshot_id = snapshot.id
    row.updated_at = stamp
    if existing is None:
        session.add(row)
    session.flush()
    for old_fix in session.scalars(select(RippleFix).where(RippleFix.ripple_event_id == row.id)):
        session.delete(old_fix)
    session.flush()
    for rank, fix in enumerate(fixes, start=1):
        session.add(
            RippleFix(
                ripple_event_id=row.id,
                rank=rank,
                kind=fix.kind,
                title_key=fix.title_key,
                params=dict(fix.params),
                actions=[dict(action) for action in fix.actions],
                orders_on_time=fix.outcome.orders_on_time,
                orders_total=fix.outcome.orders_total,
                total_late_minutes=fix.outcome.total_late_minutes,
                extra_cost_paise=fix.outcome.extra_cost_paise,
                changes_count=fix.outcome.changes_count,
                explanation_key=fix.explanation_key,
                explanation_params={"collateral": list(fix.outcome.collateral)},
                created_at=stamp,
            )
        )
    events.publish(session, "ripple.created", {"ripple_event_id": str(row.id), "code": row.code})
    if existing is None:
        interfaces.notify(
            session,
            role="manager",
            type="ripple",
            title_key=row.title_key,
            params=row.params,
            link=f"/app/ripple/{row.id}",
        )
    return row


def recompute(session: Session, trigger_event: Mapping[str, Any] | None = None) -> RippleSnapshot:
    state = load_mill_state(session)
    previous_row = latest_snapshot(session)
    if trigger_event is None and previous_row is not None and previous_row.state_version == state.version:
        return previous_row
    previous = _forecast_from_dict(previous_row.forecast) if previous_row and previous_row.forecast else None
    result = forecast(state)
    stamp = now()
    snapshot = RippleSnapshot(
        state_version=state.version,
        computed_at=result.computed_at,
        forecast=result.to_dict(),
        trigger_event_id=(
            int(trigger_event["id"])
            if trigger_event is not None and trigger_event.get("id") is not None
            else None
        ),
        created_at=stamp,
    )
    session.add(snapshot)
    session.flush()
    events.publish(
        session,
        "forecast.updated",
        {
            "snapshot_id": str(snapshot.id),
            "state_version": snapshot.state_version,
            "changed_order_ids": _changed_order_ids(previous, result),
        },
    )
    if trigger_event is not None:
        _persist_ripple(session, snapshot, state, result, previous, trigger_event)
    session.flush()
    # Core currently versions all published events, including derived Ripple events.
    # Keep the persisted snapshot aligned with the transaction's final state version.
    settings_row = session.scalar(select(MillSettings).limit(1))
    if settings_row is not None and settings_row.state_version != snapshot.state_version:
        snapshot.state_version = settings_row.state_version
        snapshot.forecast = {**(snapshot.forecast or {}), "state_version": settings_row.state_version}
    return snapshot


def _prefer_trigger(events_to_merge: list[dict]) -> dict:
    breakdowns = [
        item
        for item in events_to_merge
        if item.get("type") == "machine.status_changed"
        and isinstance(item.get("payload"), Mapping)
        and item["payload"].get("to") == "breakdown"
    ]
    return (breakdowns or events_to_merge)[-1]


class EventDebouncer:
    def __init__(
        self,
        *,
        debounce_ms: int,
        session_factory: Callable,
        recompute_fn: Callable[[Session, dict], Any] = recompute,
    ) -> None:
        self._delay = debounce_ms / 1000
        self._session_factory = session_factory
        self._recompute = recompute_fn
        self._condition = threading.Condition()
        self._pending: list[dict] = []
        self._deadline = 0.0
        self._stopped = False
        self._thread = threading.Thread(target=self._run, daemon=True, name="ripple-debounce")
        self._thread.start()

    def enqueue(self, event: dict) -> None:
        with self._condition:
            self._pending.append(event)
            self._deadline = time.monotonic() + self._delay
            self._condition.notify()

    def stop(self) -> None:
        with self._condition:
            self._stopped = True
            self._condition.notify()
        self._thread.join(timeout=1)

    def _run(self) -> None:
        while True:
            with self._condition:
                while not self._pending and not self._stopped:
                    self._condition.wait()
                if self._stopped:
                    return
                remaining = self._deadline - time.monotonic()
                if remaining > 0:
                    self._condition.wait(timeout=remaining)
                    continue
                pending, self._pending = self._pending, []
            try:
                with self._session_factory() as session:
                    self._recompute(session, _prefer_trigger(pending))
                    session.commit()
            except Exception:
                logger.exception("Ripple recompute failed for %d coalesced events", len(pending))


_debouncer: EventDebouncer | None = None
_registered = False


def register() -> None:
    global _debouncer, _registered
    if _registered:
        return
    from app.db import SessionLocal

    _debouncer = EventDebouncer(
        debounce_ms=get_settings().ripple_debounce_ms,
        session_factory=SessionLocal,
    )

    def handler(session: Session, event: dict) -> None:  # noqa: ARG001
        assert _debouncer is not None
        _debouncer.enqueue(event)

    for prefix in (
        "machine.status_changed",
        "job.",
        "stock.",
        "order.",
        "roll.",
        "dispatch.",
        "attendance.changed",
        "shift.overtime_assigned",
    ):
        events.subscribe(prefix, handler)
    _registered = True
