# Sample Outputs

Five complete worked examples. Use these to calibrate tone, specificity, and structure.

---

## Example 1: % of Total (LOD FIXED)

**User input**: "Show each category's sales as a % of total sales. Schema: [Category] (String), [Sales] (Number), [Order Date] (Date), [Region] (String)."

```json
{
  "expression_type": "LOD FIXED",
  "field_name": "Category % of Total Sales",
  "primary_expression": "SUM([Sales])\n/\nSUM({FIXED : SUM([Sales])})",
  "alternative_expression": "SUM([Sales]) / TOTAL(SUM([Sales]))",
  "alternative_tradeoff": "TOTAL() is a table calculation that respects visible filters — use it when you want '% of what the user can see'; use the FIXED version when you want '% of the absolute total regardless of filters'.",
  "explanation": "The numerator SUM([Sales]) aggregates at the view grain — whatever dimension is on the shelf. The denominator uses an empty FIXED LOD (no dimension declaration) to compute the table-scoped grand total, independent of any dimensions in the view. Dividing gives each category's share of the whole.",
  "performance_notes": "An empty FIXED LOD runs as a single subquery against the data source and is generally fast. On a live connection with a very large table, the subquery adds one extra round-trip per render — consider pre-computing this in a data source calculated field.",
  "edge_case_warnings": [
    "If [Region] is on the Filters shelf as a regular dimension filter, the FIXED denominator still includes ALL regions — your percentages will sum to less than 100% of the visible data. Promote the Region filter to Context (right-click → Add to Context) to fix this.",
    "Format the field as Percentage in Tableau (right-click field → Format → Numbers → Percentage) — it stores as a decimal and will display as 0.23 without formatting.",
    "If [Sales] contains NULLs, SUM([Sales]) silently ignores those rows. If NULLs should count as zero revenue, wrap with ZN(): SUM(ZN([Sales])) / SUM({FIXED : SUM(ZN([Sales]))})."
  ],
  "complexity_rating": "Simple",
  "teach_me": "FIXED LOD expressions compute before dimension filters run — that's why they ignore the Filters shelf unless you promote filters to Context, and it's the single most common cause of 'my percentages don't add up to 100%' bugs."
}
```

---

## Example 2: Rolling 3-Month Average (Table Calculation)

**User input**: "Rolling 3-month average of sales by region. Schema: [Region] (String), [Sales] (Number), [Order Date] (Date)."

```json
{
  "expression_type": "Table Calculation",
  "field_name": "Rolling 3-Month Avg Sales",
  "primary_expression": "WINDOW_AVG(\n  SUM([Sales]),\n  -2,\n  0\n)",
  "alternative_expression": "(LOOKUP(SUM([Sales]), 0) + LOOKUP(SUM([Sales]), -1) + LOOKUP(SUM([Sales]), -2)) / 3",
  "alternative_tradeoff": "The LOOKUP version makes the averaging logic explicit and lets you handle NULLs on the first two periods differently, but WINDOW_AVG is cleaner and handles variable window sizes more gracefully.",
  "explanation": "WINDOW_AVG averages SUM([Sales]) across a window of 3 marks: the current mark (0) and the 2 prior marks (-2 to 0). Tableau evaluates this after aggregating to the view level, so it operates on whatever grain [Order Date] is truncated to on the shelf — typically month.",
  "performance_notes": "Table calculations run entirely in Tableau's local cache (post-query). They add no database load, making WINDOW_AVG fast even on large datasets. The trade-off is they can only see data already in the view — they cannot look at filtered-out months.",
  "edge_case_warnings": [
    "Open Edit Table Calculation and set Addressing to [Order Date] (Specific Dimensions) and Partitioning to [Region]. If Addressing is left as 'Table (Across)', the window will span across regions at month boundaries — the rolling average for January East will include December West.",
    "The first two months of each region's series will have fewer than 3 data points — WINDOW_AVG computes on however many are available (1 or 2), not NULL. If you want the first two months to show NULL instead, use: IIF(INDEX() < 3, NULL, WINDOW_AVG(SUM([Sales]), -2, 0)).",
    "Ensure [Order Date] is sorted ascending in the view (Sort → Field → [Order Date] → Ascending). If sorted by Sales, the rolling average becomes meaningless.",
    "This calculation cannot be placed on the Filters shelf. If you need to filter by this average, pre-compute it as a FIXED LOD instead."
  ],
  "complexity_rating": "Moderate",
  "teach_me": "Table calculations operate on marks already in the view — they're fast and filter-aware, but they're blind to data the user has filtered out, which makes them wrong for any 'absolute' benchmark that should ignore the current filter context."
}
```

---

## Example 3: Average Order Value per Customer by Region (LOD INCLUDE)

**User input**: "I want to show average order value per customer, but my viz only has region on it. Schema: [Customer ID] (String), [Order ID] (String), [Region] (String), [Sales] (Number)."

```json
{
  "expression_type": "LOD INCLUDE",
  "field_name": "Avg Order Value per Customer",
  "primary_expression": "AVG(\n  {INCLUDE [Customer ID] : SUM([Sales])}\n)",
  "alternative_expression": "AVG(\n  {INCLUDE [Order ID] : SUM([Sales])}\n)",
  "alternative_tradeoff": "Including [Order ID] gives average per-order value (every order weighted equally); including [Customer ID] gives average total-spend per customer (each customer weighted equally regardless of how many orders they placed). Choose based on whether you want order-level or customer-level averaging.",
  "explanation": "The INCLUDE LOD computes SUM([Sales]) at the [Customer ID] grain — total spend per customer — before aggregating to the view level. The outer AVG() then averages those customer totals across the [Region] currently on the shelf. Without INCLUDE, AVG([Sales]) would give average line-item value, not average customer spend.",
  "performance_notes": "INCLUDE LODs respect dimension filters (unlike FIXED), so they recalculate when users filter by segment or date — this is usually the correct behavior. On large datasets with many distinct Customer IDs, the subquery can be expensive on live connections.",
  "edge_case_warnings": [
    "The outer aggregate is required: you cannot place {INCLUDE [Customer ID] : SUM([Sales])} directly in the view as a measure — Tableau needs AVG(), SUM(), MIN(), or MAX() to know how to collapse customer-level values to region level.",
    "If a customer appears in multiple regions (e.g., they placed orders in East and West), they will be counted in both regions' averages. If customers belong to exactly one region, this is not an issue.",
    "This calculation respects dimension filters. If the user filters to Region = 'East', the average reflects only East customers. If you want a fixed benchmark that ignores region filters, use FIXED instead of INCLUDE."
  ],
  "complexity_rating": "Moderate",
  "teach_me": "INCLUDE LOD is the right tool when you need to compute at a finer grain than your view — it pulls in a lower-level dimension just for the calculation, then lets the outer aggregate collapse it back to the view grain."
}
```

---

## Example 4: Year-over-Year Revenue Growth (Date Function + Table Calculation)

**User input**: "YoY revenue growth % by month. Schema: [Order Date] (Date), [Sales] (Number), [Category] (String)."

```json
{
  "expression_type": "Table Calculation",
  "field_name": "YoY Revenue Growth %",
  "primary_expression": "(SUM([Sales]) - LOOKUP(SUM([Sales]), -12))\n/\nABS(LOOKUP(SUM([Sales]), -12))",
  "alternative_expression": "SUM([Sales]) / LOOKUP(SUM([Sales]), -12) - 1",
  "alternative_tradeoff": "The division-minus-one form is more compact but returns NULL (not a negative percentage) when the prior period was zero — the explicit subtraction form makes the logic clearer and handles edge cases more visibly.",
  "explanation": "LOOKUP([Sales], -12) navigates 12 marks prior in the table — i.e., the same month last year — when the view is set to monthly grain. The numerator is the absolute change; dividing by the absolute value of the prior period handles cases where prior-year revenue was negative (e.g., net refunds).",
  "performance_notes": "This is a table calculation: fast, no extra database query. However, it requires 12 months of prior data to exist in the view. If the viz only shows the current year, LOOKUP(-12) returns NULL everywhere.",
  "edge_case_warnings": [
    "In Edit Table Calculation, set Addressing to [Order Date] (Month) with Specific Dimensions. If [Category] is in the view and left in the addressing, the -12 offset navigates 12 categories instead of 12 months.",
    "Ensure [Order Date] is shown at Month grain on the shelf (DATETRUNC or the built-in date hierarchy at Month level). At Day grain, -12 means 12 days ago, not 12 months.",
    "The first 12 months of the time series will show NULL — there's no prior-year data to compare against. Consider using ISNULL() to label those marks as 'No prior year data' rather than leaving them blank.",
    "If the current year is incomplete (e.g., you're in April), the YoY comparison for May–December will show NULL, which is correct behavior — but can look like missing data to end users. Add an annotation or a reference line to explain."
  ],
  "complexity_rating": "Moderate",
  "teach_me": "LOOKUP() is the most flexible table calculation for time-intelligence — it navigates N marks in any direction, making it the right tool for any 'same period last year' or 'N periods ago' comparison, as long as your sort order and addressing are set correctly."
}
```

---

## Example 5: Customer Cohort First Purchase Month (LOD FIXED, Chained)

**User input**: "I want to bucket customers by the month they first purchased, then see how their total spend grows over time. Schema: [Customer ID] (String), [Order ID] (String), [Order Date] (Date), [Sales] (Number)."

```json
{
  "expression_type": "LOD FIXED",
  "field_name": "First Purchase Month",
  "primary_expression": "DATETRUNC(\n  'month',\n  {FIXED [Customer ID] : MIN([Order Date])}\n)",
  "alternative_expression": "{FIXED [Customer ID] : MIN(DATETRUNC('month', [Order Date]))}",
  "alternative_tradeoff": "Both produce the same result. The primary form is easier to read — FIXED gives the raw first date, then DATETRUNC truncates it. The alternative applies truncation inside the LOD, which is marginally more efficient but harder to reuse if you need the exact first-date elsewhere.",
  "explanation": "The inner FIXED LOD computes the earliest [Order Date] for each [Customer ID], independent of whatever date is on the viz. DATETRUNC('month', ...) then rounds that date to the first of the month, creating a clean cohort label like '2023-01-01' that Tableau displays as 'January 2023'. Place this field on Columns to create a cohort grid.",
  "performance_notes": "This is a FIXED LOD — it runs as a subquery once per render. For a large customer table (millions of Customer IDs), this can be slow on live connections. Consider materializing cohort assignment in the data source or using a Tableau extract where it's computed at extract time.",
  "edge_case_warnings": [
    "This field calculates cohort independently of all dimension filters. If you filter to Region = 'East', customers who first purchased in the West still carry their original cohort date — which is correct for cohort analysis (cohort assignment should not change with filters), but surprising if users expect filtered behavior.",
    "A customer with only NULL [Order Date] values will have a NULL cohort — they'll appear as a separate 'null cohort' in the viz. Filter NULLs at the data source level if this is not meaningful.",
    "To complete the cohort analysis, you'll need a second calculated field for 'Months Since First Purchase': DATEDIFF('month', [First Purchase Month], DATETRUNC('month', [Order Date])). Place this on Rows alongside cohort on Columns for the classic retention grid.",
    "DATETRUNC returns a DATE value. Tableau may display it as a full date (2023-01-01) rather than 'Jan 2023' by default. Right-click the axis → Format → Dates → 'MMM YYYY' for a cleaner label."
  ],
  "complexity_rating": "Advanced",
  "teach_me": "Cohort assignment belongs in a FIXED LOD, not a table calculation — FIXED locks the assignment to each customer's own history regardless of what's visible in the view, which is exactly what cohort analysis requires."
}
```
