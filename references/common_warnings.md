# Common Warnings by Expression Type

This is a library of expert warnings. Every warning must be **specific and actionable** — explain what breaks and why, not just that something might go wrong. Tailor each warning to the actual field names in the expression.

---

## FIXED LOD Warnings

### Context Filters (most common source of "wrong totals")
- **The problem**: FIXED LODs compute before dimension filters. If [Region] is on the Filters shelf as a regular filter, a FIXED LOD on [Sales] will return totals across ALL regions, not just the visible ones. Percentages won't add up to 100%.
- **The fix**: Right-click the filter → Add to Context. Context filters run before LOD computation.
- **When to always flag**: Any FIXED LOD on a dashboard where users will filter by a dimension that's not in the FIXED declaration.

### Data Source Filters vs Dimension Filters
- Data source filters DO apply to FIXED LODs (they restrict the data before Tableau even sees it).
- Dimension filters do NOT apply unless promoted to context.
- This asymmetry is the #1 source of "why is my number wrong?" bugs in production.

### Empty FIXED (table-scoped) and filters
- `{FIXED : SUM([Sales])}` computes grand total. If a user filters to Region = "East", this still returns the grand total for ALL regions.
- Almost always needs a context filter when used in "% of total" calculations.

### NULL dimensions in FIXED declaration
- `{FIXED [Customer ID] : MIN([Order Date])}` — if [Customer ID] is NULL for some rows, those rows form their own "null customer" group. This is rarely the intended behavior. Add an ISNULL check or filter NULLs at the data source.

### Aggregation mismatch
- The expression inside a FIXED LOD must be an aggregate: `{FIXED [Customer ID] : SUM([Sales])}` ✅
- `{FIXED [Customer ID] : [Sales]}` ❌ — this is invalid syntax and will error.
- When the result is used in a view, it must be wrapped in another aggregate: `AVG({FIXED [Customer ID] : SUM([Sales])})`.

### Performance on live connections
- FIXED LODs generate a subquery in the SQL sent to the database. On large tables with live connections, each LOD = one extra query. Three LODs in a viz = 3 extra queries per render.
- On extracts, this is computed once at extract time and cached. Live connections pay this cost on every load.

---

## LOD INCLUDE Warnings

### Must be wrapped in an aggregate in the view
- `{INCLUDE [Customer ID] : SUM([Sales])}` returns a value for every (view_dim, Customer_ID) combination. In a viz showing only [Region], Tableau needs to know how to collapse those — use `AVG(...)`, `SUM(...)`, etc.
- `AVG({INCLUDE [Customer ID] : SUM([Sales])})` = average total sales per customer, shown by region. ✅
- Forgetting the outer aggregate produces a "cannot mix aggregate and non-aggregate" error.

### INCLUDE respects dimension filters (unlike FIXED)
- This is usually a feature, but can be surprising: if you filter out a customer segment, INCLUDE LODs recalculate without those customers. FIXED would not.
- If you need an "absolute" denominator that ignores filters, use FIXED instead.

### The included dimension doesn't need to be in the view — but it must be in the data
- You can INCLUDE [Customer ID] even if it's not on any shelf, and it will compute at that grain before aggregating to the view level.

---

## LOD EXCLUDE Warnings

### Excluded dimension must be in the view
- If you EXCLUDE a dimension that isn't in the view, Tableau treats it as FIXED. The expression won't error, but it silently returns a different result than intended.
- Always check: is the excluded dim actually on Rows/Columns/Detail/Color?

### EXCLUDE with multiple dimensions
- `{EXCLUDE [Sub-Category] : SUM([Sales])}` when the view has [Category] and [Sub-Category] → computes at Category grain. ✅
- `{EXCLUDE [Category], [Sub-Category] : SUM([Sales])}` → computes at table grain (like empty FIXED). May be what you want for a benchmark, may not be.

### Filter behavior mirrors INCLUDE
- EXCLUDE LODs compute after dimension filters (unlike FIXED). Same filter behavior caveats as INCLUDE apply.

---

## Table Calculation Warnings

### Addressing and Partitioning must be explicit
- The default addressing in Tableau is often "Table (Across)" or "Table (Down)" depending on the viz type. This is almost never what you want on a real dashboard.
- Always specify: "In Edit Table Calculation, set Addressing to [Order Date] and Partitioning to [Region]" — otherwise the calc restarts at unpredictable boundaries.

### WINDOW functions restart at partition boundaries
- `WINDOW_AVG(SUM([Sales]), -2, 0)` computes a 3-period rolling average. If [Region] is a partition, the average resets at each region's first row. If the first two rows of a new region have fewer than 3 prior rows, the average is computed on fewer values — this is not an error, but it's easy to misread.
- Warn when the user asks for "rolling N-period" and their data has natural partitions.

### Table calcs can't be used in Filters shelf directly
- You cannot drop a table calc onto Filters and expect it to work correctly. Tableau evaluates table calcs after aggregation, so filtering on them changes the data visible to the table calc — circular dependency.
- Workaround: use FIXED LOD to pre-compute the value, then filter on that.

### Sort order is part of the calculation
- For RUNNING_SUM, LOOKUP(-1), and any ordered table calc, the result depends entirely on sort order. If the view is sorted by Sales descending, RUNNING_SUM accumulates in descending order — not chronological.
- Always specify: "Ensure [Order Date] is sorted ascending in the view, or the running total will not be chronological."

### LOOKUP and NULL boundaries
- `LOOKUP(SUM([Sales]), -1)` returns NULL at the first row of each partition (no prior row). Wrap with `ZN()` if zeros are preferable to NULLs in charts, but only if null really means zero in context.

### RANK ties
- `RANK(SUM([Sales]))` uses competition ranking by default (1, 1, 3 for ties). Use `RANK_DENSE()` for (1, 1, 2) or `RANK_UNIQUE()` for (1, 2, 3) with arbitrary tie-breaking.
- Always flag which tie-breaking behavior was chosen.

### TOTAL vs WINDOW_SUM
- `TOTAL(SUM([Sales]))` = sum of all marks in the partition. `WINDOW_SUM(SUM([Sales]))` = same, but WINDOW_SUM accepts offset parameters for partial windows. Use TOTAL for "sum of everything visible."

---

## Date Function Warnings

### DATETRUNC returns a DATE, not a label
- `DATETRUNC('month', [Order Date])` returns `2024-10-01` for any October 2024 date — a full date value. This is correct for time series axes (Tableau can format it as "Oct 2024").
- Don't use DATETRUNC as a grouping key and expect clean month names — use DATENAME or DATEPART for labels.

### DATEDIFF direction matters
- `DATEDIFF('day', [Order Date], [Ship Date])` = positive if ship date is after order date.
- `DATEDIFF('day', [Ship Date], [Order Date])` = positive if order date is after ship date (almost certainly negative in practice — a bug).
- Always write it as `DATEDIFF('unit', start, end)` and verify which is start.

### Fiscal year vs calendar year
- `DATEPART('year', [Order Date])` uses Tableau's fiscal year start setting if fiscal year is configured for the data source. If the organization uses an April fiscal year start, year groupings will not match calendar year groupings.
- On dashboards for finance/retail/SaaS domains, always flag: "Verify the data source fiscal year setting in Tableau Desktop (Data → [Source Name] → Date Properties) matches your organization's fiscal year."

### NULL dates propagate
- Any date arithmetic on a NULL date returns NULL. `DATEDIFF('day', NULL, [Ship Date])` = NULL.
- If [Order Date] can be NULL (e.g., draft orders), wrap with: `IF NOT ISNULL([Order Date]) THEN DATEDIFF(...) END`

### TODAY() vs NOW()
- `TODAY()` returns today's date with no time component. `NOW()` returns the current datetime.
- For date comparisons (`[Order Date] >= TODAY() - 30`), use TODAY(). For datetime fields, use NOW().
- Mixing DATE and DATETIME fields in comparisons causes type errors — cast with `DATETRUNC('day', [datetime_field])` to normalize.

### Year-over-year comparisons and incomplete current periods
- `DATEPART('year', [Order Date]) = DATEPART('year', TODAY())` includes all of the current year TO DATE. If you're comparing full-year prior vs partial current year, YoY will always look negative late in the year.
- Always flag: "This comparison includes the partial current year. If you want full-year-over-full-year, filter to completed periods."

---

## Conditional / Boolean Warnings

### IIF vs IF NULL behavior
- `IIF([Profit] > 0, 'Positive', 'Negative')` — if [Profit] is NULL, IIF returns the "unknown" third value (NULL by default), not either branch. This is different from IF/THEN.
- `IF [Profit] > 0 THEN 'Positive' ELSE 'Negative' END` — NULL [Profit] falls into ELSE and returns 'Negative'. This is almost always the wrong behavior for NULLs.
- Use `IIF(ISNULL([Profit]), 'Unknown', IIF([Profit] > 0, 'Positive', 'Negative'))` for explicit NULL handling.

### CASE is not a row-level filter
- `CASE [Status] WHEN 'Active' THEN [Revenue] END` returns NULL for non-Active rows. SUM of this = sum of Active revenue only — which may be exactly what you want, but easy to misread as "all revenue."

### ZN() vs ISNULL() + 0
- `ZN([Sales])` is shorthand for `IIF(ISNULL([Sales]), 0, [Sales])` — converts NULL to 0.
- Only use ZN when NULL genuinely means zero in the business context. NULL often means "no data recorded" — replacing with 0 can misrepresent averages and counts.

---

## Basic Aggregate Warnings

### COUNT vs COUNTD
- `COUNT([Order ID])` counts rows (including duplicates). `COUNTD([Order ID])` counts distinct values.
- On a viz with multiple rows per order (e.g., one row per line item), COUNT([Order ID]) = number of line items, not number of orders. Almost always use COUNTD for "number of orders/customers/sessions."

### AVG on pre-aggregated data
- If your data source has one row per customer with a "Total Spend" field (already aggregated at the customer level), `AVG([Total Spend])` = average of those totals. This is correct.
- If you have row-level transactions and want average order value, you need `SUM([Sales]) / COUNTD([Order ID])` — `AVG([Sales])` gives average line item value, not average order value.

### SUM vs AGG on calculated fields
- If a calculated field itself contains an aggregate (e.g., `SUM([Sales]) / SUM([Quantity])`), Tableau marks it as an aggregate — you cannot wrap it in SUM() again.
- Row-level calculated fields (no aggregates inside) can be aggregated normally.
