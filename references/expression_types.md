# Expression Type Decision Tree

Use this reference every time you need to map a business question to a Tableau expression type.
Work top-to-bottom. Stop at the first match.

---

## The Core Question

> "Does this calculation need to reference rows that are NOT in the current view?"

- **Yes** → LOD Expression (FIXED, INCLUDE, or EXCLUDE)
- **No, but it needs to reference OTHER MARKS in the view** → Table Calculation
- **No, it's row-level or a simple aggregate** → Conditional / Date Function / Basic Aggregate

---

## LOD Triage: FIXED vs INCLUDE vs EXCLUDE

Once you've determined an LOD is needed, ask:

**"What is the granularity of the calculation relative to the view?"**

| Scenario | Type | Classic Example |
|---|---|---|
| Calc grain is independent of the view | FIXED | Total company revenue regardless of what's on the viz |
| Calc grain is FINER than the view | INCLUDE | Avg orders per customer, when only Region is on the viz |
| Calc grain is COARSER than the view | EXCLUDE | Regional average when both Region and Sub-Category are on the viz |

### FIXED — when to use
- You want a value that doesn't change as users drill down or filter (unless they use context filters)
- You need a "denominator" that represents the whole (% of total, index values, benchmarks)
- You need a customer-level metric when the view is at order level
- You want cohort assignment that doesn't shift with filters: `{FIXED [Customer ID] : MIN([Order Date])}` → first order date per customer

**Empty FIXED `{ FIXED : ... }`** = table-scoped aggregate, equivalent to a grand total. Use for "% of total" denominators.

### INCLUDE — when to use
- You need an average that accounts for a lower-level dimension not on the viz
- Classic: "Average order value per customer" when only region is showing → `{INCLUDE [Customer ID] : SUM([Sales])}`
- The result is still an aggregate in the view — you must wrap with AVG(), SUM(), etc.
- INCLUDE LODs respect dimension filters (unlike FIXED), making them safer for interactive dashboards

### EXCLUDE — when to use
- You want to compute at a higher grain than what's currently in the view
- Classic: "How does this sub-category's sales compare to its parent category?" — viz has [Sub-Category] but you need a [Category]-level total → `{EXCLUDE [Sub-Category] : SUM([Sales])}`
- The excluded dimension MUST be in the view — if it's not, EXCLUDE behaves like FIXED
- Multiple exclusions: `{EXCLUDE [Sub-Category], [Region] : SUM([Sales])}` — sum as if neither dim were in the view

---

## Table Calculations — when to use

Table calculations operate on the data already fetched into the view (the "local cache"). They are fast but blind to filtered-out data.

Use Table Calculations when:
- You need **ranking** within a partition: `RANK(SUM([Sales]))`
- You need **running totals** or **cumulative sums**: `RUNNING_SUM(SUM([Sales]))`
- You need **moving/rolling averages**: `WINDOW_AVG(SUM([Sales]), -2, 0)` (current + 2 prior)
- You need **period-over-period comparison using view rows**: `SUM([Sales]) / LOOKUP(SUM([Sales]), -1) - 1`
- You need **% of total that respects visible filters**: `SUM([Sales]) / TOTAL(SUM([Sales]))`
- You need **first/last value in a partition**: `FIRST()`, `LAST()`, `INDEX()`

### Addressing vs Partitioning — always specify this
- **Addressing**: the dimensions the calculation moves ACROSS (the "direction")
- **Partitioning**: the dimensions that RESTART the calculation (the "groups")
- Default is often wrong. Always specify in Edit Table Calculation dialog, or note the assumption in your answer.
- Example: RUNNING_SUM by month across all regions → Addressing = [Order Date], Partitioning = [Region]

### Table Calc vs LOD tradeoff
| | Table Calc | LOD FIXED |
|---|---|---|
| Respects dimension filters | Yes | No (unless context) |
| Can reference other marks | Yes | No |
| Performance | Fast (post-aggregation) | Slower (generates subquery) |
| Can be used in filter | No (without tricks) | Yes |

---

## Date Functions — when to use

- You need to truncate a date to a period: `DATETRUNC('month', [Order Date])` → first day of month
- You need the number of periods between two dates: `DATEDIFF('day', [Ship Date], [Delivery Date])`
- You need to add/subtract periods: `DATEADD('month', -1, [Order Date])` → same day last month
- You need to extract a part: `DATEPART('quarter', [Order Date])` → 1, 2, 3, or 4
- You need a display label: `DATENAME('month', [Order Date])` → "January", "February"...
- Year-over-year: `DATEDIFF('year', [Order Date], TODAY()) = 0` = current year

### DATETRUNC vs DATEPART — critical distinction
- `DATETRUNC('month', [Order Date])` → returns a DATE: `2024-10-01` for any October date — use for time series axes
- `DATEPART('month', [Order Date])` → returns an INTEGER: `10` — use for grouping/filtering, not axes

---

## Conditionals — when to use

- Bucketing / segmentation: `IF [Sales] > 10000 THEN 'High' ELSEIF [Sales] > 5000 THEN 'Mid' ELSE 'Low' END`
- NULL handling: `IIF(ISNULL([Field]), 0, [Field])` or `ZN([Field])`
- Boolean flags: `[Order Date] >= DATEADD('year', -1, TODAY())` → true/false
- CASE for categorical mapping: `CASE [Region] WHEN 'East' THEN 'Eastern' ... END`

### IF vs IIF vs CASE
| | Best for |
|---|---|
| IF/THEN/ELSE | Complex logic, multiple conditions, nested |
| IIF | Simple ternary: one condition, two outcomes (but NULLs propagate differently) |
| CASE | Mapping one field's values to other values — cleaner than IF for this |

---

## Chained Patterns (two expressions)

Some questions genuinely require two calculated fields. Common patterns:

**Cohort + Aggregate:**
1. `{FIXED [Customer ID] : MIN([Order Date])}` → "First Order Month" (cohort assignment)
2. `DATETRUNC('month', [First Order Month])` → use on the viz

**Flag + Count:**
1. `IF [Profit] < 0 THEN 1 ELSE 0 END` → "Loss Flag"
2. `SUM([Loss Flag])` → count of losing orders (or use COUNTD with a different approach)

**Normalization:**
1. `{FIXED : SUM([Sales])}` → "Grand Total Sales"
2. `SUM([Sales]) / [Grand Total Sales]` → "% of Total"

When you produce a chained pattern, always label both fields and show them in order.
