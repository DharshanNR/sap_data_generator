import datetime

class dq_config:
    # --- General Configuration ---
    DATA_DIR = "generated_sap_data" # Directory where generated data is stored
    REPORT_DIR = "dq_reports"
    REPORT_FILENAME_JSON = "dq_report.json"
    REPORT_FILENAME_HTML = "dq_dashboard.html"
    
    # --- Schema Definitions ---
    SCHEMA = {
        "LFA1": {
            "file": "LFA1.csv",
            "id_field": "LIFNR",
            "fields": {
                "LIFNR": {"type": str, "mandatory": True, "length": 8, "format": r"^V\d{7}$"},
                "NAME1": {"type": str, "mandatory": True, "length": (1, 35)},
                "LAND1": {"type": str, "mandatory": True, "length": 2},
                "KTOKK": {"type": str, "mandatory": True, "length": 4, "valid_values": ['ZDOM', 'ZINT', 'ZSRV', 'ZCON']},
                "ERDAT": {"type": datetime.date, "mandatory": True, "format": r"^\d{4}-\d{2}-\d{2}$"},
                "STRAS": {"type": str, "mandatory": True, "length": (1, 35)},
                "SMTP_ADDR": {"type": str, "mandatory": False,},
                "SPERR": {"type": str, "mandatory": False, "length": 1, "valid_values": [' ', 'X']},
                "IS_PREFERRED": {"type": bool, "mandatory": True} # Internal field, might not be in final CSV
            },
        },
         
        "MARA": {
            "file": "MARA.csv",
            "id_field": "MATNR",
            "fields": {
                "MATNR": {"type": str, "mandatory": True, "length": 8, "format": r"^M\d{7}$"},
                "MAKTX": {"type": str, "mandatory": True, "length": (1, 40)},
                "MTART": {"type": str, "mandatory": True, "length": (1,4), "valid_values": ['ROH', 'HALB', 'FERT', 'HAWA']},
                "MATKL": {"type": str, "mandatory": True, "length": (1, 16), "valid_values": ['Electronics', 'Office Supplies', 'Raw Materials', 'Services']},
                "MEINS": {"type": str, "mandatory": True, "length": (1, 3)},
                "ERSDA": {"type": datetime.date, "mandatory": True, "format": r"^\d{4}-\d{2}-\d{2}$"},
                "BRGEW": {"type": float, "mandatory": False, "min_value": 0},
                "NTGEW": {"type": float, "mandatory": False, "min_value": 0}
            }
        },
        "EKKO": {
            "file": "EKKO.csv",
            "id_field": "EBELN",
            "fields": {
                "EBELN": {"type": str, "mandatory": True, "length": 12, "format": r"^PO\d{10}$"},
                "BUKRS": {"type": int, "mandatory": True, "length": (1,6)},
                "BSART": {"type": str, "mandatory": True, "length": 2, "valid_values": ['NB', 'FO']},
                "AEDAT": {"type": datetime.date, "mandatory": True, "format": r"^\d{4}-\d{2}-\d{2}$"},
                "LIFNR": {"type": str, "mandatory": True, "length": 8, "format": r"^V\d{7}$"},
                "WAERS": {"type": str, "mandatory": True, "length": 3, "valid_values": ['USD', 'EUR', 'GBP']}, # Add more ISO codes if needed
                "EKORG": {"type": str, "mandatory": True, "length": 4},
                "EKGRP": {"type": str, "mandatory": True, "length": 4},
                "BEDAT": {"type": datetime.date, "mandatory": True, "format": r"^\d{4}-\d{2}-\d{2}$"}
            }
        },
        "EKPO": {
            "file": "EKPO.csv",
            "id_field": ["EBELN", "EBELP"],
            "fields": {
                "EBELN": {"type": str, "mandatory": True, "length": 12, "format": r"^PO\d{10}$"},
                "EBELP": {"type": str, "mandatory": True, "length": (1,8)},
                "MATNR": {"type": str, "mandatory": True, "length": 8, "format": r"^M\d{7}$"},
                "MENGE": {"type": float, "mandatory": True, "min_value": 0},
                "MEINS": {"type": str, "mandatory": True, "length": (1, 3)},
                "NETPR": {"type": float, "mandatory": True, "min_value": 0},
                "NETWR": {"type": float, "mandatory": True, "min_value": 0},
                "EINDT": {"type": datetime.date, "mandatory": True, "format": r"^\d{4}-\d{2}-\d{2}$"},
                "WERKS": {"type": str, "mandatory": True, "length": 4},
                "MATKL": {"type": str, "mandatory": True, "length": (1, 20), "valid_values": ['Electronics', 'Office Supplies', 'Raw Materials', 'Services']}
            }
        },
        "EKBE": {
            "file": "EKBE.csv",
            "id_field": ["EBELN", "EBELP", "BELNR"], # BELNR to uniquely identify history record
            "fields": {
                "EBELN": {"type": str, "mandatory": True, "length": 12, "format": r"^PO\d{10}$"},
                "EBELP": {"type": str, "mandatory": True, "length": 7, "format": r"^LI\d{5}$"},
                "BEWTP": {"type": str, "mandatory": True, "length": 1, "valid_values": ['E', 'Q']},
                "BUDAT": {"type": datetime.date, "mandatory": True, "format": r"^\d{4}-\d{2}-\d{2}$"},
                "MENGE": {"type": float, "mandatory": True, "min_value": 0},
                "DMBTR": {"type": float, "mandatory": True, "min_value": 0},
                "BELNR": {"type": str, "mandatory": True, "length": (1,10)}, #"format": r"^(GR|INV)\d{8}$"},
                "ACTUAL_DELIVERY_DATE": {"type":datetime.date , "mandatory": False} #datetime.date `format": r"^\d{4}-\d{2}-\d{2}$"
            }
        },
        "VENDOR_CONTRACTS": {
            "file": "vendor_contract.csv",
            "id_field": "CONTRACT_ID",
            "fields": {
                "CONTRACT_ID": {"type": str, "mandatory": True, "length": 6, "format": r"^C\d{5}$"},
                "LIFNR": {"type": str, "mandatory": True, "length": 8, "format": r"^V\d{7}$"},
                "MATNR": {"type": str, "mandatory": True, "length": 8, "format": r"^M\d{7}$"},
                "CONTRACT_PRICE": {"type": float, "mandatory": True, "min_value": 0},
                "VALID_FROM": {"type": datetime.date, "mandatory": True, "format": r"^\d{4}-\d{2}-\d{2}$"},
                "VALID_TO": {"type": datetime.date, "mandatory": True, "format": r"^\d{4}-\d{2}-\d{2}$"},
                "VOLUME_COMMITMENT": {"type": int, "mandatory": True, "min_value": 0},
                "CONTRACT_TYPE": {"type": str, "mandatory": True, "valid_values": ['BLANKET', 'SPOT', 'FRAMEWORK']}
            }
        }
        }
       
    

    # --- Validation Thresholds & Parameters ---
    # Business Logic
    NETWR_TOLERANCE_PERCENT = 0.01 # 1% tolerance for NETWR = NETPR * MENGE
    CONTRACT_PRICE_PO_PRICE_TOLERANCE_PERCENT = 0.05 # 5% tolerance for contract PO prices
    INVOICE_GR_AMOUNT_TOLERANCE_PERCENT = 0.02 # 2% tolerance for invoice vs GR amounts
    BLOCKED_VENDOR_PO_DAYS = 90 # No POs for blocked vendors in last X days

    # Statistical Validation
    OUTLIER_STD_DEV_THRESHOLD = 3 # Price outliers beyond 3 standard deviations
    PARETO_SPEND_TOLERANCE_PERCENT = 0.10 # +/- 10% for Pareto check
    CONTRACT_COMPLIANCE_RATE_RANGE = (0.60, 0.80) # 60-80%
    LATE_DELIVERY_RATE_RANGE = (0.20, 0.30) # 20-30%
    GR_INVOICE_RATIO_TOLERANCE = 0.10 # 10% tolerance for 1:1 ratio (e.g., 0.9 to 1.1)

    # Completeness Checks
    MAX_MATERIAL_GROUP_PERCENTAGE = 0.40 # No category has >40% of materials
    DATA_DATE_RANGE = (datetime.date(2020, 1, 1), datetime.date(2024, 12, 31))

    # --- Severity Levels ---
    SEVERITY = {
        "CRITICAL": "Critical",
        "WARNING": "Warning",
        "INFO": "Info"
    }

    # --- Weights for Overall DQ Score ---
    # Adjust these weights based on importance of each category
    DQ_SCORE_WEIGHTS = {
        "schema_validation": 0.30,
        "referential_integrity": 0.30,
        "business_logic_validation": 0.25,
        "statistical_validation": 0.10,
        "completeness_checks": 0.05
    }