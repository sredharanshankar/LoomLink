import datetime as dt
import pytest
from app.core import time as T


def test_now_returns_utc():
    n = T.now()
    assert n.tzinfo is not None
    assert n.utcoffset() == dt.timedelta(0)


def test_override():
    fixed = dt.datetime(2026, 4, 1, 6, 0, tzinfo=dt.timezone.utc)
    T.set_clock_override(fixed)
    assert T.now() == fixed
    T.set_clock_override(None)
    assert T.now() != fixed


def test_to_local():
    utc_dt = dt.datetime(2026, 4, 1, 0, 0, tzinfo=dt.timezone.utc)
    local = T.to_local(utc_dt)
    assert local.utcoffset() == dt.timedelta(hours=5, minutes=30)


def test_fy_label():
    assert T.fy_label(dt.date(2026, 4, 1)) == "2627"
    assert T.fy_label(dt.date(2026, 3, 31)) == "2526"
    assert T.fy_label(dt.date(2025, 4, 1)) == "2526"


def test_today_local():
    d = T.today_local()
    assert isinstance(d, dt.date)