# deLOD — Demystify your LODs

**Plain English in. Production-ready Tableau expressions out. With the warnings nobody tells you.**

![Status](https://img.shields.io/badge/status-live-orange) ![Model](https://img.shields.io/badge/Claude-Sonnet%204.6-blueviolet) ![Stack](https://img.shields.io/badge/stack-Streamlit%20%7C%20Python-blue) ![License](https://img.shields.io/badge/license-MIT-green)

🔗 **Live demo:** [delod.streamlit.app](https://delod.streamlit.app)

---

## What is this?

deLOD is what you open **before** you open Tableau.

You describe what you want — in plain English — and get back a production-ready calculated field with the explanation, warnings, and alternative approaches that a senior Tableau developer would hand to a junior one.

```
You: "Show each region's sales as a % of total sales"

deLOD:
  Expression type  →  LOD FIXED
  Field name       →  Region % of Total Sales
  Calculated field →  SUM([Sales]) / SUM({FIXED : SUM([Sales])})

  Why it works: The denominator uses an empty FIXED LOD to compute total
  sales across the entire dataset, independent of what's on the view.
  Dividing gives each region's share of the whole.

  ⚠️  If [Region] is on the Filters shelf and not promoted to Context,
      the FIXED denominator still includes ALL regions — your percentages
      will sum to less than 100% of visible data.

  💡  FIXED LOD expressions compute before dimension filters run. This is
      the single most common cause of "wrong totals" bugs in Tableau.
```

---

## Why this exists

Tableau ships an AI assistant (Tableau Agent) inside Tableau Cloud, but it has real limits:

| | Tableau Agent | deLOD |
|---|---|---|
| **Availability** | Requires Tableau Cloud license | Free, runs in any browser |
| **Where it works** | Inside Tableau's UI only | Before you open Tableau |
| **Schema input** | Infers from your connected data | You define it — field names land exactly right |
| **Warnings** | None | Expression-specific, production-grade |
| **Alternatives** | Never offered | When one exists, always shown with a tradeoff |
| **Teaching** | None | One transferable principle per answer |
| **Performance guidance** | None | LOD vs table calc tradeoffs, live vs extract notes |
| **Domains** | Whatever's connected | Retail, SaaS, Supply Chain, Finance, Marketing built in |

deLOD is for the analyst who doesn't have Tableau Cloud AI — contractors, freelancers, students, and anyone at a company that hasn't bought the AI tier.

---

## Features

- **5 built-in domain schemas** — Retail, SaaS, Supply Chain, Finance/FP&A, Marketing — or build your own field by field
- **8 expression types** — LOD FIXED, INCLUDE, EXCLUDE, Table Calculation, Date Function, Conditional, String Function, Basic Aggregate
- **Expert warnings** — specific to the expression written, not generic Tableau tips (Context Filters, Addressing/Partitioning, NULL propagation, fiscal year behavior, COUNT vs COUNTD)
- **Alternative approaches** — when a meaningfully different solution exists, shown with a one-line tradeoff
- **Performance notes** — LOD subquery cost, extract vs live behavior, table calc evaluation order
- **Teaching principle** — one generalizable lesson per answer
- **Session history** — last 5 questions available in one click
- **Prompt caching** — large system prompt cached via Anthropic's API, reducing latency on repeat use
- **Streaming output** — live feedback while generating

---

## Run it locally

```bash
# 1. Clone
git clone https://github.com/vaishalizilpe/delod.git
cd delod

# 2. Virtual environment
python3.11 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. API key
mkdir -p .streamlit
echo 'ANTHROPIC_API_KEY = "your-key-here"' > .streamlit/secrets.toml

# 4. Run
streamlit run app.py
```

Get an API key at [console.anthropic.com](https://console.anthropic.com). The free tier is enough to experiment.

---

## Project structure

```
delod/
├── app.py                        # Streamlit UI + rendering
├── prompts/
│   └── system_prompt.py          # Core IP — the prompt + caching logic
├── references/
│   ├── expression_types.md       # FIXED/INCLUDE/EXCLUDE/Table Calc decision tree
│   ├── common_warnings.md        # ~40 expert warnings by expression type
│   └── domain_schemas.md         # Field reference + common calcs per domain
├── examples/
│   └── sample_outputs.md         # 5 complete worked examples for calibration
├── schemas/
│   ├── retail.json
│   ├── saas.json
│   ├── supply_chain.json
│   ├── finance.json
│   ├── marketing.json
│   └── custom.json
└── requirements.txt
```

The real IP is in `references/` — a hand-authored expert knowledge base injected into every prompt. This is what separates the output quality from a generic "write me a Tableau formula" prompt.

---

## Examples it handles well

| You say | deLOD produces |
|---|---|
| "% of total [measure] by [dim]" | LOD FIXED with context filter warning |
| "Rolling 3-month average sales" | WINDOW_AVG with addressing/partitioning instructions |
| "Year-over-year growth by month" | LOOKUP(-12) table calc with sort order warning |
| "Average order value per customer when only region is visible" | LOD INCLUDE with outer aggregate explanation |
| "Flag customers who bought in Q1 but not Q2" | LOD FIXED with COUNTD + conditional logic |
| "Sub-category sales vs its parent category total" | LOD EXCLUDE with "must be in view" warning |
| "Days to fulfill each order" | DATEDIFF with NULL date warning |
| "Cohort customers by first purchase month" | Chained FIXED LOD + DATETRUNC pattern |

---

## Roadmap

Ideas that are next, not just someday:

- [ ] **Explain This Calc** — paste an existing expression, get plain-English explanation + refactoring suggestions
- [ ] **Tableau Public schema import** — paste a Tableau Public workbook URL, auto-import field names from the datasource metadata
- [ ] **LOD Debugger** — describe what your calc returns vs what you expected, get a diagnosis
- [ ] **SQL → Tableau** — paste a SQL subquery, get the equivalent calculated fields
- [ ] **Calculation library** — save, tag, and search your generated expressions across sessions
- [ ] **Workbook audit** — paste multiple calcs, get them ranked by performance risk and anti-pattern flags
- [ ] **Export to clipboard** — one-click copy with field name + syntax formatted for the Tableau calc editor

---

## Credits

Built by **Vaishali Zilpe** · [LinkedIn](https://linkedin.com/in/vaishalizilpe) · [GitHub](https://github.com/vaishalizilpe)

Powered by [Claude Sonnet 4.6](https://anthropic.com) and [Streamlit](https://streamlit.io).

Licensed under MIT. Use it, fork it, make it better.
