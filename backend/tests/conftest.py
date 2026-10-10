import pytest
from app.core.time import set_clock_override


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