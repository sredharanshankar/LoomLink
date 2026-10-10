"""Unit tests for master-data validation and service helpers."""
from __future__ import annotations
import uuid
import pytest
from unittest.mock import MagicMock, patch
from app.core.errors import AppError


# ---------------------------------------------------------------------------
# Validation helpers — no DB needed
# ---------------------------------------------------------------------------

from app.services.master_data import (
    _validate_gstin,
    _validate_phone,
    _GSTIN_RE,
    _PHONE_RE,
)


class TestGstinValidation:
    def test_valid_gstin_passes(self):
        _validate_gstin("29ABCDE1234F1Z5")

    def test_none_passes(self):
        _validate_gstin(None)

    def test_empty_string_passes(self):
        _validate_gstin("")

    def test_short_gstin_raises(self):
        with pytest.raises(AppError) as exc:
            _validate_gstin("29ABCDE1234F1Z")
        assert exc.value.code == "VALIDATION_ERROR"

    def test_lowercase_raises(self):
        with pytest.raises(AppError):
            _validate_gstin("29abcde1234f1z5")

    def test_wrong_z_position_raises(self):
        with pytest.raises(AppError):
            _validate_gstin("29ABCDE1234F1A5")

    def test_valid_gstin_regex(self):
        assert _GSTIN_RE.match("07AAGFF2194N1Z1")
        assert _GSTIN_RE.match("33GSPDB8261E1ZJ")

    def test_invalid_state_code(self):
        with pytest.raises(AppError):
            _validate_gstin("00ABCDE1234F1Z5")


class TestPhoneValidation:
    def test_valid_10_digit(self):
        _validate_phone("9876543210")

    def test_valid_with_91_prefix(self):
        _validate_phone("+919876543210")

    def test_none_passes(self):
        _validate_phone(None)

    def test_5_series_invalid(self):
        with pytest.raises(AppError) as exc:
            _validate_phone("5123456789")
        assert exc.value.code == "VALIDATION_ERROR"

    def test_too_short_raises(self):
        with pytest.raises(AppError):
            _validate_phone("987654321")

    def test_landline_prefix_raises(self):
        with pytest.raises(AppError):
            _validate_phone("0441234567")

    def test_valid_starts_with_6(self):
        _validate_phone("6543210987")

    def test_valid_starts_with_7(self):
        _validate_phone("7123456789")

    def test_valid_starts_with_8(self):
        _validate_phone("8001234567")


# ---------------------------------------------------------------------------
# SEED §5 — fabric type validation (yarn_g_per_100m > 0)
# ---------------------------------------------------------------------------

from app.services.master_data import create_fabric_type


def test_create_fabric_type_rejects_zero_yarn_g():
    db = MagicMock()
    db.scalar.side_effect = [MagicMock(id=uuid.uuid4()), MagicMock(id=uuid.uuid4())]
    body = {
        "name": "Test Fabric",
        "yarn_type_id": str(uuid.uuid4()),
        "route_template_id": str(uuid.uuid4()),
        "width_cm": 150,
        "yarn_g_per_100m": 0,
    }
    with pytest.raises(AppError) as exc:
        create_fabric_type(db, body, {"id": str(uuid.uuid4()), "role": "owner"})
    assert exc.value.code == "VALIDATION_ERROR"


def test_create_fabric_type_rejects_negative_yarn_g():
    db = MagicMock()
    body = {
        "name": "Test Fabric",
        "yarn_type_id": str(uuid.uuid4()),
        "route_template_id": str(uuid.uuid4()),
        "width_cm": 150,
        "yarn_g_per_100m": -10,
    }
    with pytest.raises(AppError) as exc:
        create_fabric_type(db, body, {"id": str(uuid.uuid4()), "role": "owner"})
    assert exc.value.code == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# Machine floor grid validation
# ---------------------------------------------------------------------------

from app.services.master_data import create_machine


def test_create_machine_rejects_out_of_bounds_x():
    db = MagicMock()
    body = {"code": "WV-99", "stage": "weaving", "floor_x": 13, "floor_y": 1}
    with pytest.raises(AppError) as exc:
        create_machine(db, body, {"id": str(uuid.uuid4()), "role": "owner"})
    assert exc.value.code == "VALIDATION_ERROR"


def test_create_machine_rejects_out_of_bounds_y():
    db = MagicMock()
    body = {"code": "WV-99", "stage": "weaving", "floor_x": 1, "floor_y": 9}
    with pytest.raises(AppError) as exc:
        create_machine(db, body, {"id": str(uuid.uuid4()), "role": "owner"})
    assert exc.value.code == "VALIDATION_ERROR"


def test_create_machine_rejects_floor_origin():
    db = MagicMock()
    body = {"code": "WV-99", "stage": "weaving", "floor_x": 0, "floor_y": 0}
    with pytest.raises(AppError) as exc:
        create_machine(db, body, {"id": str(uuid.uuid4()), "role": "owner"})
    assert exc.value.code == "VALIDATION_ERROR"


def test_create_machine_rejects_stage_code_mismatch():
    db = MagicMock()
    body = {"code": "WV-01", "stage": "dyeing", "floor_x": 5, "floor_y": 3}
    with pytest.raises(AppError) as exc:
        create_machine(db, body, {"id": str(uuid.uuid4()), "role": "owner"})
    assert exc.value.code == "VALIDATION_ERROR"


def test_create_machine_rejects_duplicate_floor_position():
    db = MagicMock()
    db.execute.return_value.fetchone.return_value = MagicMock()  # conflict row
    body = {"code": "WV-05", "stage": "weaving", "floor_x": 4, "floor_y": 1}
    with pytest.raises(AppError) as exc:
        create_machine(db, body, {"id": str(uuid.uuid4()), "role": "owner"})
    assert exc.value.code == "CONFLICT"


# ---------------------------------------------------------------------------
# Scan service — prefix dispatch
# ---------------------------------------------------------------------------

from app.services.scan import resolve


def test_scan_resolves_yarn_batch():
    code = "YB-2610-01"
    db = MagicMock()
    row = MagicMock()
    row.id = uuid.uuid4()
    row.code = code
    row.status = "available"
    row.yarn_type_id = uuid.uuid4()
    row.received_g = 50000
    row.remaining_g = 48000
    db.scalar.return_value = row
    result = resolve(db, code, {"id": str(uuid.uuid4()), "role": "operator"})
    assert result["type"] == "yarn_batch"
    assert result["code"] == code


def test_scan_resolves_order():
    code = "ORD-101"
    db = MagicMock()
    row = MagicMock()
    row.id = uuid.uuid4()
    row.code = code
    row.status = "confirmed"
    row.buyer_id = uuid.uuid4()
    row.fabric_type_id = uuid.uuid4()
    row.quantity_cm = 500000
    row.due_date = None
    db.scalar.return_value = row
    result = resolve(db, code, {"id": str(uuid.uuid4()), "role": "operator"})
    assert result["type"] == "order"


def test_scan_resolves_worker():
    code = "EMP-001"
    db = MagicMock()
    row = MagicMock()
    row.id = uuid.uuid4()
    row.code = code
    row.name = "Ravi"
    row.department = "weaving"
    db.scalar.return_value = row
    result = resolve(db, code, {"id": str(uuid.uuid4()), "role": "manager"})
    assert result["type"] == "worker"


def test_scan_resolves_machine_by_code():
    code = "WV-01"
    db = MagicMock()
    row = MagicMock()
    row.id = uuid.uuid4()
    row.code = code
    row.status = "idle"
    row.stage = "weaving"
    row.current_job_id = None
    db.scalar.return_value = row
    result = resolve(db, code, {"id": str(uuid.uuid4()), "role": "operator"})
    assert result["type"] == "machine"
    assert result["code"] == code


def test_scan_unknown_code_raises():
    db = MagicMock()
    db.scalar.return_value = None
    with pytest.raises(AppError) as exc:
        resolve(db, "UNKNOWN-XYZ", {"id": str(uuid.uuid4()), "role": "operator"})
    assert exc.value.code == "NOT_FOUND"
