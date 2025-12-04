# Analytics Methodology
*(sap_data_generator — Calculations, Formulas & Metrics)*

This document explains the analytical logic used inside the SAP Data Generator and the accompanying Data Quality (DQ) Validation framework.

It covers:
- Statistical distributions
- Spend / Pareto calculations
- Pricing formulas
- Contract & preferred vendor discounts
- Value calculations (NETPR, MENGE, NETWR)
- Delivery analytics
- Validation formulas & tolerances
- DQ score calculations

## Table of contents
- [1. Statistical Distributions](#1-statistical-distributions)
  - [1.1 Pareto Distribution (80/20 Logic)](#11-pareto-distribution-8020-logic)
- [2. Pricing Calculations](#2-pricing-calculations)
  - [2.1 Base Unit Price](#21-base-unit-price)
  - [2.2 Price Volatility](#22-price-volatility)
  - [2.3 Contract Price Discount](#23-contract-price-discount)
  - [2.4 Preferred Vendor Discount](#24-preferred-vendor-discount)
  - [2.5 Final NETPR](#25-final-netpr)
- [3. Quantity & Line Value Calculations](#3-quantity--line-value-calculations)
  - [3.1 Quantity (MENGE)](#31-quantity-menge)
  - [3.2 Line Value (NETWR)](#32-line-value-netwr)
  - [3.3 Price Tolerance Validation](#33-price-tolerance-validation)
- [4. PO Header & Line Item Analytics](#4-po-header--line-item-analytics)
- [5. Contract Price Validation](#5-contract-price-validation)
- [6. Delivery & Timeline Analytics](#6-delivery--timeline-analytics)
  - [6.1 Delivery Delay Calculation](#61-delivery-delay-calculation)
  - [6.2 GR/IR Matching Ratio](#62-grir-matching-ratio)
- [7. Spend Analytics](#7-spend-analytics)
- [8. Data Quality Score (DQ Score)](#8-data-quality-score-dq-score)
  - [8.1 Rule-Level Pass/Fail](#81-rule-level-passfail)
  - [8.2 Rule Weighting](#82-rule-weighting)
  - [8.3 Final DQ Score](#83-final-dq-score)
- [9. Outlier & Statistical Validation](#9-outlier--statistical-validation)
  - [9.1 Price Outlier Detection](#91-price-outlier-detection)
  - [9.2 Delivery Delay Distribution](#92-delivery-delay-distribution)
  - [9.3 Quantity Outlier Checks](#93-quantity-outlier-checks)
- [10. Summary of Key Formulas Table](#10-summary-of-key-formulas-table)

---

## 1. Statistical Distributions

The generator supports Pareto, Uniform, Normal, and Exponential distributions (as mentioned in project description).

### 1.1 Pareto Distribution (80/20 Logic)

Used

