Analytics Methodology
(sap_data_generator — Calculations, Formulas & Metrics)

This document explains the analytical logic used inside the SAP Data Generator and the accompanying Data Quality (DQ) Validation framework.
It covers:

Statistical distributions

Spend/Pareto calculations

Pricing formulas

Contract & preferred vendor discounts

Value calculations (NETPR, MENGE, NETWR)

Delivery analytics

Validation formulas & tolerances

DQ score calculations

1. Statistical Distributions

The generator supports: Pareto, Uniform, Normal, and Exponential distributions (as mentioned in project description).

1.1 Pareto Distribution (80/20 Logic)

Used for vendor spend distribution.

If:

VENDOR_PERCENTAGE_FOR_DISTRIBUTION_OF_SALES = p

VENDOR_SALES_CONTRIBUTION_PERCENTAGE = s

Then:

Top p% of vendors must contribute approximately s% of total spend.

Formula:

Spend_top_vendors  ≈  s%  of Total_Spend
Spend_other_vendors ≈ (1 − s)% of Total_Spend


For generating spend weights:

weight_i = 1 / (rank_i ** α)


Where:

rank_i = vendor rank in descending importance

α = shape parameter (between 1.1 and 2.0 for realistic skew)

Normalized:

normalized_weight_i = weight_i / Σ(weight_all)


These weights determine:

Number of POs generated per vendor

Total value of POs

Likelihood of being chosen for line items

2. Pricing Calculations

Each PO line item price is computed through multi-step transformations.

2.1 Base Unit Price

Random baseline price per material:

Base_Price(material) = Random(min_price, max_price)

2.2 Price Volatility

Applied to simulate real market price changes:

Price_after_volatility = Base_Price × (1 ± Volatility%)


Where:

Volatility% = PRICE_VOLATILITY_PERCENTAGE / 100

2.3 Contract Price Discount

If PO is a Contract PO:

Discount_contract = CONTRACT_PRICE_DISCOUNT_PERCENTAGE / 100
Price_contract = Price_after_volatility × (1 − Discount_contract)

2.4 Preferred Vendor Discount

If vendor ∈ preferred vendors list:

Discount_preferred = PREFERRED_VENDOR_DISCOUNT_PERCENTAGE / 100
Price_preferred   = Price_contract × (1 − Discount_preferred)

2.5 Final NETPR

Final price for the line item:

NETPR = Price_preferred


If vendor is neither contract nor preferred:

NETPR = Price_after_volatility

3. Quantity & Line Value Calculations
3.1 Quantity (MENGE)

Usually generated using Normal or Exponential distribution:

MENGE = RandomInteger(min_qty, max_qty)

3.2 Line Value (NETWR)
NETWR = NETPR × MENGE

3.3 Price Tolerance Validation

To allow small rounding differences:

abs( NETWR − (NETPR × MENGE) )  ≤ NETWR_TOLERANCE_PERCENT%


Where:

Tolerance_value = NETWR × (NETWR_TOLERANCE_PERCENT / 100)

4. PO Header & Line Item Analytics
4.1 Number of Line Items per PO

Configured via:

LINE_ITEMS_PER_PO_MEAN

LINE_ITEMS_PER_PO_MAX

Using a capped normal distribution:

LineItems = min( RandomNormal(mean), LINE_ITEMS_PER_PO_MAX )


Top vendors tend to generate more line items due to Pareto weights.

5. Contract Price Validation

To ensure contract logic is correct:

Difference% = abs(PO_Price − Contract_Price) / Contract_Price × 100


This must satisfy:

Difference% ≤ CONTRACT_PRICE_PO_PRICE_TOLERANCE_PERCENT

6. Delivery & Timeline Analytics
6.1 Delivery Delay Calculation

Based on:

LATE_DELIVERY_RATE_RANGE = [min%, max%]


For each PO line:

is_late = Random(0,1) < Random(min%, max%)  


If late:

Delivery_Date = Expected_Delivery_Date + RandomDelay(days)

6.2 GR/IR Matching Ratio

Goods receipt quantity (GR) and Invoice quantity (IR) must match within tolerance.

Ratio = GR_Quantity / IR_Quantity


Validation rule:

abs( Ratio − 1 ) ≤ GR_INVOICE_RATIO_TOLERANCE%

7. Spend Analytics

After generation:

Total_Spend = Σ(NETWR)
Spend_per_vendor[v] = Σ(NETWR where vendor == v)
Spend_Ratio_top_vendors = Σ(top vendors spend) / Total_Spend


Validation checks:

Spend_Ratio_top_vendors ≈ VENDOR_SALES_CONTRIBUTION_PERCENTAGE ± PARETO_SPEND_TOLERANCE_PERCENT

8. Data Quality Score (DQ Score)

The generator supports a DQ scoring mechanism after validations.

8.1 Rule-Level Pass/Fail

Each rule returns:

1 = pass
0 = fail

8.2 Rule Weighting

Each rule can have configurable “weight” (e.g., schema = high, business rules = medium).

Weighted_Score = Σ( Rule_Pass × Rule_Weight )
Max_Score      = Σ( Rule_Weight )

8.3 Final DQ Score
DQ_Score = (Weighted_Score / Max_Score) × 100


Typical expected score:

90%–100% for high-quality synthetic datasets.

9. Outlier & Statistical Validation

The validator checks:

9.1 Price Outlier Detection

Z-score:

z = (price − mean_price) / std_dev


Flag if:

|z| > Z_THRESHOLD   (typically 2 or 3)

9.2 Delivery Delay Distribution

Ensures:

actual_late_delivery_percentage ≈ configured_range

9.3 Quantity Outlier Checks

Using IQR:

IQR = Q3 − Q1
Lower_Bound = Q1 − 1.5 × IQR
Upper_Bound = Q3 + 1.5 × IQR


Quantities outside bounds are flagged.

10. Summary of Key Formulas Table
Area	Formula
Spend Pareto	Spend_top ≈ s%
Volatility	Price × (1 ± volatility%)
Contract Discount	Price × (1 − discount%)
Preferred Discount	Price × (1 − discount%)
Line Value	NETPR × MENGE
NETWR Tolerance	diff ≤ NETWR × (tol%)
Contract Price Tolerance	diff% ≤ CONTRACT_PRICE_PO_PRICE_TOLERANCE
GR/IR Ratio	abs(GR/IR − 1) ≤ tolerance
DQ Score	(weighted_pass / weighted_total) × 100
