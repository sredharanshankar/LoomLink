import pytest
from app.core.time import set_clock_override
import datetime as dt


@pytest.fixture(autouse=True)
def reset_clock():
    """Reset demo clock override after each test."""
    yield
    set_clock_override(None)