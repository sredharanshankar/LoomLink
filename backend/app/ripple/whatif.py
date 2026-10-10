from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from app.ripple.diff import RippleDiff, ripple_diff
from app.ripple.fixes import Fix, find_fixes
from app.ripple.forecast import forecast
from app.ripple.model import Forecast, JsonMixin, MillState, Window
from app.ripple.pricing import AtRisk, at_risk
from app.ripple.promise import build_hypothetical_state


@dataclass(frozen=True)
class WhatIfResult(JsonMixin):
    scenario_kind: str
    before: Forecast
    after: Forecast
    diff: RippleDiff
    at_risk: AtRisk
    fixes: tuple[Fix, ...]
    is_estimate: bool = True

    @property
    def risk(self) -> AtRisk:
        return self.at_risk


def _value(scenario: object, key: str, default: Any = None) -> Any:
    if isinstance(scenario, Mapping):
        return scenario.get(key, default)
    return getattr(scenario, key, default)


def _absence_window(state: MillState, shift: str, local_date: date) -> Window:
    if shift == "C":
        starts_at, ends_at = time(22), time(6)
    else:
        index = {"A": 0, "B": 1}.get(shift)
        if index is None or index >= len(state.settings.regular_shifts):
            raise ValueError(f"unknown shift: {shift}")
        starts_at, ends_at = state.settings.regular_shifts[index]
    zone = ZoneInfo(state.settings.timezone)
    starts = datetime.combine(local_date, starts_at, zone)
    end_date = local_date + timedelta(days=1) if ends_at <= starts_at else local_date
    ends = datetime.combine(end_date, ends_at, zone)
    return Window(starts.astimezone(UTC), ends.astimezone(UTC))


def _scenario_state(state: MillState, scenario: object) -> MillState:
    kind = str(_value(scenario, "kind", _value(scenario, "type", "")))
    if kind == "breakdown":
        machine_id = _value(scenario, "machine_id")
        minutes = int(_value(scenario, "minutes", 0))
        machines = tuple(
            replace(
                machine,
                status="breakdown",
                available_from=max(machine.available_from, state.now + timedelta(minutes=minutes)),
            )
            if machine.id == machine_id or machine.code == machine_id
            else machine
            for machine in state.machines
        )
        return replace(state, machines=machines)
    if kind == "yarn_delay":
        yarn_type_id = _value(scenario, "yarn_type_id")
        days = int(_value(scenario, "days", 0))
        yarn = tuple(
            replace(
                item,
                arrivals=tuple(
                    (arrival + timedelta(days=days), quantity) for arrival, quantity in item.arrivals
                ),
            )
            if yarn_type_id is None or item.yarn_type_id == yarn_type_id
            else item
            for item in state.yarn
        )
        return replace(state, yarn=yarn)
    if kind == "rush_order":
        return build_hypothetical_state(state, _value(scenario, "draft", {}), "rush")
    if kind == "absence":
        machine_ids = set(_value(scenario, "machine_ids", ()))
        raw_date = _value(scenario, "date")
        local_date = raw_date if isinstance(raw_date, date) else date.fromisoformat(str(raw_date))
        exclusion = _absence_window(state, str(_value(scenario, "shift")), local_date)
        machines = tuple(
            replace(
                machine,
                unavailable_windows=tuple(
                    sorted((*machine.unavailable_windows, exclusion), key=lambda window: window.start)
                ),
            )
            if machine.id in machine_ids or machine.code in machine_ids
            else machine
            for machine in state.machines
        )
        return replace(state, machines=machines)
    raise ValueError(f"unknown what-if scenario: {kind}")


def what_if(state: MillState, scenario: object) -> WhatIfResult:
    kind = str(_value(scenario, "kind", _value(scenario, "type", "")))
    before = forecast(state)
    changed = _scenario_state(state, scenario)
    after = forecast(changed)
    difference = ripple_diff(before, after, state.settings)
    risk = at_risk(changed, difference, scenario)
    affected_ids = tuple(item.order_id for item in difference.affected_orders)
    if isinstance(scenario, Mapping):
        fix_trigger = {**scenario, "affected_order_ids": affected_ids}
    else:
        fix_trigger = scenario
    fixes = find_fixes(changed, after, fix_trigger, k=3) if affected_ids else ()
    return WhatIfResult(kind, before, after, difference, risk, fixes)


def whatif(state: MillState, scenario: object) -> WhatIfResult:
    return what_if(state, scenario)
