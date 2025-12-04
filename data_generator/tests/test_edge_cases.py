# tests/test_edge_cases.py
import pytest
from data_generator.generator import run_full_data_pipeline
from data_generator.validation import run_all_checks

def test_empty_dataset():
    # Run validators on empty dataset structure (no rows)
    empty = {'EKKO': [], 'EKPO': [], 'LFA1': [], 'MARA': [], 'EKBE': [], 'VENDOR_CONTRACTS': []}
    report = run_all_checks(empty)
    # Should still produce report object; check it's not None
    assert report is not None

def test_single_vendor_material_po():
    # create a dataset with single vendor/material/PO
    cfg = {"vendor_count": 1, "material_count": 1, "po_count": 1, "lines_per_po": 1}
    out = run_full_data_pipeline(config=cfg)
    assert len(out['LFA1']) == 1
    assert len(out['MARA']) == 1
    assert len(out['EKKO']) == 1
    assert len(out['EKPO']) >= 1

def test_missing_optional_fields_handling(sample_data):
    # drop optional columns and ensure validations still run (produce warnings)
    sample = sample_data.copy()
    if 'BSART' in sample['EKKO'].columns:
        sample['EKKO'] = sample['EKKO'].drop(columns=['BSART'])
    report = run_all_checks(sample)
    assert isinstance(report, dict)

def test_extreme_large_values(sample_data):
    sample = sample_data.copy()
    # Inject extreme NETPR
    sample['EKPO'].loc[0,'NETPR'] = 1e9
    # statistical validation should detect outlier
    report = run_all_checks(sample)
    # We expect at least one statistical finding
    assert any(f['category']=='statistical' for f in report.get('findings', []))

def test_date_boundary_conditions(sample_data):
    sample = sample_data.copy()
    # push dates beyond valid range
    sample['EKKO'].loc[0,'AEDAT'] = '2015-01-01'
    report = run_all_checks(sample)
    assert isinstance(report, dict)