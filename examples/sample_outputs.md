# Sample Outputs — Calibration Examples

These five examples demonstrate the expected output format and quality level for deLOD. Use these to calibrate response depth, warning specificity, and teaching quality.

---

## Example 1: LOD FIXED — % of Total

**User question:** "Show each region's sales as a % of total sales"

**Schema:** [Region] (String), [Sales] (Number), [Order Date] (Date)

```json
{
  "expression_type": "LOD FIXED",
  "field_name": "Region % of Total Sales",
  "primary_expression": "SUM([Sales]) / SUM({FIXED : SUM([Sales])})",
  "alternative_expression": "SUM([Sales]) / TOTAL(SUM([Sales]))",
  "alternative_tradeoff": "TOTAL() always reflects visible filtered data; use it when you want '% of what's shown' and FIXED when you want '% of everything regardless of filters'.",
  "explanation": "The numerator SUM([Sales]) aggregates at the view level — one value per Region on the shelf. The denominator uses a table-scoped FIXED LOD (empty dimension declaration) to compute total [Sales] across the entire dataset, independent of the view. Dividing gives each region's share of the whole.",
  "performance_notes": "Table-scoped FIXED LODs generate a single subquery against the data source. On large tables with a live connection this runs once per render. On an extract it's computed at extract time and cached — no render-time cost.",
  "edge_case_warnings": [
    "If [Region] is on the Filters shelf as a regular filter, the denominator still reflects ALL regions — your percentages will sum to less than 100% of the visible data. Right-click [Region] on Filters → Add to Context to fix this.",
    "Format the result field as Percentage in Tableau (right-click the field → Format → Numbers → Percentage) or it displays as a decimal like 0.342.",
    "If [Sales] contains NULLs, those rows are silently dropped from the numerator. If NULLs should count as zero, wrap with ZN(): SUM(ZN([Sales])) / SUM({FIXED : SUM(ZN([Sales]))})."
  ],
  "complexity_rating": "Simple",
  "teach_me": "FIXED LOD expressions compute before dimension filters run — this is the single most common source of 'my percentages don't add up to 100%' bugs in Tableau."
}
```

---

## Example 2: LOD INCLUDE — Average at a Finer Grain

**User question:** "What's the average order value per customer, shown by region?"

**Schema:** [Customer ID] (String), [Order ID] (String), [Region] (String), [Sales] (Number)

```json
{
  "expression_type": "LOD INCLUDE",
  "field_name": "Avg Order Value per Customer",
  "primary_expression": "AVG({INCLUDE [Customer ID] : SUM([Sales])})",
  "alternative_expression": "SUM([Sales]) / COUNTD([Customer ID])",
  "alternative_tradeoff": "The alternative gives revenue per customer at the view grain but doesn't account for order-level variation — use INCLUDE when you want the true average of each customer's total, not a blended aggregate.",
  "explanation": "The INCLUDE LOD computes total [Sales] per [Customer ID], even though the view is at Region level. AVG() then averages those customer-level totals across the region. This gives the average total spend per customer for each region — not average line item value.",
  "performance_notes": "INCLUDE LODs respect dimension filters (unlike FIXED), so this calc updates correctly when users filter by Region or other dimensions. It generates a subquery on live connections — on large customer tables consider an extract.",
  "edge_case_warnings": [
    "The outer aggregate AVG() is required — omitting it produces a 'Cannot mix aggregate and non-aggregate' error because the INCLUDE returns one value per Customer per Region, and Tableau needs to know how to collapse those to the Region level.",
    "If one customer placed orders in multiple regions, their total [Sales] is attributed to each region they appear in — they'll be counted in every applicable region's average, not split proportionally.",
    "INCLUDE LODs respect dimension filters, so if a user filters to Region = 'East', only East customers contribute to the average. This is usually correct behavior — flag it if the requirement is 'company-wide average regardless of filters'."
  ],
  "complexity_rating": "Moderate",
  "teach_me": "INCLUDE LODs let you compute at a finer grain than the view and then reaggregate — always wrap them in an outer aggregate (AVG, SUM, MAX) or Tableau will throw an aggregation error."
}
```

---

## Example 3: Table Calculation — Rolling Average

**User question:** "Rolling 3-month average of sales by region"

**Schema:** [Region] (String), [Order Date] (Date), [Sales] (Number)

```json
{
  "expression_type": "Table Calculation",
  "field_name": "3-Month Rolling Avg Sales",
  "primary_expression": "WINDOW_AVG(SUM([Sales]), -2, 0)",
  "alternative_expression": "(SUM([Sales]) + LOOKUP(SUM([Sales]), -1) + LOOKUP(SUM([Sales]), -2)) / 3",
  "alternative_tradeoff": "LOOKUP-based alternative makes each component visible for debugging but fails when any prior period is NULL (start of data) — WINDOW_AVG handles partial windows at boundaries more gracefully.",
  "explanation": "WINDOW_AVG computes the average of SUM([Sales]) across a window from 2 rows back to the current row (3 values total). The window moves forward one row at a time as Tableau evaluates each mark. The result at each month is the average of that month and the two prior months.",
  "performance_notes": "Table calculations run on data already fetched into the view — they're fast regardless of data source size. However, they're blind to filtered-out data: if a user filters out January, the February rolling average only has one prior month available.",
  "edge_case_warnings": [
    "In Edit Table Calculation, set Addressing to [Order Date] and Partitioning to [Region]. If Region is in the Addressing direction, the average will span across regions — almost certainly wrong.",
    "WINDOW_AVG at the start of each partition (first 1–2 months per region) has fewer than 3 values available. Tableau averages whatever is available — the first month shows 1-month avg, second shows 2-month avg. This is not an error but can look odd. Add a label or annotation to the chart.",
    "If [Order Date] sort order in the view is descending (newest first), the rolling average runs backwards — most recent month averages the next two future months. Ensure the view is sorted ascending by [Order Date].",
    "Table calcs cannot be placed on the Filters shelf to exclude marks — filtering changes what data is in the view, which changes what the table calc sees. Use FIXED LOD if you need to filter on an aggregated value."
  ],
  "complexity_rating": "Moderate",
  "teach_me": "Table calculations operate on the data already rendered in the view — they're fast, but filtering changes their result because filtered rows are no longer available to the calculation window."
}
```

---

## Example 4: Date Function — Year-over-Year Comparison

**User question:** "Show revenue this year vs same period last year"

**Schema:** [Order Date] (Date), [Sales] (Number), [Region] (String)

```json
{
  "expression_type": "Table Calculation",
  "field_name": "YoY Revenue Growth %",
  "primary_expression": "(SUM([Sales]) - LOOKUP(SUM([Sales]), -1)) / ABS(LOOKUP(SUM([Sales]), -1))",
  "alternative_expression": "SUM(IF YEAR([Order Date]) = YEAR(TODAY()) THEN [Sales] END) / SUM(IF YEAR([Order Date]) = YEAR(TODAY()) - 1 THEN [Sales] END) - 1",
  "alternative_tradeoff": "The alternative is a standalone calculated field with no table calc dependencies — easier to use in filters and LODs — but requires both years to be in the data and doesn't work on a time series axis.",
  "explanation": "LOOKUP(-1) references the value one row back in the Addressing direction. When [Order Date] is on the axis with yearly granularity, each row is one year — so LOOKUP(-1) is the prior year. The formula divides the change by the absolute prior year value, returning a signed growth percentage.",
  "performance_notes": null,
  "edge_case_warnings": [
    "Set Addressing to [Order Date] in Edit Table Calculation. If Region is in the Addressing direction, LOOKUP(-1) returns the prior region's value, not the prior year — completely wrong result.",
    "The first year in the view returns NULL (no prior year to look up). Wrap the whole expression in ZN() if you want 0% instead of NULL for the first year: ZN((SUM([Sales]) - LOOKUP(SUM([Sales]), -1)) / ABS(LOOKUP(SUM([Sales]), -1)))",
    "This comparison includes the partial current year. If today is June, the current year has 6 months of data vs last year's full 12. YoY will look negative for annual comparisons. If you want same-period-last-year, filter both years to the same month range.",
    "If prior year [Sales] is 0 or NULL, ABS(LOOKUP(SUM([Sales]), -1)) returns 0 and the formula divides by zero — returns NULL. Handle with: IF LOOKUP(SUM([Sales]), -1) = 0 THEN NULL ELSE ... END"
  ],
  "complexity_rating": "Moderate",
  "teach_me": "LOOKUP() references other marks in the view by relative position — always specify Addressing explicitly, because the default direction is often wrong and produces silently incorrect results."
}
```

---

## Example 5: Chained LOD Pattern — Customer Cohort

**User question:** "Assign each customer to their first purchase month so I can track cohorts"

**Schema:** [Customer ID] (String), [Order Date] (Date), [Sales] (Number)

```json
{
  "expression_type": "LOD FIXED",
  "field_name": "Cohort Month",
  "primary_expression": "DATETRUNC('month', {FIXED [Customer ID] : MIN([Order Date])})",
  "alternative_expression": null,
  "alternative_tradeoff": null,
  "explanation": "The inner FIXED LOD computes the earliest [Order Date] for each [Customer ID] across the entire dataset — this is the customer's first purchase date, independent of any view filters. DATETRUNC('month') then snaps that date to the first day of the month, giving a clean cohort label. Place this dimension on the view to group customers by when they first bought.",
  "performance_notes": "This FIXED LOD runs as a subquery once per render on live connections. On large customer tables it's efficient — the MIN aggregation is database-native. On an extract, computed at extract time.",
  "edge_case_warnings": [
    "This is a chained expression. Use [Cohort Month] as a dimension on your view (Rows/Columns/Color). It will not work as a measure.",
    "DATETRUNC returns a DATE value — '2024-01-01' for any January 2024 first purchase. Tableau will display it based on your date format settings. If you want 'Jan 2024' as a label, use DATENAME('month', ...) + ' ' + STR(YEAR(...)) instead.",
    "If a customer has orders in multiple years and you filter to a single year, the FIXED LOD still returns their true first purchase date (which may be in a prior year). This is correct cohort behavior — flag it if the team expects cohort assignment to reset with filters.",
    "Customers with NULL [Customer ID] will all be grouped into a single 'null cohort' — their minimum order date becomes one cohort. Filter NULLs at the data source if this isn't the intended behavior."
  ],
  "complexity_rating": "Moderate",
  "teach_me": "Cohort assignment should almost always be a FIXED LOD — it needs to return the same value for a customer regardless of what's on the view, which is exactly what FIXED is designed for."
}
```
