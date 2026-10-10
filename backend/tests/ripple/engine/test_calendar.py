from datetime import UTC, datetime, time

import pytest

from app.ripple.calendar import InsufficientCapacityError, advance, next_open, open_windows
from app.ripple.model import EngineSettings, MachineState, Window

UTC = UTC


def dt(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 10, day, hour, minute, tzinfo=UTC)


def machine(*, overtime_windows: tuple[Window, ...] = ()) -> MachineState:
    return MachineState(
        id="m1",
        code="WV-01",
        stage="weaving",
        unit="cm",
        status="idle",
        available_from=dt(12, 0),
        default_speed_per_hour=1_000,
        speeds={},
        capabilities=None,
        idle_cost_paise_per_hour=45_000,
        overtime_windows=overtime_windows,
    )


def test_open_windows_converts_ist_shifts_and_merges_touching_overtime() -> None:
    settings = EngineSettings(
        regular_shifts=((time(6), time(14)), (time(14), time(22))),
    )
    overtime = Window(dt(12, 16, 30), dt(12, 18, 30))  # 22:00-00:00 IST

    windows = open_windows(machine(overtime_windows=(overtime,)), settings, dt(12, 0), dt(13, 0))

    assert windows == (Window(dt(12, 0, 30), dt(12, 18, 30)),)


def test_open_windows_supports_regular_shift_crossing_midnight() -> None:
    settings = EngineSettings(regular_shifts=((time(22), time(6)),))

    windows = open_windows(machine(), settings, dt(12, 18), dt(13, 4))

    assert windows == (Window(dt(12, 18), dt(13, 0, 30)),)


@pytest.mark.parametrize(
    ("instant", "expected"),
    [
        (dt(12, 1), dt(12, 1)),
        (dt(12, 2), dt(12, 3)),
        (dt(12, 5), None),
    ],
)
def test_next_open_handles_inside_gap_and_exhausted_windows(
    instant: datetime, expected: datetime | None
) -> None:
    windows = (Window(dt(12, 0), dt(12, 2)), Window(dt(12, 3), dt(12, 5)))
    assert next_open(instant, windows) == expected


def test_advance_zero_minutes_returns_next_working_instant() -> None:
    windows = (Window(dt(12, 3), dt(12, 5)),)
    assert advance(dt(12, 1), 0, windows) == dt(12, 3)


def test_advance_consumes_only_open_minutes_across_gap() -> None:
    windows = (Window(dt(12, 0), dt(12, 2)), Window(dt(12, 3), dt(12, 5)))
    assert advance(dt(12, 1, 30), 90, windows) == dt(12, 4)


def test_advance_raises_when_horizon_has_too_little_capacity() -> None:
    with pytest.raises(InsufficientCapacityError):
        advance(dt(12, 0), 121, (Window(dt(12, 0), dt(12, 2)),))


def test_window_rejects_naive_or_reversed_datetimes() -> None:
    with pytest.raises(ValueError):
        Window(datetime(2026, 10, 12), dt(12, 1))
    with pytest.raises(ValueError):
        Window(dt(12, 2), dt(12, 1))
