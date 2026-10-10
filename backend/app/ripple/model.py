from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import date, datetime, time
from enum import Enum
from types import MappingProxyType
from typing import Any


def _require_aware(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, frozenset)):
        return [_json_value(item) for item in value]
    return value


class JsonMixin:
    def to_dict(self) -> dict[str, Any]:
        return _json_value(self)


@dataclass(frozen=True)
class Window(JsonMixin):
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        _require_aware(self.start, "start")
        _require_aware(self.end, "end")
        if self.end <= self.start:
            raise ValueError("window end must be after start")


@dataclass(frozen=True)
class MachineState(JsonMixin):
    id: str
    code: str
    stage: str
    unit: str
    status: str
    available_from: datetime
    default_speed_per_hour: int
    speeds: Mapping[str, tuple[int, int]]
    capabilities: frozenset[str] | None
    idle_cost_paise_per_hour: int
    overtime_windows: tuple[Window, ...] = ()
    unavailable_windows: tuple[Window, ...] = ()

    def __post_init__(self) -> None:
        _require_aware(self.available_from, "available_from")
        object.__setattr__(self, "speeds", MappingProxyType(dict(self.speeds)))

    def __hash__(self) -> int:
        return hash(
            (
                self.id,
                self.code,
                self.stage,
                self.unit,
                self.status,
                self.available_from,
                self.default_speed_per_hour,
                tuple(sorted(self.speeds.items())),
                self.capabilities,
                self.idle_cost_paise_per_hour,
                self.overtime_windows,
                self.unavailable_windows,
            )
        )


@dataclass(frozen=True)
class JobState(JsonMixin):
    id: str
    code: str
    order_id: str
    stage: str
    seq: int
    unit: str
    fabric_type_id: str
    remaining_qty: int
    status: str
    machine_id: str | None
    queue_position: int | None
    is_running: bool


@dataclass(frozen=True)
class OrderState(JsonMixin):
    id: str
    code: str
    buyer_id: str
    buyer_name: str
    due_at: datetime
    priority: str
    penalty_paise_per_day: int
    quantity_cm: int
    fabric_type_id: str
    yarn_type_id: str
    yarn_needed_remaining_g: int
    status: str
    promised_date: date | None
    rolls_pending_qc: int
    production_done: bool

    def __post_init__(self) -> None:
        _require_aware(self.due_at, "due_at")


@dataclass(frozen=True)
class YarnState(JsonMixin):
    yarn_type_id: str
    available_g: int
    arrivals: tuple[tuple[datetime, int], ...]

    def __post_init__(self) -> None:
        for arrival_at, _ in self.arrivals:
            _require_aware(arrival_at, "arrival_at")


@dataclass(frozen=True)
class EngineSettings(JsonMixin):
    timezone: str = "Asia/Kolkata"
    regular_shifts: tuple[tuple[time, time], ...] = (
        (time(6), time(14)),
        (time(14), time(22)),
    )
    qc_buffer_minutes: int = 240
    dispatch_buffer_minutes: int = 120
    health_amber_minutes: int = 1440
    slip_threshold_minutes: int = 60
    changeover_minutes: int = 45
    changeover_cost_paise: int = 90_000
    penalty_grace_minutes: int = 240
    overtime_hourly_paise: int = 10_000
    overtime_multiplier_bp: int = 15_000
    overtime_shift_minutes: int = 480
    horizon_days: int = 30
    default_cv_bp: int = 1000


@dataclass(frozen=True)
class MillState(JsonMixin):
    now: datetime
    version: int
    settings: EngineSettings
    machines: tuple[MachineState, ...]
    jobs: tuple[JobState, ...]
    orders: tuple[OrderState, ...]
    yarn: tuple[YarnState, ...]

    def __post_init__(self) -> None:
        _require_aware(self.now, "now")


@dataclass(frozen=True)
class TimelineEntry(JsonMixin):
    job_id: str
    start_at: datetime
    end_at: datetime


@dataclass(frozen=True)
class JobForecast(JsonMixin):
    job_id: str
    machine_id: str | None
    start_at: datetime | None
    end_at: datetime | None
    waiting_on: str | None
    virtual_assignment: bool


@dataclass(frozen=True)
class Bottleneck(JsonMixin):
    kind: str
    ref: str


@dataclass(frozen=True)
class OrderForecast(JsonMixin):
    order_id: str
    code: str
    predicted_dispatch_at: datetime | None
    due_at: datetime
    slack_minutes: int | None
    health: str
    confidence_minutes: int
    bottleneck: Bottleneck | None


@dataclass(frozen=True)
class MachineForecast(JsonMixin):
    machine_id: str
    timeline: tuple[TimelineEntry, ...]
    idle_windows: tuple[Window, ...]


@dataclass(frozen=True)
class Forecast(JsonMixin):
    computed_at: datetime
    state_version: int
    orders: tuple[OrderForecast, ...]
    jobs: tuple[JobForecast, ...]
    machines: tuple[MachineForecast, ...]
    is_estimate: bool = True
