# SAP Data Generator – README

## 📌 Overview

The **SAP Data Generator** is a modular Python-based framework that generates realistic synthetic SAP Procure-to-Pay (P2P) datasets. It is designed to simulate real-world business processes such as:

- Vendor master creation  
- Material master generation  
- Purchase order creation  
- Goods receipts  
- Invoice posting  

The framework is fully configurable—you can control the number of vendors, materials, PO volume, distributions, noise levels, and business rules using a single **config.json** file.

This tool is useful for:

- Demo datasets  
- Analytics use cases  
- Data engineering practice  
- Testing ETL pipelines  
- Process mining (Celonis, Power BI, etc.)

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
sap_data_generator/
│
├── config/
│   └── config.json
│
├── data/
│   └── (Generated output files)
│
├── src/
│   ├── vendors.py
│   ├── materials.py
│   ├── purchase_orders.py
│   ├── goods_receipt.py
│   ├── invoices.py
│   ├── utils.py
│   └── main.py
│
├── validation/
│   ├── validate_po.py
│   ├── validate_invoice.py
│   └── validate_relations.py
│
└── README.md
```

---

## ⚙️ How to Configure the Data Generation

All parameters are controlled via **config/config.json**.

### Sample Config

```json
{
    "vendors": {
        "count": 100,
        "pareto_distribution": true,
        "pareto_alpha": 1.5
    },
    "materials": {
        "count": 200
    },
    "purchase_orders": {
        "count": 5000,
        "max_line_items": 5
    },
    "delays": {
        "po_to_gr_days": [2, 10],
        "gr_to_invoice_days": [1, 5]
    }
}
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
python src/main.py
```

This generates:

- Vendors  
- Materials  
- POs & PO items  
- Goods Receipts  
- Invoices  

Outputs are stored in `/data/`.

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
data/
│ vendor_master.csv
│ material_master.csv
│ purchase_orders.csv
│ po_items.csv
│ goods_receipts.csv
│ invoices.csv
```

---

## 📣 Future Improvements

- Contract data  
- MRP simulation  
- Additional distributions  
- Noise injection to simulate SAP errors  
- GUI for config editing  

---
