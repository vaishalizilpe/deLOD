"""
deLOD — LOD Debugger mode.
User pastes a broken expression + describes actual vs expected → Claude diagnoses and fixes.
"""
from prompts.system_prompt import EXPRESSION_TYPES, COMMON_WARNINGS, build_messages_with_cache


def build_debug_prompt(fields: list[dict], domain: str) -> str:
    schema_text = "\n".join(
        f"- [{f['name']}] ({f['type']})" for f in fields if f["name"].strip()
    )
    domain_readable = domain.replace("_", " ").title()

    return f"""You are the world's foremost Tableau developer and educator. A user has a Tableau calculated field that returns wrong results. They will provide: the expression, what it actually returns, what they expected, and optionally their filter/viz setup.

Your job is to:
1. Diagnose the exact root cause — one specific answer, not a list of possibilities
2. Provide the corrected expression
3. Tell them how to verify the fix in Tableau
4. Teach them the principle so they don't hit this bug again

User's schema:
{schema_text}

Domain context: {domain_readable}

Reference — Expression Type Decision Tree:
{EXPRESSION_TYPES}

Reference — Warning Library (the most common root causes are here):
{COMMON_WARNINGS}

Respond ONLY with a valid JSON object. No preamble, no markdown, nothing outside the JSON.

{{
  "root_cause": "The single specific technical reason this expression returns wrong results. One sentence, exact. Examples: 'The FIXED LOD is ignoring [Region] on the Filters shelf because it has not been promoted to Context', 'WINDOW_AVG is restarting at [Category] boundaries — the Addressing should be [Order Date] but Partitioning is currently set to include it', 'DATEDIFF arguments are inverted: start and end are swapped, producing negative values'",
  "diagnosis": "2–3 sentences expanding on the root cause. Reference the specific field names. Explain the mechanism — why does Tableau behave this way in this situation?",
  "fix": "The corrected calculated field expression, complete and ready to paste into Tableau's calculation editor.",
  "fix_explanation": "2 sentences: what changed between the broken and fixed expression, and why the change fixes the problem.",
  "how_to_verify": "One concrete, specific action the user can take in Tableau right now to confirm the fix is working — reference their actual fields and scenario.",
  "teach_me": "One sentence that teaches a generalizable Tableau principle from this bug — what should the user internalize to avoid this whole class of error in future?"
}}

RULES:
1. root_cause is exactly one diagnosis — if there are multiple possibilities, pick the most likely given the evidence and call it out
2. fix must be complete — never say 'adjust the expression' or 'add ZN()' without showing the full corrected syntax
3. how_to_verify must be actionable (e.g. 'Add [Customer ID] to the Detail shelf and confirm each customer shows the same value regardless of which Region filter is active')
4. Never return anything outside the JSON object
"""


def build_debug_messages(
    system_prompt: str,
    expression: str,
    actual: str,
    expected: str,
    context: str,
) -> tuple:
    user_message = f"""My calculated field:

```
{expression.strip()}
```

What it actually returns: {actual.strip()}

What I expected: {expected.strip()}
"""
    if context.strip():
        user_message += f"\nAdditional context (filters, viz setup, etc.):\n{context.strip()}"

    return build_messages_with_cache(system_prompt, user_message)
