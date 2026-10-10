import pytest
from app.core.errors import AppError


def test_app_error_attrs():
    e = AppError("NOT_FOUND", "Resource missing.")
    assert e.code == "NOT_FOUND"
    assert e.message == "Resource missing."
    assert e.status_code == 404


def test_app_error_custom_status():
    e = AppError("CUSTOM", "msg", status=418)
    assert e.status_code == 418


def test_app_error_details():
    e = AppError("VALIDATION_ERROR", "bad", details={"field": "name"})
    assert e.details["field"] == "name"