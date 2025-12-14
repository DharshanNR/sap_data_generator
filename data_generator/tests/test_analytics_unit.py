# tests/test_analytics_unit.py
import pandas as pd
import numpy as np
import pytest

#from src.data_generator.SAPDataGenerator import generate_lfa1
#from src.analytics import calc_vendor_spend, pct_of_top_vendors, calc_late_delivery_rate, identify_maverick_spend

def test_calc_vendor_spend_and_totals(sample_data):
    """
    Calculates total spend per vendor and verifies that the sum of 
    vendor spends matches the total spend of the EKPO data.

    Args:
        sample_data (dict): A dictionary containing the 'EKPO' DataFrame.
    """
    assert sample_data is not None
    
    
    ekpo = sample_data.get('EKPO')
    ekko = sample_data.get('EKKO')
    if ekpo is None:
        raise ValueError("Sample data must contain an 'EKPO' DataFrame.")
    merged_po_data = pd.merge(
        ekpo[['EBELN','NETWR']], 
        ekko[ ['EBELN','LIFNR']],  # Only select the necessary columns from EKKO
        on='EBELN', 
        how='inner'
    )

    spend_per_vendor = merged_po_data.groupby('LIFNR')['NETWR'].sum().reset_index()
    assert isinstance(spend_per_vendor, pd.DataFrame)
    assert 'LIFNR' in spend_per_vendor.columns and 'NETWR' in spend_per_vendor.columns
    
    # Ensure the 'NETWR' column contains numeric data
    assert pd.api.types.is_numeric_dtype(spend_per_vendor['NETWR'])
    total_spend_from_vendor_sums = spend_per_vendor['NETWR'].sum()
    
    # Calculate the overall total spend directly from the original EKPO table
    overall_total_ekpo_spend = ekpo['NETWR'].sum()

    # Assert that these two totals match exactly (using pytest.approx for float safety)
    # rel=1e-6 allows for minor floating point differences
    assert total_spend_from_vendor_sums == pytest.approx(overall_total_ekpo_spend, rel=1e-6), \
        f"Total spend mismatch! Sum of vendor spends ({total_spend_from_vendor_sums}) " \
        f"does not equal overall EKPO spend ({overall_total_ekpo_spend})."

