import os
import pytest

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://loomlink:loomlink@localhost:5432/loomlink_test")

from app.config import get_settings  # noqa: E402
get_settings.cache_clear()

from app.core.time import set_clock_override  # noqa: E402


@pytest.fixture(autouse=True)
def reset_clock():
    yield
    set_clock_override(None)


@pytest.fixture
def app():
    from app.main import create_app
    from app.core.rbac import current_user
    _app = create_app()
    _app.dependency_overrides[current_user] = lambda: {"id": "00000000-0000-0000-0000-000000000001", "role": "owner"}
    return _app


@pytest.fixture
def client(app):
    from fastapi.testclient import TestClient
    return TestClient(app, raise_server_exceptions=False)