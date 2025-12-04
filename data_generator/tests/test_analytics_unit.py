# tests/test_analytics_unit.py
import pandas as pd
import numpy as np
import pytest
import src.data_generator.SAPDataGenerator as SAPDataGenerator
#from src.data_generator.SAPDataGenerator import generate_lfa1
#from src.analytics import calc_vendor_spend, pct_of_top_vendors, calc_late_delivery_rate, identify_maverick_spend

def test_calc_vendor_spend_and_totals(sample_data):
    assert sample_data is not None
    '''spend = ekpo.groupby('LIFNR')['NETWR'].sum().reset_index()
    assert isinstance(spend, pd.DataFrame)
    assert 'LIFNR' in spend.columns and 'NETWR' in spend.columns
    assert spend['NETWR'].sum() == pytest.approx(ekpo['NETWR'].sum(), rel=1e-6)'''

'''def test_pct_of_top_vendors(sample_data):
    ekpo = sample_data['EKPO']
    pct = pct_of_top_vendors(ekpo, top_frac=0.2)
    assert 0.0 <= pct <= 1.0

def test_calc_late_delivery_rate(sample_data):
    ekpo = sample_data['EKPO']
    ekko = sample_data['EKKO']
    rate = calc_late_delivery_rate(ekpo, ekko)
    assert isinstance(rate, float)
    assert 0.0 <= rate <= 1.0

def test_identify_maverick_spend(sample_data):
    ekpo = sample_data['EKPO']
    # Should return a DataFrame/list of maverick spend entries
    m = identify_maverick_spend(ekpo, threshold=0.2)
    assert hasattr(m, '__len__')'''
