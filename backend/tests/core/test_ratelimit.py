import pytest
from app.core.ratelimit import check_rate_limit, _windows
from app.core.errors import AppError


def test_allows_up_to_limit():
    key = "__test_ratelimit_allow__"
    _windows.pop(key, None)
    for _ in range(5):
        check_rate_limit(key, max_calls=5, window_seconds=60)


def test_blocks_over_limit():
    key = "__test_ratelimit_block__"
    _windows.pop(key, None)
    for _ in range(5):
        check_rate_limit(key, max_calls=5, window_seconds=60)
    with pytest.raises(AppError) as exc_info:
        check_rate_limit(key, max_calls=5, window_seconds=60)
    assert exc_info.value.code == "RATE_LIMITED"