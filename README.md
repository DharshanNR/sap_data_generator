# SAP Data Generator – README

---

## 📌 Overview

The **SAP Data Generator** is a modular Python-based framework for generating realistic synthetic SAP Procure-to-Pay (P2P) datasets. It simulates business processes including:

--🔹Vendor master creation
--🔹 Material master generation
🔹 Purchase order creation
🔹 Purchase order line item creation
🔹 Purchase order history creation
🔹 Vendor contract creation

## 🛠 Features

🔹 Modular Python-based framework for SAP synthetic data generation
A structured Python project to generate realistic SAP Procure-to-Pay (P2P) data. 
GitHub

🔹 Configurable dataset size and distributions
Users can adjust parameters such as number of vendors, materials, purchase orders, and statistical distributions (e.g., uniform, Pareto, exponential). 
GitHub

🔹 Realistic business process simulation
Simulates end-to-end processes including vendor master, material master, purchase order creation, line items, history, and vendor contracts. 
GitHub

🔹 Lightweight and easily extensible architecture
Written with modular code to simplify extension and customization. 
GitHub

🔹 Config file driven customization
All major parameters (date range, record counts, pricing logic, plant codes, etc.) are controlled via a central Config class. 
GitHub

🔹 Business-oriented data quality validation framework
Includes scripts to validate dataset integrity, schema compliance, referential consistency, and business rule correctness. 
GitHub

🔹 Automated data quality reporting
Generates reports (JSON/HTML) detailing validation results, helping ensure generated data meets expected quality standards. 
GitHub

🔹 Ideal for demo, analytics & testing
Useful for building demo datasets, data engineering pipelines, ETL testing, analytics, and process mining exercises

---

**Configurable:** Parameters (vendor count, material count, PO volume, distributions, process rules) are set via the `Config` class, so you can tailor data generation to your use case.

**Typical uses:**

- Demo datasets
- Analytics use cases
- Data engineering practice
- Testing ETL pipelines
- Process mining

---



## 📁 Project Structure

```text
data_generator/
├── generated_sap_data/
│   └── (Generated output files)
├── src/
│   └── data_generator/
│       ├── SAPDataGenerator.py
│       ├── config.py
│       ├── utilities.py
│       └── data_quality/
│           ├── ValidationResult.py
│           ├── data_quality.py
│           ├── dq_config.py
│           └── utils.py
└── README.md
```

---

## ⚙️ Configuration (via `config.py`)

All data generation parameters live in `config.py`. Example:

```python
class Config:
    # General
    RANDOM_SEED = 42
    OUTPUT_DIR = "generated_sap_data"
    OUTPUT_FORMAT = "csv"  # or "parquet"

    # Date Range
    START_DATE = datetime.date(2020, 1, 1)
    END_DATE = datetime.date(2024, 12, 31)

    # Record Counts
    NUM_VENDORS = 1000
    NUM_MATERIALS = 5000
    NUM_PO_HEADERS = 10000
    NUM_PO_LINE_ITEMS_TARGET = 40000
    NUM_PO_HISTORY_TARGET = 30000
    NUM_CONTRACTS_TARGET = 2000

    # Vendor Master (LFA1)
    VENDOR_BLOCKED_PERCENTAGE = 0.05       # 5% blocked
    VENDOR_PREFERRED_PERCENTAGE = 0.10     # 10% preferred
    VENDOR_PERCENTAGE_FOR_DISTRIBUTION_OF_SALES = 0.2
    VENDOR_SALES_CONTRIBUTION_PERCENTAGE = 0.80
    VENDOR_TYPES = ['ZDOM', 'ZINT', 'ZSRV', 'ZCON']

    # Material Master (MARA)
    MATERIAL_TYPES = ['ROH', 'HALB', 'FERT', 'HAWA']
    MATERIAL_GROUPS = {...}  # See full source
    UNITS_OF_MEASURE = ['PC', 'KG', 'M', 'EA', 'L', 'CM', 'BOX']

    # Pricing Logic
    PRICE_VOLATILITY_PERCENTAGE = 0.15
    CONTRACT_PRICE_DISCOUNT_PERCENTAGE = (0.05, 0.15)
    PREFERRED_VENDOR_DISCOUNT_PERCENTAGE = (0.10, 0.15)

    # PO Headers (EKKO)
    COMPANY_CODES = ['1000', '2000', '3000']
    PURCHASING_ORGANIZATIONS = ['P001', 'P002']
    PURCHASING_GROUPS = ['PG01', 'PG02', 'PG03']
    CURRENCIES = ['USD', 'EUR', 'GBP']
    CONTRACT_PO_PERCENTAGE = (0.60, 0.80)

    # PO Line Items (EKPO)
    LINE_ITEMS_PER_PO_MEAN = 4
    LINE_ITEMS_PER_PO_MAX = 15
    PLANTS = ['PL01', 'PL02', 'PL03']
```

### Customize the Output

| Requirement                  | Change in `config.py`                          |
|------------------------------|-----------------------------------------------|
| Increase vendors             | `NUM_VENDORS = 5000`                          |
| Raise contract price discount| `CONTRACT_PRICE_DISCOUNT_PERCENTAGE = (0.05, 0.1)` |
| Increase PO volume           | `NUM_PO_HEADERS = 12000`                      |

After editing `config.py`, rerun the generator.

---

## ▶️ How to Run the Data Generator

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate    # Mac/Linux
venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

### 2. Run the Generator

```bash
python src/data_generator/SAPDataGenerator.py
```

**Generated:**

- Vendors
- Materials
- POs & PO items
- PO history
- Vendor Contracts

Outputs are saved to: `/generated_sap_data/`

---

## 🧪 Data Quality Validation Framework

The **Data Quality (DQ) Validation Framework** checks the integrity, structure, and business-rule correctness of the synthetic SAP datasets. It offers:

- **Centralized rule definition**
- **Automated quality reports**
- **Configurable validation behavior**

---

### ✨ Key Validation Areas

- **Schema compliance:** Column names, types, nullability
- **Referential consistency:** Primary & foreign keys
- **Business-rule logic:** Domain-specific checks
- **Realism:** Fit for analytics/process mining

---

### ⚙️ Configure (`dq_config.py`)

Validation is configured in `dq_config.py`. You can set:

- Table schemas: required columns and types
- Relationships: key dependencies
- Rules: threshold and domain checks
- Severity/weight: each rule’s impact on the overall DQ score

**Example:**

```
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
                "ACTUAL_DELIVERY_DATE": {"type":str , "mandatory": False, "format": r"^\d{4}-\d{2}-\d{2}$"} #datetime.date
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
```

---

## 📄 Validation Workflow

Main entry point: `data_quality.py`

**Pipeline steps:**

1. **Schema Validation**
   - Column presence
   - Datatypes
   - Nullability
2. **Relationship Validation**
   - Primary key uniqueness
   - Foreign key matching
   - Dependency checks
3. **Business Rule Validation**
   - Rules from `dq_config.json` (e.g., "GR date ≥ PO date", "Invoice qty matches GR qty")
4. **Score Calculation**
   - Weighted DQ Score from rule results

---

### Example Terminal Output

```
Schema validation: Passed with 2 warnings
Relationship validation: Passed
Business rules: 3 rules violated
DQ Score: 86.7%
```

**Generated:**
- `dq_results.json`: Per-rule results, severity, error counts, scores, overall DQ Score (automation/debugging)
- `dq_report.html`: Interactive dashboard (overview, summaries, rule drill-down, visualization)

**Extending Validation:**

- Add/edit rules in `dq_config.py`
- Add validation modules to `data_quality/`
- Enhance visualizations in `dq_report.html`
- Flexible architecture for new requirements

---
