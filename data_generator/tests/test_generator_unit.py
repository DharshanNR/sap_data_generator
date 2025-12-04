# tests/test_generator_unit.py
import math
import pandas as pd
import pytest
from tests.Config import sampleconfig
import src.data_generator.SAPDataGenerator as SAPDataGenerator 
# Import functions from your generator module.
# Adjust the import path if your code is placed elsewhere.
#from data_generator.generator import generate_vendors, generate_price, generate_quantity, generate_po_items, generate_goods_receipts
config=sampleconfig()
def test_generate_vendors_count(function_hook):
    """generate_vendors should return exact count requested."""
    vendors = function_hook.generate_lfa1()
    assert isinstance(vendors, (list, pd.DataFrame)), "Expected vendors to be list or DataFrame"
    # Support both shapes: if DataFrame, check length; if list, check len(list)
    length = len(vendors)
    assert length == config.NUM_VENDORS, f"Expected {config.NUM_VENDORS} vendors, got {length}"

def test_vendor_pareto_distribution(sample_data):
    """Vendor generation should be able to produce Pareto-like spend if requested."""
    vendors = sample_data['LFA1']


    merged_df = pd.merge(sample_data["EKKO"][["EBELN", "LIFNR"]], sample_data["EKPO"][["EBELN", "NETWR"]], on="EBELN", how="inner")
    vendor_spend = merged_df.groupby("LIFNR")["NETWR"].sum().sort_values(ascending=False).reset_index()
    total_spend = vendor_spend["NETWR"].sum()
    
            
    if total_spend > 0:
            num_vendors = len(vendor_spend)
            top_20_percent_vendors = int(num_vendors * 0.20)
                
            if top_20_percent_vendors > 0:
                    spend_by_top_vendors = vendor_spend.head(top_20_percent_vendors)["NETWR"].sum()
                    actual_percentage = spend_by_top_vendors / total_spend
                    
                    expected_percentage = 0.50
                    tolerance = 0.10
                    assert (expected_percentage - tolerance <= actual_percentage <= expected_percentage + tolerance), f"Pareto % out of expected tolerance: {actual_percentage}"# Allow some tolerance due to randomness

    # Accept both DataFrame and list-of-dicts
    assert True  # If we reach here, the test passes

'''def test_pricing_logic_contract_discount():
    """Contract pricing logic should apply discount (if contract True)."""
    base = 100.0
    p_contract = generate_price(base_price=base, contract=True)
    p_non = generate_price(base_price=base, contract=False)
    assert p_contract <= base, "Contract price must be <= base price"
    assert p_non >= 0, "Non-contract price must be non-negative"
    # contract should differ from non-contract sometimes
    assert not math.isclose(p_contract, p_non) or True  # allow equality but still validate non-negativity
'''
def test_generate_mara_count(function_hook):
    """generate_vendors should return exact count requested."""
    material = function_hook.generate_mara()
    assert isinstance(material, (list, pd.DataFrame)), "Expected vendors to be list or DataFrame"
    # Support both shapes: if DataFrame, check length; if list, check len(list)
    length = len(material)
    assert length == config.NUM_MATERIALS, f"Expected {config.NUM_MATERIALS} vendors, got {length}"
'''
def test_generate_po_items_links_header_and_vendor(small_sample):
    """generate_po_items should attach vendor and po header info correctly."""
    # Provide a minimal header object and vendors list
    headers = small_sample['EKKO'].head(1).to_dict('records')
    vendors = small_sample['LFA1'].to_dict('records')
    items = generate_po_items(headers=headers, vendors=vendors, lines_per_po=2)
    assert items, "Expected items to be generated"
    first = items[0]
    assert 'EBELN' in first and 'LIFNR' in first, "Expected EBELN and LIFNR fields in PO items"

def test_generate_goods_receipts_count_logic(small_sample):
    """Total goods receipt quantity must equal PO quantities when full receipts."""
    ekpo = small_sample['EKPO']
    gr = generate_goods_receipts(ekpo)
    # Each generated receipt should refer to an EKPO entry; ensure counts not zero
    assert len(gr) > 0
    # Sum of receipt amounts should be roughly equal to total NETWR
    total_netwr = ekpo['NETWR'].sum()
    total_gr_amount = sum(r.get('AMOUNT', 0) if isinstance(r, dict) else r['AMOUNT'] for r in gr)
    assert abs(total_netwr - total_gr_amount) / (total_netwr if total_netwr else 1) < 0.05, \
        "Total goods receipt amounts should match netwr within 5%"

# Edge unit test: negative price never created
def test_negative_price_never_generated():
    for _ in range(20):
        p = generate_price()
        assert p >= 0, f"Generated negative price {p}"'''






