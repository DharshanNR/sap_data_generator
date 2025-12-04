# dashboard_data_prep.py
import pandas as pd
import numpy as np
import datetime
import os
#import streamlit as st # Used for caching decorators

DATA_DIR = "generated_sap_data" # Assuming this is where your CSVs are

#@st.cache_data(ttl=3600) # Cache data for 1 hour
def load_and_preprocess_data():
    print("Loading and preprocessing data...")
    
    # --- 1. Load Raw Data ---
    try:
        lfa1 = pd.read_csv(os.path.join(DATA_DIR, "LFA1.csv"))
        mara = pd.read_csv(os.path.join(DATA_DIR, "MARA.csv"))
        ekko = pd.read_csv(os.path.join(DATA_DIR, "EKKO.csv"))
        ekpo = pd.read_csv(os.path.join(DATA_DIR, "EKPO.csv"))
        ekbe = pd.read_csv(os.path.join(DATA_DIR, "EKBE.csv"))
        vendor_contracts = pd.read_csv(os.path.join(DATA_DIR, "vendor_contract.csv"))
    except FileNotFoundError as e:
        #st.error(f"Error loading data: {e}. Make sure CSV files are in the '{DATA_DIR}' directory.")
        #st.stop()
        pass

    # --- 2. Type Conversions and Basic Cleaning ---
    # Dates
    ekko['AEDAT'] = pd.to_datetime(ekko['AEDAT'])
    ekpo['EINDT'] = pd.to_datetime(ekpo['EINDT'])
    ekbe['BUDAT'] = pd.to_datetime(ekbe['BUDAT'])
    ekbe['ACTUAL_DELIVERY_DATE'] = pd.to_datetime(ekbe['ACTUAL_DELIVERY_DATE'])
    vendor_contracts['VALID_FROM'] = pd.to_datetime(vendor_contracts['VALID_FROM'])
    vendor_contracts['VALID_TO'] = pd.to_datetime(vendor_contracts['VALID_TO'])
    lfa1['ERDAT'] = pd.to_datetime(lfa1['ERDAT'])
    mara['ERSDA'] = pd.to_datetime(mara['ERSDA'])

    # Numeric
    ekpo['MENGE'] = pd.to_numeric(ekpo['MENGE'], errors='coerce')
    ekpo['NETPR'] = pd.to_numeric(ekpo['NETPR'], errors='coerce')
    ekpo['NETWR'] = pd.to_numeric(ekpo['NETWR'], errors='coerce')
    ekbe['MENGE'] = pd.to_numeric(ekbe['MENGE'], errors='coerce')
    ekbe['DMBTR'] = pd.to_numeric(ekbe['DMBTR'], errors='coerce')
    vendor_contracts['CONTRACT_PRICE'] = pd.to_numeric(vendor_contracts['CONTRACT_PRICE'], errors='coerce')
    vendor_contracts['VOLUME_COMMITMENT'] = pd.to_numeric(vendor_contracts['VOLUME_COMMITMENT'], errors='coerce')

    # Fill NaNs for numeric columns where appropriate
    ekpo.fillna({'MENGE': 0, 'NETPR': 0, 'NETWR': 0}, inplace=True)
    ekbe.fillna({'MENGE': 0, 'DMBTR': 0}, inplace=True)
    vendor_contracts.fillna({'CONTRACT_PRICE': 0, 'VOLUME_COMMITMENT': 0}, inplace=True)

    # --- 3. Merge DataFrames for Analysis ---
    # Merge EKKO and EKPO
    df_po_items = pd.merge(ekpo, ekko, on='EBELN', suffixes=('_item', '_header'))
    
    # Merge with LFA1 (Vendor Master)
    df_po_items = pd.merge(df_po_items, lfa1, left_on='LIFNR_header', right_on='LIFNR', suffixes=('_po', '_vendor'))
    
    # Merge with MARA (Material Master)
    df_po_items = pd.merge(df_po_items, mara, on='MATNR', suffixes=('_po', '_material'))

    # --- 4. Calculate Derived Metrics ---
    # Total Spend per PO Item
    df_po_items['TOTAL_SPEND'] = df_po_items['NETWR']
    

    # On-Time Delivery Status (for EKBE 'E' records)
    df_ekbe_gr = ekbe[ekbe['BEWTP'] == 'E'].copy()
    
    df_ekbe_gr = pd.merge(df_ekbe_gr, ekpo[['EBELN', 'EBELP', 'EINDT','LIFNR']], on=['EBELN', 'EBELP'], how='left')
    df_ekbe_gr['IS_LATE'] = (df_ekbe_gr['ACTUAL_DELIVERY_DATE'] > df_ekbe_gr['EINDT']).astype(int)
    df_ekbe_gr['DELIVERY_DELAY_DAYS'] = (df_ekbe_gr['ACTUAL_DELIVERY_DATE'] - df_ekbe_gr['EINDT']).dt.days.apply(lambda x: max(0, x))

    # Contract Compliance Rate (simplified: % of POs that are 'NB')
    total_pos = len(ekko)
    contract_pos = len(ekko[ekko['BSART'] == 'NB'])
    contract_compliance_rate = contract_pos / total_pos if total_pos > 0 else 0

    # --- 5. Aggregations for KPIs and Charts ---
    # Monthly Spend
    monthly_spend = df_po_items.set_index('AEDAT').resample('MS')['TOTAL_SPEND'].sum().reset_index()
    monthly_spend.rename(columns={'AEDAT': 'MONTH', 'TOTAL_SPEND': 'SPEND'}, inplace=True)

    # Spend by Category
    spend_by_category = df_po_items.groupby('MATKL_material')['TOTAL_SPEND'].sum().reset_index()
    spend_by_category.rename(columns={'MATKL_material': 'CATEGORY'}, inplace=True)

    
    # Vendor Performance (On-Time Delivery %)
    vendor_delivery_summary = df_ekbe_gr.groupby('LIFNR').agg(
        total_deliveries=('EBELN', 'count'),
        late_deliveries=('IS_LATE', 'sum')
    ).reset_index()
    vendor_delivery_summary['ON_TIME_DELIVERY_RATE'] = (1 - (vendor_delivery_summary['late_deliveries'] / vendor_delivery_summary['total_deliveries'])).fillna(0)

    # Vendor Spend
    vendor_spend_summary = df_po_items.groupby('LIFNR_header')['TOTAL_SPEND'].sum().reset_index()
    vendor_spend_summary.rename(columns={'LIFNR_header': 'LIFNR'}, inplace=True)

    # Merge vendor spend and delivery performance
    vendor_summary = pd.merge(vendor_spend_summary, vendor_delivery_summary, on='LIFNR', how='left')
    vendor_summary = pd.merge(vendor_summary, lfa1[['LIFNR', 'NAME1', 'LAND1', 'KTOKK', 'SPERR']], on='LIFNR', how='left')
    vendor_summary['ON_TIME_DELIVERY_RATE'].fillna(0, inplace=True) # Vendors with no deliveries are 0% on-time
    vendor_summary['TOTAL_SPEND_PERCENT'] = (vendor_summary['TOTAL_SPEND'] / vendor_summary['TOTAL_SPEND'].sum()).fillna(0)

    # --- 6. Savings Opportunities (Simplified for example) ---
    # Maverick Spend: POs to non-contracted vendors for contracted materials
    # This requires a more complex join and logic. For now, a placeholder.
    # Example: Identify materials with contracts but purchased from non-contracted vendors
    # For simplicity, let's assume 'Maverick' is a portion of non-contract POs.
    
    df_po_items['IS_CONTRACT_PO'] = (df_po_items['BSART'] == 'NB')
    maverick_spend_potential = df_po_items[~df_po_items['IS_CONTRACT_PO']]['TOTAL_SPEND'].sum() * 0.1 # 10% of non-contract spend

    # Price Variance: Identify materials where NETPR > avg_contract_price
    # This needs a robust way to get 'avg_contract_price' for each material.
    # For now, let's use a simplified approach:
    material_avg_contract_price = vendor_contracts.groupby('MATNR')['CONTRACT_PRICE'].mean().reset_index()
    df_po_items_with_contract_price = pd.merge(df_po_items, material_avg_contract_price, on='MATNR', how='left')
    df_po_items_with_contract_price['PRICE_VARIANCE'] = df_po_items_with_contract_price['NETPR'] - df_po_items_with_contract_price['CONTRACT_PRICE']
    price_variance_opportunities = df_po_items_with_contract_price[
        (df_po_items_with_contract_price['PRICE_VARIANCE'] > 0) &
        (~df_po_items_with_contract_price['IS_CONTRACT_PO']) # Only consider non-contract POs
    ]['PRICE_VARIANCE'].sum()

    # Consolidation Opportunities: Materials bought from many vendors
    material_vendor_counts = df_po_items.groupby('MATNR')['LIFNR_header'].nunique().reset_index(name='NUM_VENDORS')
    consolidation_opportunities_materials = material_vendor_counts[material_vendor_counts['NUM_VENDORS'] > 2]
    # Estimate savings as a percentage of spend for these materials
    consolidation_spend = df_po_items[df_po_items['MATNR'].isin(consolidation_opportunities_materials['MATNR'])]['TOTAL_SPEND'].sum()
    consolidation_savings_potential = consolidation_spend * 0.05 # 5% savings

    savings_opportunities = {
        'Maverick Spend': maverick_spend_potential,
        'Price Variance': price_variance_opportunities,
        'Consolidation': consolidation_savings_potential
    }

    # --- 7. Trend Indicators (for KPIs) ---
    # For simplicity, let's calculate % change vs. previous period (e.g., last 3 months vs prior 3 months)
    # This needs to be dynamic based on the selected date range in the dashboard.
    # For now, we'll return the full data and calculate trends in the dashboard.

    print("Data preprocessing complete.")
    return {
        "lfa1": lfa1,
        "mara": mara,
        "ekko": ekko,
        "ekpo": ekpo,
        "ekbe": ekbe,
        "vendor_contracts": vendor_contracts,
        "df_po_items": df_po_items,
        "df_ekbe_gr": df_ekbe_gr,
        "monthly_spend": monthly_spend,
        "spend_by_category": spend_by_category,
        "vendor_summary": vendor_summary,
        "contract_compliance_rate": contract_compliance_rate,
        "savings_opportunities": savings_opportunities
    }

# Call the function to load and preprocess data
# This will be called by app.py and cached.
# preprocessed_data = load_and_preprocess_data()

if __name__ == "__main__":
    data = load_and_preprocess_data()
    print("Loaded data keys:", data.keys())