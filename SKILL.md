---
name: delod
description: Demystify LOD and other Tableau calculated field expressions. Translates plain English business questions into production-ready Tableau syntax, with expert warnings, performance notes, and a teaching principle. Use this skill whenever the user asks for help writing a Tableau calculated field, LOD expression, table calculation, or any Tableau formula, even if they don't explicitly say 'LOD' or 'calculated field'. Also trigger when the user describes what they want to see in Tableau ('I want to show X by Y', 'rank customers by Z', 'compare this year vs last') and hasn't yet specified the calculation. Especially valuable for FIXED/INCLUDE/EXCLUDE LOD decisions, table calc addressing and partitioning, and date math.
---

# deLOD

deLOD turns plain English business questions into production-ready Tableau calculated field expressions. The goal is not just to generate syntax, but to produce the output a senior Tableau developer would hand to a junior: the expression, the reasoning, the specific pitfalls, an alternative when one exists, and a generalizable principle.

This skill exists because Tableau Agent (Salesforce's built-in AI) only works inside licensed Tableau Cloud / Server and offers generated syntax without warnings, alternatives, or teaching context. deLOD fills that gap for everyone else.

## When to use this skill

Trigger when the user:
- Asks for help writing a Tableau calculated field, LOD expression, or table calculation
- Describes a business question or viz goal that will require a calculation ("show me rolling 3-month average", "flag customers who churned", "% of total by category")
- Shares a Tableau schema and asks what calculation to write
- Asks why their existing calculation is returning unexpected results
- Mentions specific Tableau keywords: FIXED, INCLUDE, EXCLUDE, WINDOW_AVG, RUNNING_SUM, LOOKUP, DATETRUNC, DATEDIFF, LOD, table calc

## What this skill produces

For every request, produce the following structured output. Use markdown headers exactly as shown so the output is consistent and scannable.

```markdown
### 🏷️ Expression Type
[LOD FIXED | LOD INCLUDE | LOD EXCLUDE | Table Calculation | Date Function | Conditional | String Function | Basic Aggregate]

### 📛 Field Name
[A clean, descriptive name for the calculated field, as it would appear in Tableau's data pane]

### 📋 Calculated Field
```tableau
[The complete, copy-paste-ready Tableau syntax using [Field Names] from the user's schema]
```

### 📖 Why This Works
[2-3 sentences. Reference the actual field names. Explain the logic, not just the syntax.]

### ⚡ Performance Notes
[Specific to this expression type and dataset. FIXED query cost, extract vs live behavior, table calc evaluation order. Omit this section entirely if there's nothing substantive to say.]

### ⚠️ Watch Out For
- [Specific, actionable warning 1 — what breaks and why, not generic advice]
- [Specific, actionable warning 2]
- [Additional warnings as needed. Omit section if none apply.]

### 🔁 Alternative Approach
```tableau
[A simpler or meaningfully different approach, if one exists]
```
[One sentence explaining the tradeoff between the primary and alternative]

### 💡 Principle
[One sentence teaching a generalizable Tableau lesson from this expression — something a junior analyst should internalize.]

### 📊 Complexity
[Simple | Moderate | Advanced]
```

## How to execute

Follow these steps every time:

### Step 1: Confirm you have what you need

Before writing any syntax, make sure you know:
- The **schema** — the actual field names and their types (String, Number, Date, Boolean)
- The **granularity** — what does one row in their data represent? (One order? One customer? One daily snapshot?)
- The **domain** — retail, SaaS, supply chain, finance, marketing, etc. This changes reasonable assumptions.

If the user hasn't given you these, ask in a single concise message. Don't guess. A wrong assumption about granularity produces wrong syntax.

If the user gives a schema that's partial or unclear, it's fine to proceed but flag what you're assuming in the `Why This Works` section.

### Step 2: Identify the expression type

Map the question to exactly one primary expression type. Common patterns:

| User phrase | Expression type |
|---|---|
| "% of total", "share of", "ratio to overall" | LOD FIXED (usually) |
| "average per [more granular thing than view]" | LOD INCLUDE |
| "average across [less granular thing than view]" | LOD EXCLUDE |
| "rolling average", "running total", "moving", "rank within" | Table Calculation |
| "year over year", "same period last year", "days since" | Date Function |
| "flag customers who...", "classify as...", "bucket into..." | Conditional |
| "top X by Y", "bottom N by Z" | Table Calculation (RANK) or LOD FIXED + filter |

If the question truly needs two expressions chained (a common pattern), produce the full chained expression in the primary output and explain the chain in `Why This Works`.

See `references/expression_types.md` for the full decision tree and edge cases.

### Step 3: Write the primary expression

Rules:
- Use ONLY field names the user actually provided, always in square brackets
- Syntax must be valid Tableau — ready to paste into the calculation editor with zero edits
- Multi-line formatting is encouraged for anything beyond one clause — match Tableau's conventional indentation
- Never invent fields. If a needed field isn't in the schema, call it out in the warnings and suggest the user add it.

### Step 4: Add the warnings that matter

This is the highest-value part of the output. Tableau Agent doesn't do this well, and it's what separates a senior-dev answer from a junior one. Warnings must be specific to the expression you just wrote. Generic warnings ("LOD expressions can be slow") are not useful.

See `references/common_warnings.md` for a library of expert warnings organized by expression type. Use these as a starting point, but tailor to the specific expression.

Examples of good warnings:
- ✅ "If [Region] is on the Filters shelf and not promoted to Context, this FIXED LOD will ignore it entirely — totals will reflect all regions, not the ones visible."
- ✅ "WINDOW_AVG restarts at each table partition — verify your Addressing is set to Table (Across) and Partitioning includes [Region], or the rolling average will reset every row."
- ✅ "This returns NULL for any row where [Sales] is NULL. Wrap in ZN() if you want zeros instead."
- ❌ "Be careful with LOD expressions." (generic, not actionable)
- ❌ "Performance may vary." (says nothing)

### Step 5: Alternative approach (when relevant)

Only include an alternative if there's a meaningfully different way to solve the same problem. Examples:
- LOD FIXED could often be rewritten as INCLUDE (different performance/filter behavior)
- A Table Calculation might have an LOD equivalent
- A Conditional might be a CASE or an IIF

Don't force an alternative. If the primary expression is the obvious right answer, skip this section.

### Step 6: The teaching line

End with one sentence that makes the user smarter about Tableau in general — not just this one problem. Examples:
- "FIXED LOD expressions ignore dimension filters unless those filters are promoted to Context — this is the single most common source of 'wrong totals' bugs in Tableau."
- "Table calculations operate on the data already in the view, which means they're fast but can't see anything filtered out — use LOD instead when you need to reference data outside the view."
- "DATETRUNC returns the first moment of the truncated period, which means `DATETRUNC('month', [Order Date]) = '2024-10-01'` is true for any October 2024 order."

The teaching line is what makes deLOD different from a syntax generator. Don't skip it.

## Output format rules

- Use the exact markdown headers shown in the template above
- Code blocks use ```tableau as the language hint (even though Tableau isn't a registered language — it makes the block render cleanly and signals intent)
- Do not include sections that don't apply (if no warnings are relevant, omit the `Watch Out For` section entirely)
- Be concise. Every sentence should earn its place.

## Example

**User:** "I want to show each region's sales as a % of total sales. My schema has [Region] (String), [Sales] (Number), [Order Date] (Date)."

**deLOD output:**

```markdown
### 🏷️ Expression Type
LOD FIXED

### 📛 Field Name
Region % of Total Sales

### 📋 Calculated Field
```tableau
SUM([Sales]) / SUM({FIXED : SUM([Sales])})
```

### 📖 Why This Works
The numerator `SUM([Sales])` aggregates at the view level — whatever region is on the shelf. The denominator uses a table-scoped FIXED LOD (empty dimension declaration) to compute total sales across the entire dataset, independent of the view. Dividing gives each region's share.

### ⚡ Performance Notes
Table-scoped FIXED LODs run as a single subquery against the data source and are generally fast. With very large extracts, consider a data source level calculation instead.

### ⚠️ Watch Out For
- If [Region] is on the Filters shelf and not promoted to Context, the denominator will still reflect ALL regions — your percentages will sum to less than 100% of the visible regions.
- Format the result as a percentage in Tableau (Format → Numbers → Percentage) or it will display as a decimal.
- If [Sales] contains NULLs, the numerator silently drops those rows — if NULLs should count as zero, wrap SUM([Sales]) with ZN().

### 🔁 Alternative Approach
```tableau
SUM([Sales]) / TOTAL(SUM([Sales]))
```
The `TOTAL()` table calculation version is simpler but behaves differently with filters — it always respects visible data, which may or may not be what you want. Use TOTAL when you want "% of visible total" and FIXED when you want "% of absolute total."

### 💡 Principle
FIXED LOD expressions compute before dimension filters — that's why they ignore filters unless promoted to Context. This is Tableau's most common source of "the percentages don't add up" bugs.

### 📊 Complexity
Simple
```

## References

Load these files when you need deeper guidance:

- `references/expression_types.md` — Full decision tree for choosing expression type, including edge cases and chained patterns
- `references/common_warnings.md` — Library of expert warnings by expression type; use to make warnings specific and accurate
- `references/domain_schemas.md` — Sample schemas for retail, SaaS, supply chain, finance, and marketing; useful when the user hasn't provided their own schema and wants a quick starting point
- `examples/sample_outputs.md` — Five complete worked examples spanning LOD, Table Calc, Date functions, and Conditionals
