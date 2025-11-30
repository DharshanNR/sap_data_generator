# SAP Data Generator  
A highly extensible, configurable, and realistic **synthetic SAP/ERP business process data generator** designed for creating end-to-end datasets used in demos, analytics testing, ETL pipelines, and process mining simulations.

This framework allows you to simulate real-world business processes such as **Order-to-Cash (O2C)**, **Procure-to-Pay (P2P)**, and other enterprise workflows using controlled randomness, distributions, and business rules — producing **data that looks indistinguishable from real SAP tables**.

---

# 🚀 Overview

Enterprise systems like SAP require large volumes of realistic data for:

- Demo environments  
- Validation of ETL/data pipelines  
- Testing analytics dashboards (PowerBI/Tableau)  
- Process mining (Celonis, SAP Signavio)  
- Performance testing  
- Synthetic dataset creation where sensitive customer data can’t be used  

However, real ERP datasets are often **sensitive, inconsistent, or unavailable**.  
This tool fills that gap by generating realistic SAP-like datasets with full parent–child relationships, noise, and configurable business behavior.

---

# 🎯 Key Features

### ✔ **Modular architecture**
Each SAP table or entity is generated using an isolated, reusable module.

### ✔ **Config-driven generation**
Simply change parameters in a JSON/YAML config to alter:
- Volume of records  
- Distributions (normal, pareto, exponential…)  
- Noise levels  
- Date windows  
- Amount ranges  
- Relationships (1:N, N:N)

### ✔ **Realistic enterprise process simulation**
Supports linking:
- Vendors → Purchase Orders → Line Items → Invoices → Payments  
- Customers → Sales Orders → Deliveries → Billing documents  
- Material master + pricing + company codes  

### ✔ **Statistical simulation**
Add realistic variation using:
- Gaussian noise  
- Pareto distribution (80/20 spending)  
- Random rework rates  
- Delays based on exponential distribution  

### ✔ **Export-friendly**
Generated data can be exported to:
- CSV
- Parquet
- JSON

### ✔ **Built for extensibility**
Add new entities, relationships, or business rules with minimal code changes.

---

