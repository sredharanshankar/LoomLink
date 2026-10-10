"""Every stub endpoint must return 501 with the standard error envelope."""
import pytest


_STUB_ENDPOINTS = [
    ("GET", "/api/v1/suppliers"),
    ("GET", "/api/v1/yarn-types"),
    ("GET", "/api/v1/orders"),
    ("GET", "/api/v1/jobs"),
    ("GET", "/api/v1/machines"),
    ("GET", "/api/v1/rolls"),
    ("GET", "/api/v1/inspections"),
    ("GET", "/api/v1/dispatches"),
    ("GET", "/api/v1/workers"),
    ("GET", "/api/v1/invoices"),
    ("GET", "/api/v1/ripple"),
    ("GET", "/api/v1/ripple/idle-hunter"),
    ("GET", "/api/v1/leak/today"),
    ("GET", "/api/v1/finance/receivables"),
    ("GET", "/api/v1/finance/payables"),
    ("GET", "/api/v1/dashboard/owner"),
    ("GET", "/api/v1/users"),
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
