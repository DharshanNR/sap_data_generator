# sap_data_generator

**sap_data_generator** is a Python-based framework to programmatically generate realistic SAP (or ERP-like) synthetic data sets representing business processes.  
It is designed to support simulation of enterprise workflows (orders, invoices, procure-to-pay cycles, etc.) with configurable distributions, noise, and statistical properties — useful for testing, demos, or data-driven analytics platforms.

## 🔎 Project Overview

### Why this exists  
- In enterprise software evaluations, demos, or stress testing — real production data is often unavailable or sensitive.  
- This tool enables generation of realistic but synthetic data that mimics real-world business processes and metrics.  
- Enables generating data at scale (transactions, orders, line-items, invoices, etc.), with statistical realism (variations, noise, distributions).

### Key Features  
- Generate synthetic datasets representing business processes (e.g. order-to-cash, procure-to-pay)  
- Configurable parameters for volume, distributions, noise, date ranges, numeric ranges, etc.  
- Modular and extensible architecture — easily adapt or extend to new tables / entities / processes  
- Export data in common formats (CSV, JSON, or format compatible with SAP/ERP ingestion)  
- Can serve for demo setups, testing flows, data pipelines, or analytics validation  

## 🚀 Getting Started

### Prerequisites  
- Python 3.8+ (or appropriate version)  
- Virtual environment recommended  

### Installation  

```bash
git clone https://github.com/DharshanNR/sap_data_generator.git
cd sap_data_generator
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
