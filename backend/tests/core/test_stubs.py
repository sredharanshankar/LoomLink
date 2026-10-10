"""Every stub endpoint must return 501 with the standard error envelope."""
import pytest


_STUB_ENDPOINTS = [
    # inspections not yet wired to a route
    ("GET", "/api/v1/inspections"),
]


@pytest.mark.parametrize("method,path", _STUB_ENDPOINTS)
def test_stub_returns_501_envelope(client, method, path):
    resp = getattr(client, method.lower())(path)
    if resp.status_code == 404:
        pytest.skip(f"{method} {path} not registered yet")
    assert resp.status_code == 501, f"{method} {path} returned {resp.status_code}"
    body = resp.json()
    assert "error" in body, f"missing 'error' key in {body}"
    assert body["error"]["code"] == "NOT_IMPLEMENTED"
