# deLOD — Demystify your LODs

**Plain English in. Production-ready Tableau expressions out. With the warnings nobody tells you.**

![Status](https://img.shields.io/badge/status-live-orange) ![Model](https://img.shields.io/badge/Claude-Sonnet%204.5-blueviolet) ![Stack](https://img.shields.io/badge/stack-Streamlit%20%7C%20Python-blue) ![License](https://img.shields.io/badge/license-MIT-green)

🔗 **Live demo:** [delodbyvz.streamlit.app](https://delodbyvz.streamlit.app)

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

## Three modes

**⚡ Generate Expression** — You describe what you want in plain English: "show rolling 3-month average sales by region" or "flag customers who bought in Q1 but not Q2." deLOD returns a complete, copy-paste-ready Tableau calculated field using your actual field names, an explanation of why the expression is structured the way it is, specific warnings about where it will break in production (context filters, NULL propagation, addressing and partitioning), an alternative approach when one meaningfully exists, and a one-sentence principle that makes you a better Tableau developer for next time.

**🔍 Explain This Calc** — Paste any Tableau expression — something you inherited from a workbook, found on Stack Overflow, or wrote yourself six months ago. deLOD returns a plain-English description of what it does (written for a business audience, not a developer), a step-by-step breakdown of how Tableau evaluates it, a quality rating (Good / Brittle / Over-engineered / Wrong approach / Correct but improvable), and a refactored version with an explanation of what changed and why — if the original can be improved.

**🔧 LOD Debugger** — Your expression runs without errors but returns wrong numbers. Paste the expression, describe what it actually returns, and describe what you expected. deLOD identifies the single specific root cause (not a list of possibilities), explains the mechanism behind the bug, gives you the corrected expression, tells you exactly how to verify the fix in Tableau, and teaches you the underlying principle so you don't hit the same class of bug again.

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

**Schema & data:**

- **6 built-in domain schemas** — Retail, SaaS, Supply Chain, Finance/FP&A, Marketing, or Custom
- **Import from CSV or Excel** — upload a file, field names and types are detected automatically
- **Import from Tableau Public** — paste a workbook URL, field names are pulled directly from the published `.twb`

**Expression quality:**

- **8 expression types** — LOD FIXED, INCLUDE, EXCLUDE, Table Calculation, Date Function, Conditional, String Function, Basic Aggregate
- **Expert warnings** — specific to the expression written (Context Filters, Addressing/Partitioning, NULL propagation, fiscal year behavior, COUNT vs COUNTD)
- **Alternative approaches** — when a meaningfully different solution exists, shown with a one-line tradeoff explaining when to choose each
- **Performance notes** — LOD subquery cost, extract vs live behavior, table calc evaluation order
- **Teaching principle** — one generalizable lesson per answer

**Under the hood:**

- **Prompt caching** — large expert knowledge base cached via Anthropic's API, reducing latency on repeat use
- **Streaming output** — live character feedback while generating
- **Session history** — last 5 Generate questions available in one click

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
├── app.py                        # Streamlit UI — three modes, schema import, rendering
├── tableau_public.py             # Tableau Public URL parser + .twb field extractor
├── prompts/
│   ├── system_prompt.py          # Generate mode — prompt + caching logic
│   ├── explain_prompt.py         # Explain This Calc mode
│   └── debug_prompt.py           # LOD Debugger mode
├── references/
│   ├── expression_types.md       # FIXED/INCLUDE/EXCLUDE/Table Calc decision tree
│   ├── common_warnings.md        # ~40 expert warnings by expression type
│   └── domain_schemas.md         # Field reference + common calcs per domain
├── examples/
│   └── sample_outputs.md         # 5 complete worked examples for output calibration
├── schemas/
│   ├── retail.json
│   ├── saas.json
│   ├── supply_chain.json
│   ├── finance.json
│   ├── marketing.json
│   └── custom.json
└── requirements.txt
```

The real IP is in `references/` — a hand-authored expert knowledge base injected into every prompt. This is what separates output quality from a generic "write me a Tableau formula" prompt.

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

- [ ] **SQL → Tableau** — paste a SQL subquery, get the equivalent calculated fields in order
- [ ] **Workbook audit** — paste multiple calcs, get them ranked by performance risk and anti-pattern flags
- [ ] **Calculation library** — save, tag, and search your generated expressions across sessions
- [ ] **Export to clipboard** — one-click copy formatted for the Tableau calc editor

---

## Credits

Built by **Vaishali Zilpe** · [LinkedIn](https://linkedin.com/in/vaishalizilpe) · [GitHub](https://github.com/vaishalizilpe)

Powered by [Claude](https://anthropic.com) and [Streamlit](https://streamlit.io).

Licensed under MIT. Use it, fork it, make it better.
