from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.ripple.model import EngineSettings, MachineState, Window


class InsufficientCapacityError(ValueError):
    """Raised when the supplied windows cannot contain all requested work."""


def _merge(windows: list[Window]) -> tuple[Window, ...]:
    if not windows:
        return ()
    ordered = sorted(windows, key=lambda window: (window.start, window.end))
    merged: list[Window] = [ordered[0]]
    for window in ordered[1:]:
        previous = merged[-1]
        if window.start <= previous.end:
            merged[-1] = Window(previous.start, max(previous.end, window.end))
        else:
            merged.append(window)
    return tuple(merged)


def _subtract(windows: tuple[Window, ...], exclusions: tuple[Window, ...]) -> tuple[Window, ...]:
    pieces = list(windows)
    for exclusion in _merge(list(exclusions)):
        revised: list[Window] = []
        for window in pieces:
            if exclusion.end <= window.start or exclusion.start >= window.end:
                revised.append(window)
                continue
            if window.start < exclusion.start:
                revised.append(Window(window.start, exclusion.start))
            if exclusion.end < window.end:
                revised.append(Window(exclusion.end, window.end))
        pieces = revised
    return tuple(pieces)


def regular_windows(settings: EngineSettings, start: datetime, horizon_end: datetime) -> tuple[Window, ...]:
    if start.tzinfo is None or horizon_end.tzinfo is None:
        raise ValueError("window bounds must be timezone-aware")
    if horizon_end <= start:
        return ()
    local_zone = ZoneInfo(settings.timezone)
    local_start = start.astimezone(local_zone)
    local_end = horizon_end.astimezone(local_zone)
    current_day: date = local_start.date() - timedelta(days=1)
    final_day = local_end.date()
    generated: list[Window] = []
    while current_day <= final_day:
        for shift_start, shift_end in settings.regular_shifts:
            begins = datetime.combine(current_day, shift_start, local_zone)
            end_day = current_day + timedelta(days=1) if shift_end <= shift_start else current_day
            ends = datetime.combine(end_day, shift_end, local_zone)
            utc_start = begins.astimezone(UTC)
            utc_end = ends.astimezone(UTC)
            clipped_start = max(start, utc_start)
            clipped_end = min(horizon_end, utc_end)
            if clipped_end > clipped_start:
                generated.append(Window(clipped_start, clipped_end))
        current_day += timedelta(days=1)
    return _merge(generated)


def open_windows(
    machine: MachineState,
    settings: EngineSettings,
    start: datetime,
    horizon_end: datetime,
) -> tuple[Window, ...]:
    windows = list(regular_windows(settings, start, horizon_end))
    for overtime in machine.overtime_windows:
        clipped_start = max(start, overtime.start)
        clipped_end = min(horizon_end, overtime.end)
        if clipped_end > clipped_start:
            windows.append(Window(clipped_start, clipped_end))
    merged = _merge(windows)
    exclusions = tuple(
        Window(max(start, item.start), min(horizon_end, item.end))
        for item in machine.unavailable_windows
        if min(horizon_end, item.end) > max(start, item.start)
    )
    return _subtract(merged, exclusions)


def next_open(t: datetime, windows: tuple[Window, ...]) -> datetime | None:
    for window in windows:
        if window.start <= t < window.end:
            return t
        if t < window.start:
            return window.start
    return None


def advance(start: datetime, minutes: int, windows: tuple[Window, ...]) -> datetime:
    if minutes < 0:
        raise ValueError("minutes cannot be negative")
    cursor = next_open(start, windows)
    if cursor is None:
        raise InsufficientCapacityError("no open capacity remains")
    remaining = minutes
    if remaining == 0:
        return cursor
    for window in windows:
        if window.end <= cursor:
            continue
        active_start = max(cursor, window.start)
        available = int((window.end - active_start).total_seconds() // 60)
        if remaining <= available:
            return active_start + timedelta(minutes=remaining)
        remaining -= available
        cursor = window.end
    raise InsufficientCapacityError("work exceeds the supplied planning horizon")
