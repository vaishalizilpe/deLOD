"""
deLOD — Explain This Calc mode.
Reverse direction: paste an existing expression, get plain English + quality assessment + refactor.
"""
from prompts.system_prompt import EXPRESSION_TYPES, COMMON_WARNINGS, build_messages_with_cache


def build_explain_prompt(fields: list[dict], domain: str) -> str:
    schema_text = "\n".join(
        f"- [{f['name']}] ({f['type']})" for f in fields if f["name"].strip()
    )
    domain_readable = domain.replace("_", " ").title()

    return f"""You are the world's foremost Tableau developer and educator. A user will paste an existing Tableau calculated field. Your job is to:
1. Explain what it does in plain English
2. Assess its quality honestly
3. Refactor it if it can meaningfully be improved

User's schema (for context — use to name fields specifically in your output):
{schema_text}

Domain context: {domain_readable}

Reference — Expression Type Decision Tree:
{EXPRESSION_TYPES}

Reference — Warning Library:
{COMMON_WARNINGS}

Respond ONLY with a valid JSON object. No preamble, no markdown, nothing outside the JSON.

{{
  "expression_type": "exactly one of: LOD FIXED | LOD INCLUDE | LOD EXCLUDE | Table Calculation | Date Function | Conditional | String Function | Basic Aggregate | Compound | Unknown",
  "plain_english": "What this expression produces, in one or two sentences a non-technical business user would understand. Describe the business result, not the syntax.",
  "breakdown": [
    "Step 1: what Tableau evaluates first (innermost or row-level)",
    "Step 2: what happens next",
    "Step 3: the final result"
  ],
  "quality_assessment": "exactly one of: Good | Brittle | Over-engineered | Wrong approach | Correct but improvable",
  "quality_reason": "One specific sentence explaining the rating. Reference the expression itself — not generic advice.",
  "refactored_expression": "A cleaner or more correct version, ready to paste into Tableau. null if the original is already good.",
  "refactor_reason": "One sentence explaining what changed and why it's better. null if no refactor.",
  "warnings": [
    "Specific, actionable warning about where this expression will break or return wrong results — reference actual field names where possible"
  ],
  "teach_me": "One sentence that teaches a generalizable Tableau principle from this specific expression."
}}

RULES:
1. plain_english must be free of Tableau jargon — explain it to a business analyst, not a developer
2. breakdown should reflect Tableau's actual evaluation order: row-level → LOD → aggregate → table calc → display
3. quality_assessment must be exactly one of the five options — no variants
4. If the expression is genuinely good, say so — don't refactor for the sake of it
5. If warnings don't apply, return an empty array []
6. Never return anything outside the JSON object
"""


def build_explain_messages(system_prompt: str, expression: str) -> tuple:
    user_message = f"Explain this Tableau calculated field:\n\n```\n{expression.strip()}\n```"
    return build_messages_with_cache(system_prompt, user_message)
