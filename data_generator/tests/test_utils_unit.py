# tests/test_utils_unit.py
import pytest
from data_generator.utils import iso_date_str, pct, safe_divide, validate_currency_code

def test_iso_date_str_format():
    s = iso_date_str()
    assert isinstance(s, str)
    assert len(s.split('-')) == 3

def test_pct_calculation():
    assert pct(25, 100) == 0.25
    assert pct(0, 100) == 0.0

def test_safe_divide_zero():
    assert safe_divide(0, 10) == 0.0
    assert safe_divide(10, 0) == 0.0

def test_validate_currency_code():
    assert validate_currency_code('USD') is True
    assert validate_currency_code('INR') is True
    assert validate_currency_code('US') is False






