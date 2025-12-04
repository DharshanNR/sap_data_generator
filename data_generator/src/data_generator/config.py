import datetime

class Config:
    # General
    RANDOM_SEED = 42
    OUTPUT_DIR = "generated_sap_data"
    OUTPUT_FORMAT = "csv" # or "parquet"

    # Date Range
    START_DATE = datetime.date(2020, 1, 1)
    END_DATE = datetime.date(2024, 12, 31)

    # Record Counts
    NUM_VENDORS = 100# Slightly more than 1000 to ensure 1000 valid ones
    NUM_MATERIALS = 500 # Slightly more than 5000
    NUM_PO_HEADERS = 100 # Slightly more than 10000
    NUM_PO_LINE_ITEMS_TARGET = 400 # Target for EKPO
    NUM_PO_HISTORY_TARGET = 300 # Target for EKBE
    NUM_CONTRACTS_TARGET = 200 # Target for VENDOR_CONTRACTS

    # LFA1 - Vendor Master
    VENDOR_BLOCKED_PERCENTAGE =0.05 # 5% blocked
    VENDOR_PREFERRED_PERCENTAGE = 0.10 # 10% preferred
    VENDOR_PERCENTAGE_FOR_DISTRIBUTION_OF_SALES=.2
    VENDOR_SALES_CONTRIBUTION_PERCENTAGE=0.80
    VENDOR_TYPES = ['ZDOM', 'ZINT', 'ZSRV', 'ZCON'] # Domestic, International, Service, Consumable

    # MARA - Material Master
    MATERIAL_TYPES = ['ROH', 'HALB', 'FERT', 'HAWA']
    MATERIAL_GROUPS = {
        'Electronics': {'count': 0.25, 'price_range': (100, 10000),'Description':[
            'Integrated Circuits (ICs)',
            'Printed Circuit Boards (PCBs)',
            'Semiconductors',
            'Capacitors and Resistors',
            'Connectors and Cables'
        ]},
        'Office Supplies': {'count': 0.25, 'price_range': (1, 500),'Description':[
            'Pens and Pencils',
            'Notebooks and Paper',
            'Staplers and Staples',
            'Folders and Binders',
            'Printer Ink and Toner'
        ]},
        'Raw Materials': {'count': 0.25, 'price_range': (50, 5000),'Description':[
            'Steel and Aluminum',
            'Plastics (e.g., PET, PVC)',
            'Wood and Lumber',
            'Copper and Other Metals',
            'Chemicals and Solvents'
        ]},
        'Services': {'count': 0.25, 'price_range': (500, 50000),'Description':[
            'IT Support and Maintenance',
            'Consulting and Advisory',
            'Logistics and Shipping',
            'Cleaning and Janitorial',
            'Marketing and Advertising'
        ]}
    }
    UNITS_OF_MEASURE =  ['PC', 'KG', 'M', 'EA', 'L', 'CM', 'BOX']

    # Pricing Logic
    PRICE_VOLATILITY_PERCENTAGE = 0.15 # ±15%
    CONTRACT_PRICE_DISCOUNT_PERCENTAGE = (0.05, 0.15) # 5-15% lower for contracts
    PREFERRED_VENDOR_DISCOUNT_PERCENTAGE = (0.10, 0.15) # 10-15% better pricing

    # EKKO - Purchase Order Headers
    COMPANY_CODES = ['1000', '2000', '3000']
    PURCHASING_ORGANIZATIONS = ['P001', 'P002']
    PURCHASING_GROUPS = ['PG01', 'PG02', 'PG03']
    CURRENCIES = ['USD', 'EUR', 'GBP']
    CONTRACT_PO_PERCENTAGE = (0.60, 0.80) # 60-80% contract-based

    # EKPO - PO Line Items
    LINE_ITEMS_PER_PO_MEAN = 4 # Log-normal distribution mean
    LINE_ITEMS_PER_PO_MAX = 15
    PLANTS = ['PL01', 'PL02', 'PL03']

    # EKBE - PO History
    INVOICE_DAYS_AFTER_GR = (5, 30) # Invoice 5-30 days after Goods Receipt

    # Delivery Performance
    LATE_DELIVERY_PERCENTAGE = (0.20, 0.30) # 20-30% late
    DELAY_DISTRIBUTION = {
        '1-7_days': 0.70,
        '8-14_days': 0.20,
        '15-30_days': 0.10
    }
    VENDOR_PERFORMANCE_VARIATION = 0.20 # ±20% from average late rate

    # VENDOR_CONTRACTS - Custom Table
    CONTRACT_VALIDITY_YEARS = (1, 3)
    VOLUME_COMMITMENT_UNITS = (100, 10000)
    CONTRACT_COVERAGE_PERCENTAGE = (0.2, 0.50) # 40-50% material-vendor combinations
    CONTRACT_TYPES = ['BLANKET', 'SPOT', 'FRAMEWORK']
    EXPIRED_CONTRACT_PERCENTAGE = 0.10 # 10% of contracts are expired

    # Seasonal Patterns
    Q4_SPEND_INCREASE_PERCENTAGE = 0.30 # 30% more spending in Q4 vs Q1