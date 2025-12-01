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

```

### How to Customize the Output

| Requirement | Edit in config.json |
|------------|----------------------|
| Increase vendors | `"vendors": { "count": 500 }` |
| Add Pareto skew | `"pareto_distribution": true` |
| Increase PO volume | `"purchase_orders": { "count": 20000 }` |
| Add more line items | `"max_line_items": 10` |
| Adjust delays | Edit `"delays"` section |
| Change distribution | Add `"distribution": "exponential"` |

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
