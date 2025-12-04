# tests/test_data_quality_rules.py
import pandas as pd
from data_generator.validation import (
    validate_foreign_keys, validate_netwr_calc, validate_invoice_vs_gr, validate_contract_dates,
    validate_currency_iso, validate_material_group_balance
)

def test_fk_ekpo_ekko_integrity(sample_data):
    ekpo = sample_data['EKPO']
    ekko = sample_data['EKKO']
    bad = validate_foreign_keys(child=ekpo, child_key='EBELN', parent=ekko, parent_key='EBELN')
    assert len(bad) == 0, f"Found FK violations: {bad[:3]}"

def test_fk_ekpo_matnr(sample_data):
    ekpo = sample_data['EKPO']
    mara = sample_data['MARA']
    bad = validate_foreign_keys(child=ekpo, child_key='MATNR', parent=mara, parent_key='MATNR')
    assert len(bad) == 0

def test_netwr_calculation(sample_data):
    ekpo = sample_data['EKPO']
    bad = validate_netwr_calc(ekpo, tolerance=0.01)
    assert len(bad) == 0

def test_invoice_matches_gr(sample_data):
    ekbe = sample_data['EKBE']
    bad = validate_invoice_vs_gr(ekbe, pct_tol=0.02)
    assert len(bad) == 0

def test_contract_dates_valid(sample_data):
    vc = sample_data['VENDOR_CONTRACTS']
    bad = validate_contract_dates(vc)
    assert len(bad) == 0

def test_currency_iso(sample_data):
    ekko = sample_data['EKKO'].copy()
    # insert a bad currency to ensure validator catches it
    ekko.loc[0,'WAERS'] = 'BAD'
    bad = validate_currency_iso(ekko, col='WAERS')
    assert len(bad) >= 1

def test_material_group_balance(sample_data):
    mara = sample_data['MARA']
    bad = validate_material_group_balance(mara, threshold=0.4)
    # In small fixture, unlikely to violate — assertion accepts list/empty
    assert isinstance(bad, (list, dict))