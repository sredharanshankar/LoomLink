import pytest
from app.core.units import (
    kg_to_g, g_to_kg_str,
    m_to_cm, cm_to_m_str,
    rupees_to_paise, paise_to_rupees_str,
    amount_in_words_inr,
)


def test_kg_to_g():
    assert kg_to_g(1) == 1000
    assert kg_to_g(0) == 0


def test_g_to_kg_str():
    assert g_to_kg_str(1500) == "1.500"
    assert g_to_kg_str(0) == "0.000"


def test_m_to_cm():
    assert m_to_cm(1) == 100
    assert m_to_cm(0) == 0


def test_cm_to_m_str():
    assert cm_to_m_str(250) == "2.50"
    assert cm_to_m_str(0) == "0.00"


def test_rupees_to_paise():
    assert rupees_to_paise(1) == 100
    assert rupees_to_paise(1.5) == 150


def test_paise_to_rupees_str():
    assert paise_to_rupees_str(100000) == "₹1,000.00"
    assert paise_to_rupees_str(12345678) == "₹1,23,456.78"
    assert paise_to_rupees_str(0) == "₹0.00"


def test_amount_in_words_inr():
    result = amount_in_words_inr(10000000)
    assert "One Lakh" in result or "one lakh" in result.lower()
    assert "Only" in result