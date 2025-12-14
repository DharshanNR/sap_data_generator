# tests/test_data_quality_rules.py
import pandas as pd
import numpy as np
import pytest



def test_fk_ekpo_ekko_integrity(sample_data):
    """
    Validates the foreign key integrity between EKPO (PO Line Items) 
    and EKKO (PO Header) DataFrames using pure Pandas logic.

    Checks that every EBELN (PO Number) present in the child table (EKPO)
    also exists in the parent table (EKKO).

    Args:
        sample_data (dict): A dictionary containing 'EKPO' and 'EKKO' DataFrames.
    """
    ekpo = sample_data['EKPO']
    ekko = sample_data['EKKO']
    child_keys = ekpo['EBELN'].unique()
    parent_keys = ekko['EBELN'].unique()
    bad_keys = np.setdiff1d(child_keys, parent_keys)

    # 4. Use the assertion logic provided in the original prompt
    assert len(bad_keys) == 0, f"Found FK violations (EBELN mismatch): {bad_keys[:10]} (showing first 10 violations)"

    print(f"Foreign Key integrity check passed. All {len(child_keys)} POs in EKPO match a header in EKKO.")

def test_fk_ekpo_matnr(sample_data):
    """
    Validates the foreign key integrity between EKPO (PO Line Items) 
    and MARA (Material Master) DataFrames using pure Pandas/Numpy logic.

    Checks that every MATNR (Material Number) present in the child table (EKPO)
    also exists in the parent table (MARA).

    Args:
        sample_data (dict): A dictionary containing 'EKPO' and 'MARA' DataFrames.
    """
    ekpo = sample_data['EKPO']
    mara = sample_data['MARA']

    child_material_numbers = ekpo['MATNR'].unique()
    parent_material_numbers = mara['MATNR'].unique()
    missing_materials = np.setdiff1d(child_material_numbers, parent_material_numbers)
    assert len(missing_materials) == 0, f"Found FK violations (MATNR mismatch): {missing_materials[:10]} materials in EKPO do not exist in MARA."

def test_netwr_calculation_inline(sample_data):
    """
    Test function that validates NETWR calculation within a single scope.

    Checks that EKPO['NETWR'] == EKPO['MENGE'] * EKPO['NETPR'] 
    for all rows within the specified tolerance.

    Args:
        sample_data (dict): Dictionary containing the 'EKPO' DataFrame.
        tolerance (float): The allowed floating-point error margin.
    """
    ekpo = sample_data['EKPO']
    calculated_netwr = ekpo['MENGE'] * ekpo['NETPR']
    is_calculation_correct = np.isclose(ekpo['NETWR'], calculated_netwr, atol=.2)
    bad_rows_df = ekpo[~is_calculation_correct]
    assert len(bad_rows_df) == 0, f"Found {len(bad_rows_df)} rows with incorrect NETWR calculation. First 3 examples:\n{bad_rows_df[['MENGE', 'NETPR', 'NETWR']].head(3).to_string(index=False)}"
