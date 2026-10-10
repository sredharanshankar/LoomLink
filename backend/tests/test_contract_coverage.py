"""Assert every CONTRACT §6 (method, path) pair is registered in the OpenAPI spec."""
import re
import pathlib
import pytest


_SKIP_PATHS = {"/ws", "/buyer-line/whatsapp/webhook"}


def _parse_contract_endpoints():
    contract = pathlib.Path(__file__).parents[2] / "docs" / "CONTRACT.md"
    text = contract.read_text(encoding="utf-8")

    m = re.search(r"## 6\. API endpoints(.+?)^## 7", text, re.DOTALL | re.MULTILINE)
    if not m:
        return []
    section = m.group(1)

    endpoints = []
    for line in section.splitlines():
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) < 2:
            continue
        method_cell, path_cell = cells[0], cells[1]
        if not re.match(r"^(GET|POST|PATCH|PUT|DELETE)(/(GET|POST|PATCH|PUT|DELETE))*$", method_cell):
            continue
        methods = method_cell.split("/")
        raw_paths = [p.strip() for p in path_cell.split(",")]
        for raw_path in raw_paths:
            path = raw_path.split("?")[0].strip()
            if not path.startswith("/"):
                continue
            if path in _SKIP_PATHS:
                continue
            for method in methods:
                endpoints.append((method.upper(), path))
    return endpoints


_ENDPOINTS = _parse_contract_endpoints()


@pytest.fixture(scope="module")
def openapi_paths(app):
    spec = app.openapi()
    return {
        (method.upper(), path)
        for path, methods in spec.get("paths", {}).items()
        for method in methods
        if method.upper() in ("GET", "POST", "PATCH", "PUT", "DELETE")
    }


@pytest.mark.parametrize("method,path", _ENDPOINTS)
def test_contract_endpoint_registered(method, path, openapi_paths):
    full_path = f"/api/v1{path}"
    assert (method, full_path) in openapi_paths, (
        f"CONTRACT §6 requires {method} {path} but it is missing from the OpenAPI spec."
    )
