Business Logic — sap_data_generator
Purpose of Business Logic

The goal of sap_data_generator’s business logic is to simulate realistic procurement-process data for SAP Procure-to-Pay (P2P) workflows: vendors, materials, purchase orders (POs), contracts, delivery history, and associated pricing. This enables creation of synthetic yet realistic datasets suitable for analytics, ETL testing, process mining, or demo data. 
GitHub

The business logic implements rules around:

how spend / purchase volume is distributed among vendors (e.g. via Pareto)

how pricing is assigned to materials / purchase orders, considering volatility, discounts for preferred or contract vendors

how delivery (goods receipt / invoice / PO → GR → invoice) is simulated, including delays / history

Below are the key sub-domains of logic: Pareto (spend distribution), Pricing, Delivery / Order history / Timing.

Core Configurable Parameters

In config.py, the following (among others) influence business logic. 
GitHub

VENDOR_PERCENTAGE_FOR_DISTRIBUTION_OF_SALES: fraction of vendors that will cover majority of spend. 
GitHub

VENDOR_SALES_CONTRIBUTION_PERCENTAGE: the target portion of overall spend volume attributed to those “top” vendors. 
GitHub

Statistical distribution flags: the generator supports "statistical distributions (uniform, pareto, exponential, etc.)" for different volumes/assignments. 
GitHub

Pricing-related:

PRICE_VOLATILITY_PERCENTAGE — base volatility in material/unit prices. 
GitHub

CONTRACT_PRICE_DISCOUNT_PERCENTAGE — discount range to apply when purchase is under a vendor contract. 
GitHub

PREFERRED_VENDOR_DISCOUNT_PERCENTAGE — discount range for "preferred" vendors. 
GitHub

Purchase order composition:

LINE_ITEMS_PER_PO_MEAN, LINE_ITEMS_PER_PO_MAX — average and maximum number of line items per PO. 
GitHub

Validation / tolerance thresholds for data quality and business-logic validation. For example:

NETWR_TOLERANCE_PERCENT: tolerance for total line-item value vs (unit price × quantity) calculation. 
GitHub

CONTRACT_PRICE_PO_PRICE_TOLERANCE_PERCENT: tolerance for price deviations when using contract prices. 
GitHub

LATE_DELIVERY_RATE_RANGE: configured acceptable range (e.g. 20-30%) for simulating late deliveries. 
GitHub

These parameters allow controlling how “realistic” or skewed the synthetic data is (e.g. more concentrated spend, more volatility, more late deliveries, etc.)

Pareto / Spend Distribution Logic

The repo claims to support “statistical distributions (uniform, pareto, exponential, etc.)” for volumes. 
GitHub

What “Pareto” means here

A Pareto (or power-law / heavy-tail) distribution imitates the “80/20 rule” often seen in vendor spend: a small fraction of vendors contribute the majority of spend volume.

The config parameters allow specifying what fraction of vendors will cover most spend:

VENDOR_PERCENTAGE_FOR_DISTRIBUTION_OF_SALES: proportion of vendors considered “top vendors”.

VENDOR_SALES_CONTRIBUTION_PERCENTAGE: fraction of total spend allocated to these “top vendors.”

Expected Behavior

Vendor Selection for Top Spend — randomly select a subset of vendors, sized as per VENDOR_PERCENTAGE_FOR_DISTRIBUTION_OF_SALES.

Assign Spend Share — allocate a large portion of spend (equal to VENDOR_SALES_CONTRIBUTION_PERCENTAGE) to this subset; remaining spend is distributed among other vendors.

Generate POs Accordingly — number of POs, PO line-items, quantities, and prices for “top vendors” will accordingly be higher, to reflect their higher spend share.

Statistical Distribution Use — when creating data (e.g. number of POs per vendor, line items per PO, perhaps spend per PO), use the configured heavy-tail / Pareto or other distributions to simulate realistic skew.

Note: Because code is modular and config-driven, the actual distribution (Pareto vs uniform vs exponential) might be selectable/configurable — though I did not find an explicit “distribution_type = pareto” flag in config. Given README mentions Pareto, likely there is logic selecting that distribution under the hood. 
GitHub

Pricing Logic

The synthetic dataset aims to reflect realistic material and contract pricing behavior. Key aspects:

Base price volatility: Materials are assigned base prices, but with volatility controlled by PRICE_VOLATILITY_PERCENTAGE — meaning the unit price can fluctuate by ± that percentage around a baseline. This simulates realistic variation in pricing over time or per PO. 
GitHub

Contract discounts: If a PO is created under a vendor contract, the price for materials may get a discount. The discount percentage range is from CONTRACT_PRICE_DISCOUNT_PERCENTAGE. 
GitHub

Preferred-vendor discount: Vendors marked as “preferred” may offer extra discount, per PREFERRED_VENDOR_DISCOUNT_PERCENTAGE. This reflects real-world vendor preferential pricing. 
GitHub

PO Price vs Contract price tolerance: The validation rules define a tolerance (CONTRACT_PRICE_PO_PRICE_TOLERANCE_PERCENT) to allow small deviations between contract price and PO price. This accounts for realistic small variances (e.g. rounding, currency conversion, minor price renegotiations). 
GitHub

Net value calculation & validation: For each PO line item, the generated NETPR (unit price) and MENGE (quantity) yield NETWR (line value). There is a tolerance (NETWR_TOLERANCE_PERCENT) to allow small deviations when validating NETWR ≈ NETPR × MENGE. 
GitHub

Expected Behavior Flow

When a material/vendor combination is chosen for a PO, baseline unit price is determined (perhaps derive from material master, or random baseline).

Apply volatility: adjust price by ± PRICE_VOLATILITY_PERCENTAGE.

Determine if PO uses a contract price (based on percentage of POs flagged as contract POs — config has CONTRACT_PO_PERCENTAGE). If yes, apply contract-discount. 
GitHub

If vendor is marked “preferred”, apply additional discount per PREFERRED_VENDOR_DISCOUNT_PERCENTAGE.

Compute final unit price (NETPR) and then compute line value (NETWR = NETPR × MENGE).

Validate price logic if data quality validation is run — ensure price deviations and net-value calculations are within configured tolerances.

This approach allows modeling realistic variability in pricing, contracts, vendor preferences — which helps generate more realistic procurement data.

Delivery / Purchase Order / History Simulation Logic

One of the advertised features: “Simulates realistic delays (PO → GR → Invoice)” in purchase lifecycle. 
GitHub

Key aspects:

The generator creates: PO headers (e.g. table EKKO), PO line items (EKPO), and PO history (likely EKBE for goods receipts / invoice history), plus vendor contracts. 
GitHub

Config includes tolerances/parameters for delivery-related simulation and subsequent validation: For example:

LATE_DELIVERY_RATE_RANGE: defines a range (e.g. 20–30%) of deliveries (or POs) that should be simulated as late. 
GitHub

GR_INVOICE_RATIO_TOLERANCE: tolerance for matching goods receipt vs invoice amounts/quantities (e.g. expecting ~1:1 ratio, allowing ± 10%). 
GitHub

Expected Behavior Flow

For each PO and PO line item, after generation, decide (based on configured late-delivery rate) whether the delivery will be on-time or late.

Generate one or more history records in the “PO history” (goods receipt / invoice) table (EKBE), with appropriate BELNR, BUDAT (posting date), MENGE, DMBTR (amount), and if late, adjust the BUDAT to a date later than expected.

For invoice vs GR validation: ensure that quantities and amounts line up — e.g. delivered quantity ≈ invoiced quantity — with tolerance defined by GR_INVOICE_RATIO_TOLERANCE.

This gives realistic temporal behavior: not every PO is delivered immediately; some are delayed; invoices correspond to goods receipts, but with possible small discrepancies.

Data-Quality / Validation Logic (Business-Logic Validation)

Although not strictly “business logic for data generation,” the repo includes a validation framework to check if generated data meets expectations. 
GitHub

Key validations relevant to business logic:

Schema & Referential Integrity — ensures all tables and relationships (e.g. foreign keys) are correct. 
GitHub

Business-rule validation — e.g. that invoice quantity matches GR quantity; that delivery dates make sense (GR date ≥ PO date), etc. 
GitHub

Statistical validation / Pareto check — the config includes PARETO_SPEND_TOLERANCE_PERCENT: after generation, the system can check whether the actual top-vendor spend share is within ± tolerance of the configured target. 
GitHub

Price / value tolerances — e.g. that NETWR ≈ NETPR × MENGE within tolerance, contract-prices vs PO-prices within tolerance, etc. 
GitHub

This ensures that synthetic data is not just random, but follows the business constraints and realistic distribution targets — helpful for analytics or process-mining workloads where unrealistic anomalies can cause misleading results.

Assumptions / Gaps / What Is Not Explicit

Because the repository lacks a formal spec or design document, some aspects must be assumed or inferred:

There is no explicit flag in config.py like DISTRIBUTION_TYPE = "pareto". The README mentions “statistical distributions (uniform, pareto, exponential, etc.)” — so likely the code chooses distribution(s) internally based on context or default, but it's not explicit which distribution is used for which attribute (e.g. frequency of POs per vendor, spend per vendor, delays, etc.). That means results may vary depending on internal defaults. 
GitHub

How baseline material prices / contract prices are determined is not fully documented. It’s possible that the code picks random baseline price values per material, then applies volatility/discounts — but the exact baseline logic needs to be inspected in code (e.g. in utilities.py or SAPDataGenerator.py).

Delivery scheduling: while there is a concept of late delivery rate, I did not see a configurable “standard lead time” or “expected delivery delay distribution”. So “late vs on-time” likely is binary or random per PO based on rate. For more realistic simulation (with variable lead times, partial deliveries, split deliveries), code would need enhancement.

No support (in config) for more advanced business-logic such as: vendor capacity limits, material inventory, reorder frequency, dynamic pricing over time, or supply-chain constraints. The generator is primarily focused on generating standalone synthetic snapshots — not a full simulation of supply-chain dynamics.
