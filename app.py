"""
deLOD — Demystify your LODs
Three modes: Generate · Explain This Calc · LOD Debugger
"""
import json
import streamlit as st
import anthropic
import pandas as pd
from pathlib import Path

from prompts.system_prompt import build_system_prompt, build_messages_with_cache
from prompts.explain_prompt import build_explain_prompt, build_explain_messages
from prompts.debug_prompt import build_debug_prompt, build_debug_messages
from tableau_public import import_fields_from_url

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="deLOD · Demystify your LODs",
    page_icon="🟠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Font ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }

    /* ── App shell ── */
    .stApp { background: #07090f !important; }
    .main .block-container { padding-top: 1.5rem; max-width: 1100px; }

    /* ── Inputs ── */
    .stTextArea textarea, .stTextInput input {
        background: #0d1117 !important;
        color: #cbd5e1 !important;
        border: 1px solid #1e2d45 !important;
        border-radius: 10px !important;
        font-size: 14px !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #f59e0b !important;
        box-shadow: 0 0 0 3px rgba(245,158,11,0.12) !important;
    }
    .stTextArea textarea::placeholder,
    .stTextInput input::placeholder { color: #334155 !important; }

    /* ── Primary button ── */
    [data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #f59e0b 0%, #ea580c 100%) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        padding: 0.6rem 1.8rem !important;
        box-shadow: 0 4px 16px rgba(245,158,11,0.28) !important;
        transition: box-shadow 0.2s, transform 0.2s !important;
    }
    [data-testid="baseButton-primary"]:hover {
        box-shadow: 0 6px 22px rgba(245,158,11,0.42) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Secondary buttons ── */
    [data-testid="baseButton-secondary"] {
        background: #0d1117 !important;
        color: #64748b !important;
        border: 1px solid #1e293b !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 12px !important;
        transition: border-color 0.15s, color 0.15s !important;
    }
    [data-testid="baseButton-secondary"]:hover {
        background: #111827 !important;
        border-color: #f59e0b !important;
        color: #f59e0b !important;
    }

    /* ── Selectbox ── */
    [data-baseweb="select"] > div {
        background: #0d1117 !important;
        border: 1px solid #1e293b !important;
        border-radius: 8px !important;
        color: #94a3b8 !important;
    }
    [data-baseweb="popover"] { background: #0d1117 !important; border: 1px solid #1e293b !important; }
    [data-baseweb="menu"] { background: #0d1117 !important; }
    [role="option"]:hover { background: #1e293b !important; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        border-bottom: 1px solid #1a2235 !important;
        gap: 0;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: #475569 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 11px 22px !important;
        border-radius: 0 !important;
        border-bottom: 2px solid transparent !important;
        margin-bottom: -1px !important;
        transition: color 0.15s !important;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #94a3b8 !important; background: transparent !important; }
    .stTabs [aria-selected="true"] {
        background: transparent !important;
        color: #f59e0b !important;
        border-bottom: 2px solid #f59e0b !important;
    }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 28px !important; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #06080d !important;
        border-right: 1px solid #0f1623 !important;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span:not(.logo-title):not(.de) { color: #4b5563 !important; }
    [data-testid="stSidebar"] input { color: #94a3b8 !important; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #4b5563 !important; }

    /* ── Radio buttons ── */
    [data-testid="stRadio"] label p { color: #4b5563 !important; }
    [data-testid="stRadio"] [aria-checked="true"] ~ div p { color: #f59e0b !important; }

    /* ── Expander ── */
    [data-testid="stExpander"] {
        background: #0a0e17 !important;
        border: 1px solid #1a2235 !important;
        border-radius: 10px !important;
        margin-top: 6px !important;
    }
    [data-testid="stExpander"] summary { color: #475569 !important; }
    [data-testid="stExpander"] summary:hover { color: #64748b !important; }
    [data-testid="stExpander"] [data-testid="stVerticalBlock"] { background: #0a0e17 !important; }

    /* ── File uploader ── */
    [data-testid="stFileUploader"] { background: transparent !important; }
    [data-testid="stFileDropzoneInstructions"] { color: #475569 !important; }
    [data-testid="stFileUploadDropzone"] {
        background: #0a0e17 !important;
        border: 1px dashed #1e293b !important;
        border-radius: 10px !important;
    }
    [data-testid="stFileUploadDropzone"]:hover { border-color: #f59e0b !important; }

    /* ── Dataframe ── */
    [data-testid="stDataFrame"] { background: #0a0e17 !important; border-radius: 8px !important; }
    [data-testid="stDataFrame"] * { color: #64748b !important; }
    .dvn-scroller, .dvn-scroller * { background: #0a0e17 !important; }

    /* ── Alerts (success / error / warning) ── */
    [data-testid="stAlert"] {
        background: #0a0e17 !important;
        border-radius: 8px !important;
        border: 1px solid #1a2235 !important;
    }
    [data-testid="stAlert"] p { color: #94a3b8 !important; }

    /* ── Caption / small text ── */
    [data-testid="stCaptionContainer"] p,
    .stCaption { color: #334155 !important; font-size: 12px !important; }

    /* ── Spinner ── */
    [data-testid="stSpinner"] p { color: #64748b !important; }
    .stSpinner > div { border-top-color: #f59e0b !important; }

    /* ── Markdown containers (body text) ── */
    [data-testid="stMarkdownContainer"] p { color: #64748b; }
    [data-testid="stMarkdownContainer"] strong { color: #94a3b8; }
    [data-testid="stMarkdownContainer"] a { color: #f59e0b !important; }

    /* ── Code ── */
    code {
        background: #0d1117 !important;
        color: #fde68a !important;
        padding: 2px 7px !important;
        border-radius: 5px !important;
        font-size: 12px !important;
        border: 1px solid #1e293b !important;
    }
    pre {
        background: #060a0f !important;
        border: 1px solid #1a2235 !important;
        border-radius: 10px !important;
        position: relative !important;
        overflow: hidden !important;
    }
    pre::before {
        content: 'TABLEAU';
        position: absolute; top: 12px; right: 16px;
        font-size: 9px; font-weight: 800;
        letter-spacing: 0.18em; color: #1e3a5f;
    }
    pre code {
        font-size: 13px !important;
        line-height: 1.8 !important;
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
    }

    /* ── Logo ── */
    .logo-title { font-size: 2rem; font-weight: 800; letter-spacing: -1.5px; line-height: 1; color: #e2e8f0; }
    .logo-title .de { color: #f59e0b; text-shadow: 0 0 24px rgba(245,158,11,0.35); }
    .tagline { color: #334155; font-size: 0.85rem; margin-top: 6px; margin-bottom: 28px; }

    /* ── Custom component styles ── */
    .badge {
        display: inline-flex; align-items: center;
        padding: 3px 11px; border-radius: 20px;
        font-size: 10px; font-weight: 800;
        letter-spacing: 0.07em; border: 1px solid;
        text-transform: uppercase;
    }
    .field-pill {
        background: #0d1117; color: #475569;
        padding: 3px 10px; border-radius: 6px;
        font-size: 12px; font-family: monospace;
        border: 1px solid #1a2235;
    }
    .section-label {
        font-size: 9px; font-weight: 800; color: #1e293b;
        letter-spacing: 0.18em; text-transform: uppercase;
        margin-bottom: 10px; margin-top: 2px;
        display: flex; align-items: center; gap: 10px;
    }
    .section-label::after { content: ''; flex: 1; height: 1px; background: #0f1623; }

    /* ── Result card ── */
    .result-card {
        background: #090d16; border: 1px solid #1a2235;
        border-radius: 14px; padding: 0;
        margin-top: 22px; overflow: hidden;
    }
    .result-card-accent { height: 3px; }
    .result-card-body { padding: 22px 24px; }

    /* ── Info boxes ── */
    .warn-box {
        background: #130808; border-left: 3px solid #dc2626;
        padding: 10px 14px; border-radius: 0 8px 8px 0;
        margin: 6px 0; color: #fca5a5;
        font-size: 13px; line-height: 1.55;
    }
    .perf-box {
        background: #070f1e; border-left: 3px solid #2563eb;
        padding: 11px 15px; border-radius: 0 8px 8px 0;
        color: #93c5fd; font-size: 13px; line-height: 1.55;
    }
    .teach-box {
        background: #0c0920; border-left: 3px solid #7c3aed;
        padding: 13px 16px; border-radius: 0 8px 8px 0;
        color: #c4b5fd; font-size: 13px; font-style: italic; line-height: 1.65;
    }
    .plain-english {
        background: #06130d; border-left: 3px solid #059669;
        padding: 14px 18px; border-radius: 0 8px 8px 0;
        color: #6ee7b7; font-size: 15px; line-height: 1.7; font-weight: 500;
    }
    .breakdown-step {
        background: #0a0e17; border: 1px solid #1a2235;
        border-left: 3px solid #1e3a5f;
        padding: 9px 14px; border-radius: 0 8px 8px 0;
        margin: 5px 0; color: #64748b; font-size: 13px; line-height: 1.5;
    }
    .diagnosis-box {
        background: #130707; border-left: 3px solid #dc2626;
        padding: 14px 18px; border-radius: 0 8px 8px 0;
        color: #fca5a5; font-size: 14px; line-height: 1.6; font-weight: 500;
    }
    .fix-box {
        background: #06130d; border-left: 3px solid #059669;
        padding: 12px 16px; border-radius: 0 8px 8px 0;
        color: #6ee7b7; font-size: 13px; line-height: 1.6;
    }
    .verify-box {
        background: #070f1e; border-left: 3px solid #2563eb;
        padding: 11px 15px; border-radius: 0 8px 8px 0;
        color: #93c5fd; font-size: 13px;
    }

    /* ── Empty states ── */
    .empty-state {
        text-align: center; padding: 80px 20px;
        border: 1px dashed #0f1623; border-radius: 14px;
        margin-top: 22px; background: #070a0f;
    }
    .empty-icon { font-size: 48px; opacity: 0.2; margin-bottom: 16px; line-height: 1; }
    .empty-title { font-size: 17px; font-weight: 700; color: #1e293b; margin-bottom: 8px; }
    .empty-sub { font-size: 13px; color: #111827; max-width: 340px; margin: 0 auto; line-height: 1.65; }

    /* ── Mode description ── */
    .mode-desc {
        color: #475569; font-size: 13px; line-height: 1.65; margin-bottom: 18px;
        padding: 12px 16px; background: #0a0e17; border-radius: 8px;
        border: 1px solid #0f1623;
    }

    /* ── Explanation text inside result cards ── */
    .card-body-text { color: #64748b; font-size: 14px; line-height: 1.7; }
    .alt-tradeoff { color: #334155; font-size: 12px; margin-top: 6px; font-style: italic; line-height: 1.5; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
BADGE_STYLES = {
    "LOD FIXED":         ("#78350f", "#fde68a", "#f59e0b"),
    "LOD INCLUDE":       ("#064e3b", "#6ee7b7", "#10b981"),
    "LOD EXCLUDE":       ("#1e1b4b", "#c4b5fd", "#7c3aed"),
    "Table Calculation": ("#1e3a5f", "#93c5fd", "#3b82f6"),
    "Date Function":     ("#4a044e", "#f5d0fe", "#d946ef"),
    "Conditional":       ("#2d1b69", "#ddd6fe", "#8b5cf6"),
    "String Function":   ("#042f2e", "#99f6e4", "#14b8a6"),
    "Basic Aggregate":   ("#431407", "#fed7aa", "#f97316"),
    "Compound":          ("#1a1a2e", "#a5b4fc", "#6366f1"),
    "Unknown":           ("#1e293b", "#94a3b8", "#475569"),
}
COMPLEXITY_COLOR = {"Simple": "#10b981", "Moderate": "#f59e0b", "Advanced": "#ef4444"}
QUALITY_STYLES = {
    "Good":                    ("#064e3b", "#6ee7b7", "#10b981"),
    "Brittle":                 ("#78350f", "#fde68a", "#f59e0b"),
    "Over-engineered":         ("#1e1b4b", "#c4b5fd", "#7c3aed"),
    "Wrong approach":          ("#4c0519", "#fecdd3", "#ef4444"),
    "Correct but improvable":  ("#1e3a5f", "#93c5fd", "#3b82f6"),
}

# ── CSV / Excel field inference ───────────────────────────────────────────────
def dtype_to_field_type(dtype) -> str:
    name = str(dtype)
    if "datetime" in name:
        return "Date"
    if "bool" in name:
        return "Boolean"
    if any(t in name for t in ("int", "float", "uint")):
        return "Number"
    return "String"


def fields_from_dataframe(df: pd.DataFrame) -> list[dict]:
    """Return [{name, type}] inferred from a DataFrame's columns and dtypes."""
    fields = []
    for col in df.columns:
        fields.append({"name": str(col), "type": dtype_to_field_type(df[col].dtype)})
    return fields


# ── Load schemas ──────────────────────────────────────────────────────────────
def load_schemas() -> dict:
    schemas = {}
    schema_dir = Path(__file__).parent / "schemas"
    for path in sorted(schema_dir.glob("*.json")):
        with open(path) as f:
            schemas[path.stem] = json.load(f)
    return schemas

SCHEMAS = load_schemas()
FIELD_TYPES = ["String", "Number", "Date", "Boolean"]

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [
    ("domain",         "retail"),
    ("fields",         [dict(f) for f in SCHEMAS["retail"]["fields"]]),
    ("history",        []),
    ("gen_result",     None),
    ("explain_result", None),
    ("debug_result",   None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="logo-title"><span class="de">de</span>LOD</div>', unsafe_allow_html=True)
    st.markdown('<div class="tagline">Demystify your LODs</div>', unsafe_allow_html=True)

    # Domain picker
    st.markdown('<div class="section-label">Domain</div>', unsafe_allow_html=True)
    domain_labels = {k: v["label"] for k, v in SCHEMAS.items()}
    new_domain = st.radio(
        "Domain",
        options=list(domain_labels.keys()),
        format_func=lambda k: domain_labels[k],
        label_visibility="collapsed",
        key="domain_radio",
        index=list(domain_labels.keys()).index(st.session_state.domain),
    )
    if new_domain != st.session_state.domain:
        st.session_state.domain = new_domain
        st.session_state.fields = [dict(f) for f in SCHEMAS[new_domain]["fields"]]
        st.rerun()

    # Schema editor
    st.markdown('<div class="section-label" style="margin-top:20px;">Your Schema</div>', unsafe_allow_html=True)
    remove_idx = None
    for i, field in enumerate(st.session_state.fields):
        c1, c2, c3 = st.columns([5, 3, 1])
        with c1:
            new_name = st.text_input("name", field["name"], key=f"name_{i}", label_visibility="collapsed")
        with c2:
            new_type = st.selectbox(
                "type", FIELD_TYPES,
                index=FIELD_TYPES.index(field["type"]) if field["type"] in FIELD_TYPES else 0,
                key=f"type_{i}", label_visibility="collapsed",
            )
        with c3:
            if st.button("×", key=f"rm_{i}"):
                remove_idx = i
        st.session_state.fields[i] = {"name": new_name, "type": new_type}

    if remove_idx is not None:
        st.session_state.fields.pop(remove_idx)
        st.rerun()

    if st.button("+ Add field", use_container_width=True):
        st.session_state.fields.append({"name": "", "type": "String"})
        st.rerun()

    # Tableau Public import
    st.markdown('<div class="section-label" style="margin-top:20px;">Import from Tableau Public</div>',
                unsafe_allow_html=True)
    with st.expander("🔗 Paste workbook URL"):
        tp_url = st.text_input(
            "Tableau Public URL",
            placeholder="https://public.tableau.com/app/profile/…/viz/…",
            label_visibility="collapsed",
            key="tp_url_input",
        )
        if st.button("Import Fields", use_container_width=True, key="tp_import_btn"):
            if tp_url.strip():
                with st.spinner("Fetching workbook…"):
                    result = import_fields_from_url(tp_url)
                if result["success"]:
                    st.session_state.fields = result["fields"]
                    st.session_state.domain = "custom"
                    st.success(
                        f"Imported {len(result['fields'])} fields "
                        f"from {result['workbook_name']}"
                    )
                    st.rerun()
                else:
                    st.error(result["error"])
            else:
                st.warning("Paste a Tableau Public workbook URL first.")

    # CSV / Excel import
    with st.expander("📂 Upload CSV or Excel"):
        st.markdown(
            '<div style="background:#0d1117;border:1px solid #1e293b;border-radius:6px;'
            'padding:10px 12px;margin-bottom:10px;font-size:11px;color:#64748b;line-height:1.7;">'
            '<strong style="color:#94a3b8;">What this does:</strong> reads your column headers and '
            'infers field types so you can generate expressions against your real field names. '
            'Your data is never stored or sent anywhere — only the schema is used.<br><br>'
            '<strong style="color:#94a3b8;">Limitations to know:</strong><br>'
            '▸ <strong>Dates stored as text</strong> (e.g. "2024-01-15") come in as String — '
            'change them to Date in the schema editor above.<br>'
            '▸ <strong>Only the first 50 rows</strong> are read for type inference. '
            'A column that\'s mostly empty at the top may be mistyped.<br>'
            '▸ <strong>Calculated fields and Tableau-specific types</strong> '
            '(LODs, parameters) won\'t be in your CSV — add them manually.<br>'
            '▸ <strong>Excel merged cells or multi-row headers</strong> will confuse the parser — '
            'export a clean flat CSV instead.'
            '</div>',
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "Drop a file",
            type=["csv", "xlsx", "xls"],
            label_visibility="collapsed",
            key="csv_upload",
        )
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file, nrows=50)
                else:
                    df = pd.read_excel(uploaded_file, nrows=50)

                fields = fields_from_dataframe(df)
                if fields:
                    st.caption(f"{len(fields)} columns detected — review types before applying.")
                    preview = pd.DataFrame(fields).rename(
                        columns={"name": "Field", "type": "Type"}
                    )
                    st.dataframe(preview, hide_index=True, use_container_width=True)

                    if st.button("Apply to Schema", use_container_width=True, key="csv_apply_btn"):
                        st.session_state.fields = fields
                        st.session_state.domain = "custom"
                        st.success(f"Schema updated with {len(fields)} fields from {uploaded_file.name}")
                        st.rerun()
                else:
                    st.warning("No columns found in this file.")
            except Exception as e:
                st.error(f"Couldn't read file: {e}")

    # Recent history (generate mode only)
    if st.session_state.history:
        st.markdown('<div class="section-label" style="margin-top:20px;">Recent</div>', unsafe_allow_html=True)
        for i, item in enumerate(st.session_state.history[:5]):
            label = item["q"][:60] + ("…" if len(item["q"]) > 60 else "")
            if st.button(label, key=f"hist_{i}", use_container_width=True):
                st.session_state.replay = item
                st.rerun()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="logo-title"><span class="de">de</span>LOD</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="tagline">English in · Tableau out · With the warnings nobody tells you</div>',
    unsafe_allow_html=True,
)

# ── Shared Claude client ───────────────────────────────────────────────────────
def get_client() -> anthropic.Anthropic | None:
    try:
        return anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    except Exception:
        st.error("Missing ANTHROPIC_API_KEY in .streamlit/secrets.toml")
        return None


def stream_and_parse(client: anthropic.Anthropic, system_blocks, messages) -> dict | None:
    """Stream a Claude response and parse the JSON result."""
    raw_chunks: list[str] = []
    placeholder = st.empty()
    try:
        with client.messages.stream(
            model="claude-sonnet-4-5",
            max_tokens=2000,
            system=system_blocks,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                raw_chunks.append(text)
                placeholder.caption(f"Generating… {len(''.join(raw_chunks))} chars")
        placeholder.empty()
        raw = "".join(raw_chunks)
        clean = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        placeholder.empty()
        st.error("Claude returned non-JSON. Try rephrasing your input.")
        return None
    except Exception as e:
        placeholder.empty()
        st.error(f"API error: {e}")
        return None

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_gen, tab_explain, tab_debug = st.tabs([
    "⚡ Generate Expression",
    "🔍 Explain This Calc",
    "🔧 LOD Debugger",
])

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — GENERATE
# ════════════════════════════════════════════════════════════════════════════════
with tab_gen:
    EXAMPLES = [
        "Show me revenue this year vs same period last year",
        "Flag customers who bought in Q1 but not Q2",
        "Rolling 3-month average sales by region",
        "% of total profit each category contributes",
        "Rank reps by sales within each region",
    ]
    ex_cols = st.columns(len(EXAMPLES))
    selected_example = None
    for i, ex in enumerate(EXAMPLES):
        with ex_cols[i]:
            if st.button(ex, key=f"ex_{i}", use_container_width=True):
                selected_example = ex

    # Handle history replay
    if "replay" in st.session_state:
        st.session_state.gen_result = st.session_state.replay["r"]
        st.session_state.current_q = st.session_state.replay["q"]
        del st.session_state.replay

    default_q = selected_example or st.session_state.get("current_q", "")
    question = st.text_area(
        "Your question",
        value=default_q,
        placeholder="e.g. Show me rolling 3-month average sales by region",
        height=80,
        label_visibility="collapsed",
    )
    st.session_state.current_q = question

    if st.button("Generate Expression →", type="primary", key="gen_btn"):
        valid = [f for f in st.session_state.fields if f["name"].strip()]
        if not valid:
            st.warning("Add at least one field to your schema first.")
        elif not question.strip():
            st.warning("Describe what you want to calculate.")
        else:
            client = get_client()
            if client:
                system_prompt = build_system_prompt(valid, st.session_state.domain)
                system_blocks, messages = build_messages_with_cache(system_prompt, question)
                result = stream_and_parse(client, system_blocks, messages)
                if result:
                    st.session_state.gen_result = result
                    st.session_state.history.insert(0, {"q": question, "r": result})
                    st.session_state.history = st.session_state.history[:5]

    # ── Render generate result ─────────────────────────────────────────────────
    def render_generate(r: dict) -> None:
        bg, color, border = BADGE_STYLES.get(r["expression_type"], ("#1e293b", "#94a3b8", "#475569"))
        comp_color = COMPLEXITY_COLOR.get(r.get("complexity_rating", ""), "#334155")

        st.markdown(
            f'<div class="result-card">'
            f'<div class="result-card-accent" style="background:linear-gradient(90deg,{border},{bg});"></div>'
            f'<div class="result-card-body">',
            unsafe_allow_html=True,
        )
        # Header: type badge + field name + complexity
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:20px;">'
            f'<span class="badge" style="background:{bg};color:{color};border-color:{border};">'
            f'{r["expression_type"]}</span>'
            f'<span class="field-pill">[{r["field_name"]}]</span>'
            f'<span style="color:{comp_color};font-size:11px;font-weight:700;'
            f'letter-spacing:0.05em;margin-left:auto;text-transform:uppercase;">'
            f'● {r.get("complexity_rating","")}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="section-label">Calculated Field</div>', unsafe_allow_html=True)
        st.code(r["primary_expression"], language="sql")

        st.markdown('<div class="section-label" style="margin-top:18px;">Why this works</div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="card-body-text">{r["explanation"]}</div>', unsafe_allow_html=True)

        if r.get("performance_notes"):
            st.markdown('<div class="section-label" style="margin-top:18px;">⚡ Performance</div>',
                        unsafe_allow_html=True)
            st.markdown(f'<div class="perf-box">{r["performance_notes"]}</div>', unsafe_allow_html=True)

        if r.get("edge_case_warnings"):
            st.markdown('<div class="section-label" style="margin-top:18px;">⚠️ Watch out for</div>',
                        unsafe_allow_html=True)
            for w in r["edge_case_warnings"]:
                st.markdown(f'<div class="warn-box">▸ {w}</div>', unsafe_allow_html=True)

        if r.get("alternative_expression"):
            st.markdown('<div class="section-label" style="margin-top:18px;">🔁 Alternative</div>',
                        unsafe_allow_html=True)
            st.code(r["alternative_expression"], language="sql")
            if r.get("alternative_tradeoff"):
                st.markdown(f'<div class="alt-tradeoff">{r["alternative_tradeoff"]}</div>',
                            unsafe_allow_html=True)

        if r.get("teach_me"):
            st.markdown('<div class="section-label" style="margin-top:18px;">💡 Principle</div>',
                        unsafe_allow_html=True)
            st.markdown(f'<div class="teach-box">"{r["teach_me"]}"</div>', unsafe_allow_html=True)

        st.markdown('</div></div>', unsafe_allow_html=True)

    if st.session_state.gen_result:
        render_generate(st.session_state.gen_result)
    else:
        st.markdown(
            '<div class="empty-state">'
            '<div class="empty-icon">⟨/⟩</div>'
            '<div class="empty-title">Ask a business question</div>'
            '<div class="empty-sub">Set your schema → describe what you want → '
            'get production-ready Tableau syntax with expert warnings</div>'
            '</div>',
            unsafe_allow_html=True,
        )

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — EXPLAIN THIS CALC
# ════════════════════════════════════════════════════════════════════════════════
with tab_explain:
    st.markdown(
        '<div class="mode-desc">'
        'Paste any Tableau calculated field — from a workbook you inherited, Stack Overflow, '
        'or one you wrote yourself. Get a plain-English explanation, quality assessment, '
        'and a refactored version if it can be improved.'
        '</div>',
        unsafe_allow_html=True,
    )

    expression_input = st.text_area(
        "Tableau calculated field",
        placeholder='e.g.  SUM([Sales]) / SUM({FIXED : SUM([Sales])})',
        height=120,
        label_visibility="collapsed",
        key="explain_input",
    )

    if st.button("Explain This →", type="primary", key="explain_btn"):
        if not expression_input.strip():
            st.warning("Paste a calculated field first.")
        else:
            client = get_client()
            if client:
                valid = [f for f in st.session_state.fields if f["name"].strip()]
                system_prompt = build_explain_prompt(valid, st.session_state.domain)
                system_blocks, messages = build_explain_messages(system_prompt, expression_input)
                result = stream_and_parse(client, system_blocks, messages)
                if result:
                    st.session_state.explain_result = result

    # ── Render explain result ──────────────────────────────────────────────────
    def render_explain(r: dict) -> None:
        bg, color, border = BADGE_STYLES.get(r.get("expression_type", "Unknown"),
                                              ("#1e293b", "#94a3b8", "#475569"))
        q_bg, q_color, q_border = QUALITY_STYLES.get(r.get("quality_assessment", ""),
                                                       ("#1e293b", "#94a3b8", "#475569"))

        st.markdown(
            f'<div class="result-card">'
            f'<div class="result-card-accent" style="background:linear-gradient(90deg,{border},{bg});"></div>'
            f'<div class="result-card-body">',
            unsafe_allow_html=True,
        )

        # Header: type + quality badges
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:20px;">'
            f'<span class="badge" style="background:{bg};color:{color};border-color:{border};">'
            f'{r.get("expression_type","")}</span>'
            f'<span class="badge" style="background:{q_bg};color:{q_color};border-color:{q_border};">'
            f'{r.get("quality_assessment","")}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="section-label">What this does</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="plain-english">{r["plain_english"]}</div>', unsafe_allow_html=True)

        if r.get("quality_reason"):
            st.markdown('<div class="section-label" style="margin-top:18px;">Quality assessment</div>',
                        unsafe_allow_html=True)
            st.markdown(f'<div class="card-body-text">{r["quality_reason"]}</div>',
                        unsafe_allow_html=True)

        if r.get("breakdown"):
            st.markdown('<div class="section-label" style="margin-top:18px;">How Tableau evaluates it</div>',
                        unsafe_allow_html=True)
            for i, step in enumerate(r["breakdown"], 1):
                st.markdown(
                    f'<div class="breakdown-step">'
                    f'<span style="color:#334155;font-weight:800;margin-right:10px;">{i}</span>'
                    f'{step}</div>',
                    unsafe_allow_html=True,
                )

        if r.get("refactored_expression"):
            st.markdown('<div class="section-label" style="margin-top:18px;">✨ Refactored version</div>',
                        unsafe_allow_html=True)
            st.code(r["refactored_expression"], language="sql")
            if r.get("refactor_reason"):
                st.markdown(f'<div class="alt-tradeoff">{r["refactor_reason"]}</div>',
                            unsafe_allow_html=True)

        if r.get("warnings"):
            st.markdown('<div class="section-label" style="margin-top:18px;">⚠️ Watch out for</div>',
                        unsafe_allow_html=True)
            for w in r["warnings"]:
                st.markdown(f'<div class="warn-box">▸ {w}</div>', unsafe_allow_html=True)

        if r.get("teach_me"):
            st.markdown('<div class="section-label" style="margin-top:18px;">💡 Principle</div>',
                        unsafe_allow_html=True)
            st.markdown(f'<div class="teach-box">"{r["teach_me"]}"</div>', unsafe_allow_html=True)

        st.markdown('</div></div>', unsafe_allow_html=True)

    if st.session_state.explain_result:
        render_explain(st.session_state.explain_result)
    else:
        st.markdown(
            '<div class="empty-state">'
            '<div class="empty-icon">🔍</div>'
            '<div class="empty-title">Paste any Tableau expression</div>'
            '<div class="empty-sub">Inherited a workbook? Found something online? '
            'Get a plain-English breakdown, quality rating, and a fix if it needs one.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — LOD DEBUGGER
# ════════════════════════════════════════════════════════════════════════════════
with tab_debug:
    st.markdown(
        '<div class="mode-desc">'
        'Your expression is running but returning wrong numbers. '
        "Describe what you're seeing vs what you expected — "
        'get an exact diagnosis and a corrected expression.'
        '</div>',
        unsafe_allow_html=True,
    )

    debug_expression = st.text_area(
        "Your calculated field",
        placeholder='e.g.  SUM([Sales]) / SUM({FIXED : SUM([Sales])})',
        height=100,
        label_visibility="collapsed",
        key="debug_expr",
    )

    col_actual, col_expected = st.columns(2)
    with col_actual:
        st.markdown('<div class="section-label">What it actually returns</div>', unsafe_allow_html=True)
        actual_val = st.text_input(
            "actual",
            placeholder='e.g. "42% for every region" or "all nulls"',
            label_visibility="collapsed",
            key="debug_actual",
        )
    with col_expected:
        st.markdown('<div class="section-label">What you expected</div>', unsafe_allow_html=True)
        expected_val = st.text_input(
            "expected",
            placeholder='e.g. "percentages that add up to 100% for visible regions"',
            label_visibility="collapsed",
            key="debug_expected",
        )

    debug_context = st.text_area(
        "Additional context (optional)",
        placeholder="Describe your filter setup, which dimensions are on the viz, extract vs live, etc.",
        height=70,
        label_visibility="collapsed",
        key="debug_context",
    )

    if st.button("Diagnose →", type="primary", key="debug_btn"):
        if not debug_expression.strip():
            st.warning("Paste your calculated field first.")
        elif not actual_val.strip() or not expected_val.strip():
            st.warning("Fill in both what it returns and what you expected.")
        else:
            client = get_client()
            if client:
                valid = [f for f in st.session_state.fields if f["name"].strip()]
                system_prompt = build_debug_prompt(valid, st.session_state.domain)
                system_blocks, messages = build_debug_messages(
                    system_prompt,
                    debug_expression,
                    actual_val,
                    expected_val,
                    debug_context,
                )
                result = stream_and_parse(client, system_blocks, messages)
                if result:
                    st.session_state.debug_result = result

    # ── Render debug result ────────────────────────────────────────────────────
    def render_debug(r: dict) -> None:
        st.markdown(
            '<div class="result-card">'
            '<div class="result-card-accent" style="background:linear-gradient(90deg,#dc2626,#7c3aed);"></div>'
            '<div class="result-card-body">',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="section-label">Root cause</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="diagnosis-box">🎯 {r["root_cause"]}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-label" style="margin-top:18px;">Why this happens</div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="card-body-text">{r["diagnosis"]}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-label" style="margin-top:18px;">✅ Fixed expression</div>',
                    unsafe_allow_html=True)
        st.code(r["fix"], language="sql")

        if r.get("fix_explanation"):
            st.markdown(f'<div class="fix-box">{r["fix_explanation"]}</div>', unsafe_allow_html=True)

        if r.get("how_to_verify"):
            st.markdown('<div class="section-label" style="margin-top:18px;">🧪 How to verify</div>',
                        unsafe_allow_html=True)
            st.markdown(f'<div class="verify-box">{r["how_to_verify"]}</div>', unsafe_allow_html=True)

        if r.get("teach_me"):
            st.markdown('<div class="section-label" style="margin-top:18px;">💡 Principle</div>',
                        unsafe_allow_html=True)
            st.markdown(f'<div class="teach-box">"{r["teach_me"]}"</div>', unsafe_allow_html=True)

        st.markdown('</div></div>', unsafe_allow_html=True)

    if st.session_state.debug_result:
        render_debug(st.session_state.debug_result)
    else:
        st.markdown(
            '<div class="empty-state">'
            '<div class="empty-icon">🔧</div>'
            '<div class="empty-title">Paste your broken expression</div>'
            '<div class="empty-sub">Describe what it returns vs what you expected — '
            'get an exact root cause and a corrected expression.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="text-align:center;padding:24px 0;color:#334155;font-size:11px;margin-top:40px;">'
    'Built with Claude · '
    '<a href="https://github.com/vaishalizilpe/delod" style="color:#475569;">GitHub</a>'
    '</div>',
    unsafe_allow_html=True,
)
