import pytest
from app.core.security import (
    hash_password, verify_password,
    hash_pin, verify_pin,
    create_access_token, decode_access_token,
    generate_refresh_token, hash_refresh_token,
    generate_tracking_token,
)


def test_password_round_trip():
    h = hash_password("secret123")
    assert verify_password("secret123", h)
    assert not verify_password("wrong", h)


def test_pin_round_trip():
    h = hash_pin("123456")
    assert verify_pin("123456", h)
    assert not verify_pin("000000", h)


def test_access_token_round_trip():
    token, exp = create_access_token("user-1", "owner")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-1"
    assert payload["role"] == "owner"
    assert "jti" in payload
    assert "exp" in payload


def test_refresh_token_distinct():
    raw1, h1 = generate_refresh_token()
    raw2, h2 = generate_refresh_token()
    assert raw1 != raw2
    assert h1 != h2


def test_hash_refresh_token_deterministic():
    raw, _ = generate_refresh_token()
    assert hash_refresh_token(raw) == hash_refresh_token(raw)


def test_tracking_token_url_safe():
    t = generate_tracking_token()
    assert len(t) >= 24
    assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=" for c in t)