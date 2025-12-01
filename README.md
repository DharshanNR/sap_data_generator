# SAP Data Generator – README

---

## 📌 Overview

The **SAP Data Generator** is a modular Python-based framework for generating realistic synthetic SAP Procure-to-Pay (P2P) datasets. It simulates business processes including:

- Vendor master creation
- Material master generation
- Purchase order creation
- Purchase order line item creation
- Purchase order history creation
- Vendor contract creation

**Configurable:** Parameters (vendor count, material count, PO volume, distributions, process rules) are set via the `Config` class, so you can tailor data generation to your use case.

**Typical uses:**

- Demo datasets
- Analytics use cases
- Data engineering practice
- Testing ETL pipelines
- Process mining

---

## 🛠 Features

- Flexible data volume (vendors, materials, POs, etc.)
- Supports statistical distributions (uniform, pareto, exponential, etc.)
- Generates linked transactions across tables
- Simulates realistic delays (PO → GR → Invoice)
- Lightweight, modular codebase
- Built-in data quality validation scripts

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

### ⚙️ Configure (`dq_config.json`)

Validation is configured in `dq_config.json`. You can set:

- Table schemas: required columns and types
- Relationships: key dependencies
- Rules: threshold and domain checks
- Severity/weight: each rule’s impact on the overall DQ score

**Example:**

```json
{
  "schema": {
    "purchase_orders": {
      "required_columns": ["PO_ID", "VENDOR_ID", "PO_DATE"],
      "types": {
        "PO_ID": "string",
        "PO_DATE": "date"
      }
    }
  },
  "relationships": {
    "po_items": {
      "foreign_key": "PO_ID",
      "references": "purchase_orders"
    }
  },
  "rules": {
    "validate_po_dates": {
      "description": "PO Date must be before GR Date",
      "weight": 0.10
    }
  }
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

- Add/edit rules in `dq_config.json`
- Add validation modules to `data_quality/`
- Enhance visualizations in `dq_report.html`
- Flexible architecture for new requirements

---
