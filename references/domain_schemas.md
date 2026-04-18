# Domain Schemas Reference

Use these when the user hasn't provided their own schema and wants a "typical" starting point, or when you need to make assumptions about field names and types.

---

## Retail / E-Commerce

**Grain**: One row per order line item (one product per order per row)

| Field | Type | Notes |
|---|---|---|
| [Order ID] | String | Order-level key — COUNTD for # orders |
| [Customer ID] | String | Customer-level key |
| [Order Date] | Date | When order was placed |
| [Ship Date] | Date | When order shipped — DATEDIFF from Order Date = fulfillment time |
| [Region] | String | Geographic hierarchy top level |
| [State] | String | Geographic hierarchy mid level |
| [City] | String | Geographic hierarchy leaf |
| [Category] | String | Product hierarchy top level (e.g., Furniture, Technology) |
| [Sub-Category] | String | Product hierarchy leaf (e.g., Chairs, Phones) |
| [Product Name] | String | SKU-level identifier |
| [Sales] | Number | Revenue for this line item |
| [Profit] | Number | Can be negative — always check for NULLs |
| [Quantity] | Number | Units in this line item |
| [Discount] | Number | 0.0–1.0 decimal — discount rate applied |

**Common calculations for this domain:**
- Revenue per order: `SUM([Sales]) / COUNTD([Order ID])`
- Profit margin: `SUM([Profit]) / SUM([Sales])`
- First purchase date per customer: `{FIXED [Customer ID] : MIN([Order Date])}`
- Repeat customer flag: `{FIXED [Customer ID] : COUNTD([Order ID])} > 1`
- Discount impact: `SUM([Sales] * [Discount])` = revenue given away

---

## SaaS / Subscription

**Grain**: Typically one row per account per month (MRR snapshot) or one row per event

| Field | Type | Notes |
|---|---|---|
| [Account ID] | String | Account-level key |
| [User ID] | String | User-level key — finer grain than account |
| [Subscription Start] | Date | When the account became a paying customer |
| [Subscription End] | Date | NULL if still active |
| [Churn Date] | Date | NULL if not churned — use ISNULL([Churn Date]) for active flag |
| [Plan Tier] | String | e.g., Free, Starter, Pro, Enterprise |
| [MRR] | Number | Monthly Recurring Revenue for this account |
| [ARR] | Number | Annual Recurring Revenue — often MRR * 12 |
| [Sessions] | Number | Product usage proxy |
| [Active Flag] | Boolean | TRUE = currently subscribed |

**Common calculations for this domain:**
- Customer lifetime (months): `DATEDIFF('month', [Subscription Start], IFNULL([Subscription End], TODAY()))`
- Churned in period: `NOT ISNULL([Churn Date]) AND DATETRUNC('month', [Churn Date]) = DATETRUNC('month', TODAY())`
- Net Revenue Retention: requires cohort FIXED LODs — complex, always ask to clarify
- MRR growth MoM: Table Calculation — `(SUM([MRR]) - LOOKUP(SUM([MRR]), -1)) / ABS(LOOKUP(SUM([MRR]), -1))`
- Health score bucketing: CASE or IF on usage metrics

---

## Supply Chain / Operations

**Grain**: One row per purchase order or per delivery event

| Field | Type | Notes |
|---|---|---|
| [Supplier ID] | String | Supplier-level key |
| [PO Date] | Date | Purchase order creation date |
| [Delivery Date] | Date | Actual delivery — can be NULL if not yet delivered |
| [Product ID] | String | Product SKU |
| [Units Ordered] | Number | |
| [Units Received] | Number | Can differ from ordered — fill rate = received/ordered |
| [Lead Time Days] | Number | Sometimes derived: DATEDIFF('day', [PO Date], [Delivery Date]) |
| [Unit Cost] | Number | Cost per unit |
| [Carbon Emissions] | Number | ESG metric — kg CO2 equivalent |
| [Region] | String | Origin or destination region |

**Common calculations for this domain:**
- Fill rate: `SUM([Units Received]) / SUM([Units Ordered])`
- On-time delivery flag: `[Delivery Date] <= DATEADD('day', [Expected Lead Days], [PO Date])`
- Average lead time by supplier: `{INCLUDE [Supplier ID] : AVG([Lead Time Days])}`
- Total spend: `SUM([Units Ordered] * [Unit Cost])`
- Carbon per unit: `SUM([Carbon Emissions]) / SUM([Units Received])`

---

## Finance / FP&A

**Grain**: One row per GL transaction, or one row per account per period

| Field | Type | Notes |
|---|---|---|
| [Account Code] | String | GL account identifier |
| [Account Name] | String | Human-readable account label |
| [Cost Center] | String | Organizational unit |
| [Department] | String | Higher-level org grouping |
| [Transaction Date] | Date | Posting date |
| [Fiscal Period] | String | e.g., "FY2024-Q3" — often pre-computed |
| [Fiscal Year] | Number | e.g., 2024 |
| [Fiscal Quarter] | Number | 1–4 |
| [Amount] | Number | Positive = debit, negative = credit (or vice versa — confirm convention) |
| [Budget Amount] | Number | Planned amount for this period |
| [Actuals Amount] | Number | What actually happened |

**Common calculations for this domain:**
- Budget variance: `SUM([Actuals Amount]) - SUM([Budget Amount])`
- Budget variance %: `(SUM([Actuals Amount]) - SUM([Budget Amount])) / ABS(SUM([Budget Amount]))`
- YTD actuals: filter by fiscal year + RUNNING_SUM — or use FIXED with fiscal period
- Prior period comparison: `LOOKUP(SUM([Actuals Amount]), -1)`
- Expense as % of revenue: requires two rows types in same data or a data blend

**Critical for finance domain**: Always flag fiscal year setting. Finance teams almost never use calendar year. Ask which month the fiscal year starts before writing any date-based calculation.

---

## Marketing / Digital Analytics

**Grain**: One row per session, per click, or per campaign-date combination

| Field | Type | Notes |
|---|---|---|
| [Session ID] | String | Web session identifier |
| [User ID] | String | Visitor — may be anonymous (NULL) before login |
| [Campaign ID] | String | Paid campaign identifier |
| [Campaign Name] | String | Human-readable |
| [Channel] | String | e.g., Paid Search, Organic, Email, Direct |
| [Date] | Date | Event/session date |
| [Impressions] | Number | Ad impressions |
| [Clicks] | Number | Ad clicks |
| [Spend] | Number | Ad spend in currency |
| [Sessions] | Number | Website sessions |
| [Conversions] | Number | Goal completions |
| [Revenue] | Number | Attributed revenue — attribution model matters |

**Common calculations for this domain:**
- CTR: `SUM([Clicks]) / SUM([Impressions])`
- CPC: `SUM([Spend]) / SUM([Clicks])` — guard against divide by zero: `IIF(SUM([Clicks]) = 0, NULL, SUM([Spend]) / SUM([Clicks]))`
- ROAS (Return on Ad Spend): `SUM([Revenue]) / SUM([Spend])`
- Conversion Rate: `SUM([Conversions]) / SUM([Sessions])`
- Cost per Conversion: `SUM([Spend]) / SUM([Conversions])` — same NULL guard
- Channel mix %: `SUM([Spend]) / {FIXED : SUM([Spend])}` — note context filter warning

**Critical for marketing domain**: Attribution model is almost never in Tableau — it's baked into the data source. Flag that any revenue metric reflects whatever attribution model the source system uses (last-click, first-click, linear, etc.).
