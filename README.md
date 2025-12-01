# SAP Data Generator – README

## 📌 Overview

The **SAP Data Generator** is a modular Python-based framework that generates realistic synthetic SAP Procure-to-Pay (P2P) datasets. It is designed to simulate real-world business processes such as:

- Vendor master creation  
- Material master generation  
- Purchase order creation  
- Purchase order line item creation
- Purchase order Hisory creation
- Vendor contract 

The framework is fully configurable—parameters such as vendor count, material count, PO volume, distributions, and process rules can be edited through the Config class, allowing you to customize data generation without modifying the core logic.

This tool is useful for:

- Demo datasets  
- Analytics use cases  
- Data engineering practice  
- Testing ETL pipelines  
- Process mining 

---

## 🛠 Features

- Configurable data volume (vendors, materials, POs, etc.)  
- Supports statistical distributions (uniform, pareto, exponential etc.)  
- Generates linked transactions across tables  
- Realistic delays between PO → GR → Invoice  
- Lightweight and modular codebase  
- Validation scripts included to verify data quality  

---

## 📁 Project Structure

```
data_generator/
│

│
├── generated_sap_data/
│   └── (Generated output files)
│
├── src/
|    └── data_generator/
│       ├── SAPDataGenerator.py
│       ├── config.py
│       ├── utilities.py
|     └── data_quality/
│       ├── ValidationResult.py
│       ├── data_quality.py
│       ├── dq_config.py
│       └── utils.py.py
│

│
└── README.md
```

---

## ⚙️ How to Configure the Data Generation

All parameters are controlled via **config.py**.

### Sample Config

```
class Config:
    # General
    RANDOM_SEED = 42
    OUTPUT_DIR = "generated_sap_data"
    OUTPUT_FORMAT = "csv" # or "parquet"

    # Date Range
    START_DATE = datetime.date(2020, 1, 1)
    END_DATE = datetime.date(2024, 12, 31)

    # Record Counts
    NUM_VENDORS = 1000# Slightly more than 1000 to ensure 1000 valid ones
    NUM_MATERIALS = 5000 # Slightly more than 5000
    NUM_PO_HEADERS = 10000 # Slightly more than 10000
    NUM_PO_LINE_ITEMS_TARGET = 40000 # Target for EKPO
    NUM_PO_HISTORY_TARGET = 30000 # Target for EKBE
    NUM_CONTRACTS_TARGET = 2000 # Target for VENDOR_CONTRACTS

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

```

### How to Customize the Output

| Requirement | Edit in config.json |
|------------|----------------------|
| Increase vendors | `NUM_VENDORS=5000` |
| Increase contract price discount | `CONTRACT_PRICE_DISCOUNT_PERCENTAGE= (0.05,0.1)` |
| Increase PO volume | `NUM_PO_HEADERS=1200` |


After editing the config file, rerun the generator.

---

## ▶️ How to Run the Data Generator

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

Install required packages:

```bash
pip install -r requirements.txt
```

---

### 2. Run the Generator

```bash
python src/data_generator/SAPDataGenerator.py
```

This generates:

- Vendors  
- Materials  
- POs & PO items  
- PO history 
- Vendor Contract

Outputs are stored in `/generated_sap_data/`.

---

## ✔️ Running Validation Scripts
Data Quality Validation Framework

The Data Quality (DQ) Validation Framework is a modular, configurable engine designed to validate the integrity, structure, and business-rule correctness of the synthetic SAP datasets generated by the project. It provides a centralized way to define validation rules, run quality checks, and generate automated data quality reports.

This validation layer ensures that the generated dataset is:

Schema compliant

Referentially consistent

Business-rule accurate

Realistic for analytics / process mining use cases

📁 Module Structure
data_quality/
│
├── dq_config.json            # Configuration for schema, rules, thresholds, weights
├── schema_validation.py      # Column checks, datatype checks, null validations
├── relationship_validation.py# PK–FK and table linkage checks
├── rule_engine.py            # Business rule validations
├── dq_reporter.py            # Outputs JSON + HTML DQ report
└── run_validation.py         # Main entry point for DQ validation

⚙️ Configuration (dq_config.json)

All validation behavior is controlled through the dq_config.json file.
This allows you to update rules without modifying Python code.

✔️ You can configure:

Table schemas

Datatype expectations

Nullability rules

Primary & foreign key relationships

Cross-table dependencies

Threshold-based rules (e.g., quantity > 0)

Date & process rules (e.g., GR ≥ PO date)

Rule severity (Error/Warning)

Weightage for DQ Score calculation

Example dq_config snippet:
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

▶️ Running the Validation Pipeline

From the project root:

python data_generator/src/data_quality/run_validation.py


OR if you're inside the module folder:

python run_validation.py

📄 Validation Workflow

When executed, the pipeline performs:

1️⃣ Schema Validation

Column presence

Datatype matching

Nullability constraints

2️⃣ Relationship Validation

Primary key uniqueness

Foreign key matching

Table dependency checks

3️⃣ Business Rule Validation

Based on dq_config, e.g.:

GR date must be ≥ PO date

Invoice quantity must match GR quantity

Prices must be positive

4️⃣ Score Calculation

Each rule has a weight defined in dq_config.
A final DQ Score is computed using weighted rule outcomes.

📊 Output Files

After running, two outputs are generated:

1. JSON Report — dq_results.json

Contains:

Pass/fail per rule

Rule severity

Error counts

Table-level scores

The final overall DQ Score

Useful for automation or debugging.

2. HTML Dashboard — dq_report.html

A visual, interactive dashboard:

Overview of DQ performance

Error summaries

Rule-level results

DQ Score visualization

Drill-down per table

This file is ideal for demos and internal presentations.

✔️ Example Terminal Output
Schema validation: ✔ Passed with 2 warnings  
Relationship validation: ✔ Passed  
Business rules: ✖ 3 rules violated  
DQ Score: 86.7%

Generated:
 - dq_results.json
 - dq_report.html

📣 Extending the Validation Engine

You can easily add:

New rules by editing dq_config.json

New validation modules inside the data_quality folder

Additional visualizations in the HTML dashboard

The architecture is designed for extensibility.
### Validate Purchase Orders

```bash
python validation/validate_po.py
```

### Validate Invoices

```bash
python validation/validate_invoice.py
```

### Validate Cross-Table Relations

```bash
python validation/validate_relations.py
```

---

## 📌 Example Output Files

```
genrated_sap_datae/
│ LFA1.csv
│ MARA.csv
│ EKKO.csv
│ EKPO.csv
│ EKBE.csv
│ vendor_contracts.csv
```

---

## 📣 Future Improvements

- Contract data  
- MRP simulation  
- Additional distributions  
- Noise injection to simulate SAP errors  
- GUI for config editing  

---
