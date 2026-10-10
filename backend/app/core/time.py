from __future__ import annotations
import datetime as _dt
import threading
from zoneinfo import ZoneInfo

_process_start: _dt.datetime = _dt.datetime.now(_dt.timezone.utc)
_clock_override: _dt.datetime | None = None
_lock = threading.Lock()


def set_clock_override(dt: _dt.datetime | None) -> None:
    """For tests only. Pass None to restore real clock."""
    global _clock_override
    with _lock:
        _clock_override = dt


def now() -> _dt.datetime:
    """Return the current aware UTC datetime. Honours DEMO_CLOCK_START."""
    from app.config import get_settings

    with _lock:
        override = _clock_override

    if override is not None:
        elapsed = _dt.datetime.now(_dt.timezone.utc) - _process_start
        return override + elapsed

    settings = get_settings()
    if settings.demo_clock_start:
        try:
            demo_start = _dt.datetime.fromisoformat(settings.demo_clock_start)
            if demo_start.tzinfo is None:
                demo_start = demo_start.replace(tzinfo=_dt.timezone.utc)
            elapsed = _dt.datetime.now(_dt.timezone.utc) - _process_start
            return demo_start.astimezone(_dt.timezone.utc) + elapsed
        except ValueError:
            pass

    return _dt.datetime.now(_dt.timezone.utc)


def _tz() -> ZoneInfo:
    from app.config import get_settings
    return ZoneInfo(get_settings().mill_timezone)


def today_local() -> _dt.date:
    return now().astimezone(_tz()).date()


def to_local(dt: _dt.datetime) -> _dt.datetime:
    return dt.astimezone(_tz())


def local_datetime(date: _dt.date, time: _dt.time) -> _dt.datetime:
    """Return UTC datetime for a local date+time combination."""
    tz = _tz()
    local = _dt.datetime(date.year, date.month, date.day, time.hour, time.minute, time.second, tzinfo=tz)
    return local.astimezone(_dt.timezone.utc)


def fy_label(date: _dt.date) -> str:
    """Return 4-char FY label, e.g. '2627' for FY 2026-27."""
    year = date.year
    if date.month < 4:
        fy_start = year - 1
    else:
        fy_start = year
    fy_end = fy_start + 1
    return f"{fy_start % 100:02d}{fy_end % 100:02d}"
