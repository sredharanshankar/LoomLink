from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.ripple.model import EngineSettings, Forecast, JsonMixin

HEALTH_RANK = {"green": 0, "amber": 1, "red": 2}


@dataclass(frozen=True)
class OrderDelta(JsonMixin):
    order_id: str
    code: str
    before_dispatch_at: datetime | None
    after_dispatch_at: datetime | None
    before_slack_minutes: int | None
    after_slack_minutes: int | None
    before_health: str
    after_health: str
    delta_minutes: int | None
    newly_late: bool
    worsened: bool


@dataclass(frozen=True)
class MachineIdleChange(JsonMixin):
    machine_id: str
    before_minutes: int
    after_minutes: int
    delta_minutes: int


@dataclass(frozen=True)
class RippleDiff(JsonMixin):
    orders: tuple[OrderDelta, ...]
    affected_orders: tuple[OrderDelta, ...]
    machine_idle_changes: tuple[MachineIdleChange, ...]


def _idle_minutes(windows: object) -> int:
    return sum(int((item.end - item.start).total_seconds() // 60) for item in windows)  # type: ignore[attr-defined]


def ripple_diff(before: Forecast, after: Forecast, settings: EngineSettings) -> RippleDiff:
    before_orders = {item.order_id: item for item in before.orders}
    after_orders = {item.order_id: item for item in after.orders}
    deltas: list[OrderDelta] = []
    for order_id in sorted(before_orders.keys() | after_orders.keys()):
        old = before_orders.get(order_id)
        new = after_orders.get(order_id)
        if old is None or new is None:
            continue
        if old.predicted_dispatch_at is not None and new.predicted_dispatch_at is not None:
            delta_minutes = int((new.predicted_dispatch_at - old.predicted_dispatch_at).total_seconds() // 60)
        elif old.predicted_dispatch_at is None and new.predicted_dispatch_at is None:
            delta_minutes = 0
        else:
            delta_minutes = None
        newly_late = (
            old.slack_minutes is not None
            and old.slack_minutes >= 0
            and (new.slack_minutes is None or new.slack_minutes < 0)
        )
        health_worse = HEALTH_RANK.get(new.health, 2) > HEALTH_RANK.get(old.health, 2)
        became_unschedulable = old.predicted_dispatch_at is not None and new.predicted_dispatch_at is None
        threshold_slip = became_unschedulable or (
            delta_minutes is not None and delta_minutes >= settings.slip_threshold_minutes
        )
        worsened = health_worse or threshold_slip
        deltas.append(
            OrderDelta(
                order_id=order_id,
                code=new.code,
                before_dispatch_at=old.predicted_dispatch_at,
                after_dispatch_at=new.predicted_dispatch_at,
                before_slack_minutes=old.slack_minutes,
                after_slack_minutes=new.slack_minutes,
                before_health=old.health,
                after_health=new.health,
                delta_minutes=delta_minutes,
                newly_late=newly_late,
                worsened=worsened,
            )
        )
    affected = tuple(
        sorted(
            (item for item in deltas if item.newly_late or item.worsened),
            key=lambda item: (
                item.after_slack_minutes if item.after_slack_minutes is not None else -(10**18),
                item.code,
            ),
        )
    )
    before_machines = {item.machine_id: item for item in before.machines}
    after_machines = {item.machine_id: item for item in after.machines}
    changes: list[MachineIdleChange] = []
    for machine_id in sorted(before_machines.keys() | after_machines.keys()):
        old_minutes = (
            _idle_minutes(before_machines[machine_id].idle_windows) if machine_id in before_machines else 0
        )
        new_minutes = (
            _idle_minutes(after_machines[machine_id].idle_windows) if machine_id in after_machines else 0
        )
        if old_minutes != new_minutes:
            changes.append(MachineIdleChange(machine_id, old_minutes, new_minutes, new_minutes - old_minutes))
    return RippleDiff(tuple(deltas), affected, tuple(changes))
