# deLOD — Architecture & Interview Guide

**Built by Vaishali Zilpe**
[delodbyvz.streamlit.app](https://delodbyvz.streamlit.app) · [github.com/vaishalizilpe/deLOD](https://github.com/vaishalizilpe/deLOD)

---

## One-line pitch

A Tableau expression tool built on Claude that turns plain English into production-ready calculated fields — with expert warnings, alternatives, and teaching. Three modes: Generate, Explain, Debug.

---

## What problem it solves

Tableau Agent (Salesforce's built-in AI) only works inside licensed Tableau Cloud, generates syntax with no warnings, and teaches nothing. deLOD fills the gap for analysts who need expert-level guidance outside that environment — with output that reflects what a senior Tableau developer would actually hand to a junior one.

---

## Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | Streamlit | Python-native, session state built in, fast to iterate |
| LLM | Claude Sonnet 4.5 via Anthropic SDK | Structured JSON output, streaming, prompt caching |
| Schema import | pandas + requests + stdlib XML | CSV/Excel type inference, Tableau Public `.twb` parsing |
| Hosting | Streamlit Community Cloud | Zero-config deployment from GitHub |

---

## Architecture overview

```
User
  │
  ▼
Streamlit UI (app.py)
  │  sidebar: schema editor, domain picker, CSV/Tableau Public import
  │  main: 3 tabs — Generate / Explain / Debug
  │
  ├── build_system_prompt()     ← prompts/system_prompt.py
  ├── build_explain_prompt()    ← prompts/explain_prompt.py
  └── build_debug_prompt()      ← prompts/debug_prompt.py
         │
         │  Each prompt = schema + domain + full reference knowledge base
         │
         ▼
  Anthropic SDK
  client.messages.stream()      ← streaming JSON response
         │
         ▼
  JSON parsed → render_generate() / render_explain() / render_debug()
         │
         ▼
  Styled HTML components in Streamlit
```

---

## The three modes

### ⚡ Generate
User describes a business question in plain English. The system maps it to an expression type (LOD FIXED/INCLUDE/EXCLUDE, Table Calculation, Date Function, etc.), generates copy-paste Tableau syntax using the user's actual field names, and returns warnings, an alternative, and a teaching principle.

### 🔍 Explain This Calc
User pastes any existing Tableau expression. Claude returns: plain-English explanation (jargon-free), step-by-step evaluation breakdown, a quality rating from a fixed set (Good / Brittle / Over-engineered / Wrong approach / Correct but improvable), a refactored version with rationale, and applicable warnings.

### 🔧 LOD Debugger
User pastes a broken expression and describes actual vs expected output. Claude identifies the single specific root cause, explains the mechanism, returns the corrected expression, and tells the user exactly how to verify the fix in Tableau.

---

## Key technical decisions

### 1. Structured JSON output

Every Claude response is a JSON object with named fields (`expression_type`, `primary_expression`, `edge_case_warnings`, `teach_me`, etc.). This was a deliberate choice over markdown:

- Each section is conditionally rendered — warnings only show if they exist
- Each section is independently styled (red boxes for warnings, purple for principles, green for fixes)
- Parsing is deterministic — no regex scraping of prose
- Different JSON schemas per mode without changing the render pipeline

### 2. Prompt caching

The system prompt for Generate mode is ~6,000 tokens — it includes the full expression type decision tree, ~40 expert warnings by type, domain field references, and 5 calibration examples. Sending this on every call is expensive and slow.

Using Anthropic's `cache_control: {"type": "ephemeral"}` on the system prompt block means repeat calls (same schema, different question) hit the cache — roughly 90% cost reduction on the prompt tokens and ~200ms latency improvement.

```python
system_blocks = [{
    "type": "text",
    "text": system_prompt,
    "cache_control": {"type": "ephemeral"},
}]
```

### 3. Streaming

`client.messages.stream()` instead of `client.messages.create()`. The user sees a live character counter while Claude generates, instead of a blank spinner for 3–5 seconds. UX is significantly better for outputs that are 800–1,200 tokens.

### 4. Knowledge base injection (not RAG)

The reference files (`expression_types.md`, `common_warnings.md`, `domain_schemas.md`, `sample_outputs.md`) are loaded at module import time as Python constants and injected wholesale into every system prompt.

This is the deliberate alternative to RAG. The total knowledge base is ~8KB — small enough to fit in context, large enough to meaningfully improve output quality. No vector DB, no retrieval latency, no retrieval errors. For this scale, injection beats retrieval.

```python
# Loaded once at import, injected into every prompt
EXPRESSION_TYPES = _load_reference("expression_types.md")
COMMON_WARNINGS  = _load_reference("common_warnings.md")
```

### 5. Separate prompt modules per mode

Each mode has its own file: `system_prompt.py`, `explain_prompt.py`, `debug_prompt.py`. Each has its own JSON schema and its own set of rules. They share the reference constants but nothing else. This means:

- Each mode can evolve independently
- Adding a fourth mode doesn't touch existing prompts
- The JSON schema is explicit per mode — no ambiguity about what fields are expected

### 6. Session state per mode

Streamlit reruns the entire script on every interaction. Results are stored in `st.session_state.gen_result`, `st.session_state.explain_result`, `st.session_state.debug_result` so switching tabs doesn't clear the last output.

### 7. Schema import — two sources

**CSV / Excel:** `pandas.read_csv(file, nrows=50)` reads only 50 rows for type inference. dtypes map to Tableau types (string → String, int64/float64 → Number, datetime64 → Date, bool → Boolean). User sees a preview table before applying.

**Tableau Public:** URL is parsed with regex to extract the workbook slug. The `.twb` file is fetched via `requests` — Tableau Public workbooks are XML. `xml.etree.ElementTree` parses `<column>` elements from each `<datasource>` block, extracting `name`/`caption` and `datatype`. System fields (Measure Names, Number of Records, etc.) are filtered out. Falls back with clear error messages for packaged `.twbx` files.

---

## What makes the output quality high

The system prompt has explicit rules that most AI tools skip:

- **Warnings must reference actual field names** — not "FIXED LODs can be slow" but "If [Region] is on the Filters shelf and not promoted to Context, this FIXED LOD ignores it entirely"
- **One diagnosis, not a list** — the debugger is instructed to commit to a single root cause, not hedge with possibilities
- **The teaching line is mandatory** — every response ends with one generalizable principle, not a summary
- **Never invent fields** — the expression must only use field names from the user's provided schema; if a needed field is missing, it must be called out in warnings

---

## Numbers to know

| | |
|---|---|
| Reference knowledge base | ~8KB injected into every prompt |
| Expert warnings | ~40 specific warnings organized by expression type |
| Calibration examples | 5 complete worked JSON outputs |
| Domain schemas | 6 (Retail, SaaS, Supply Chain, Finance, Marketing, Custom) |
| Expression types | 8 |
| Files in repo | 20 |

---

## Project structure

```
delod/
├── app.py                    # Streamlit UI — three modes, schema import, rendering
├── tableau_public.py         # Tableau Public URL parser + .twb field extractor
├── prompts/
│   ├── system_prompt.py      # Generate mode — prompt + caching logic
│   ├── explain_prompt.py     # Explain This Calc mode
│   └── debug_prompt.py       # LOD Debugger mode
├── references/
│   ├── expression_types.md   # FIXED/INCLUDE/EXCLUDE/Table Calc decision tree
│   ├── common_warnings.md    # ~40 expert warnings by expression type
│   └── domain_schemas.md     # Field reference + common calcs per domain
├── examples/
│   └── sample_outputs.md     # 5 complete worked examples for output calibration
├── schemas/
│   ├── retail.json
│   ├── saas.json
│   ├── supply_chain.json
│   ├── finance.json
│   ├── marketing.json
│   └── custom.json
└── requirements.txt
```

---

## What I'd build next

- **SQL → Tableau** — translate a SQL subquery into equivalent calculated fields in dependency order
- **Workbook audit** — paste 5–10 calcs, get them ranked by performance risk and anti-pattern flags
- **Calculation library** — persistent storage of generated expressions across sessions with tags and search

---

## Summary for "tell me about a project you built"

> deLOD is a Tableau expression tool I built with Claude and Streamlit. It has three modes — Generate, Explain, and Debug — and the core design decision was structured JSON output: every Claude response is a typed object so each section (warnings, alternatives, teaching principle) can be conditionally rendered and independently styled. The system prompt injects a hand-authored expert knowledge base on every call instead of using RAG — the whole thing is under 8KB so injection beats retrieval at this scale. I added prompt caching on the system prompt block which cut latency by ~200ms and cost by ~90% on the prompt tokens. The Tableau Public import parses the `.twb` XML directly using Python's stdlib XML parser to extract field names without needing a Tableau API key.

---

*Built with Claude Sonnet 4.5 and Streamlit · April 2026*
