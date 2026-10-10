import datetime as dt
import pytest
from unittest.mock import MagicMock
from app.core.ids import next_code, _format_code, _sequence_key


def _make_session(start_value: int = 0):
    session = MagicMock()
    session.execute.return_value.fetchone.return_value = (start_value,)
    return session


def test_supplier_format():
    assert _format_code("supplier", 1, dt.date(2025, 1, 1), None) == "SUP-001"
    assert _format_code("supplier", 42, dt.date(2025, 1, 1), None) == "SUP-042"


def test_buyer_format():
    assert _format_code("buyer", 5, dt.date(2025, 1, 1), None) == "BUY-005"


def test_worker_format():
    assert _format_code("worker", 10, dt.date(2025, 1, 1), None) == "EMP-010"


def test_yarn_batch_format():
    result = _format_code("yarn_batch", 3, dt.date(2025, 6, 15), None)
    assert result == "YB-2506-03"


def test_purchase_order_format():
    result = _format_code("purchase_order", 1, dt.date(2026, 10, 1), None)
    assert result == "PO-2610-01"


def test_order_starts_at_101():
    assert _format_code("order", 1, dt.date(2025, 1, 1), None) == "ORD-101"
    assert _format_code("order", 99, dt.date(2025, 1, 1), None) == "ORD-199"


def test_job_requires_order_no():
    assert _format_code("job", 1, dt.date(2025, 1, 1), 101) == "JOB-101-01"


def test_job_sequence_key_requires_order_no():
    with pytest.raises(ValueError):
        _sequence_key("job", dt.date(2025, 1, 1), None)


def test_roll_requires_order_no():
    assert _format_code("roll", 3, dt.date(2025, 1, 1), 101) == "ROLL-101-03"


def test_invoice_fy_label():
    result = _format_code("invoice", 1, dt.date(2025, 4, 1), None)
    assert "25-26" in result


def test_dispatch_format():
    result = _format_code("dispatch", 1, dt.date(2026, 1, 1), None)
    assert result == "DSP-2601-01"


def test_ripple_event_format():
    result = _format_code("ripple_event", 1, dt.date(2026, 10, 5), None)
    assert result == "RPL-261005-01"


def test_next_code_increments():
    session = _make_session(start_value=4)
    result = next_code(session, "supplier")
    assert result == "SUP-005"


def test_next_code_inserts_on_missing_row():
    session = MagicMock()
    session.execute.return_value.fetchone.side_effect = [None, (0,)]
    result = next_code(session, "buyer")
    assert result == "BUY-001"
