"""Schema completeness + fixture extraction for scope chat."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# Schema-driven questions — AI asks only for gaps (docs/CHAT_SURFACES.md).
FIELD_QUESTIONS: dict[str, str] = {
    "outcome_statement": (
        "What outcome do you need delivered? Describe the result — brand, landing page, "
        "app feature — not the tasks to perform."
    ),
    "deliverables": (
        "What should we deliver? For example: logo (SVG+PNG), brand guide, Figma UI, live website URL."
    ),
    "acceptance_criteria": (
        "How will we know it's done? Any quality bars — mobile performance, file formats, visual tone?"
    ),
    "in_scope": "What's included in this package?",
    "out_of_scope": "What should we explicitly leave out?",
    "company_context": "What's your company or product name, and what problem does it solve?",
    "client_inputs": (
        "What can you provide — tagline, reference websites, existing logo or brand assets?"
    ),
    "workflow_summary": "Does this workflow look right, or should we change the order of steps?",
}

WORKFLOW_BY_TASK_TYPES = (
    "Brand direction → Logo design → UI design in Figma → Build landing page → Deploy to live URL"
)

EMPTY_DRAFT: dict[str, Any] = {
    "outcome_statement": "",
    "deliverables": [],
    "acceptance_criteria": [],
    "in_scope": [],
    "out_of_scope": [],
    "assumptions": [],
    "client_inputs_required": [],
    "mapped_task_types": [],
    "risk_tier": "L1",
    "workflow_summary": "",
    "sku_id": None,
    "version": 0,
}

LAUNCH_STUDIO_DRAFT: dict[str, Any] = {
    "deliverables": [
        {"name": "Logo", "format": "SVG + PNG", "required": True},
        {"name": "Brand guide", "format": "PDF", "required": True},
        {"name": "Figma UI", "format": "Figma link", "required": True},
        {"name": "Live landing page", "format": "URL", "required": True},
    ],
    "acceptance_criteria": [
        {
            "criterion": "Logo delivered in SVG and PNG",
            "check_type": "deterministic",
            "rule": "files_include_format(['svg','png'])",
        },
        {
            "criterion": "Landing page loads under 3s on mobile",
            "check_type": "deterministic",
            "rule": "lighthouse_performance >= 70",
        },
        {
            "criterion": "Visual design matches requested tone",
            "check_type": "ai_judged",
            "rubric": "Professional, trustworthy, accessible contrast.",
        },
        {
            "criterion": "Page is responsive on mobile and desktop",
            "check_type": "deterministic",
            "rule": "responsive_check_pass",
        },
    ],
    "in_scope": ["Brand identity", "1 landing page", "2 revision rounds"],
    "out_of_scope": ["CMS", "SEO", "Content writing", "Mobile app"],
    "assumptions": ["Client provides company name and tagline"],
    "client_inputs_required": ["company_name", "tagline", "reference_sites"],
    "mapped_task_types": [
        "brand_identity",
        "logo_design",
        "figma_ui_design",
        "landing_page_frontend",
        "deployment_devops",
    ],
    "workflow_summary": WORKFLOW_BY_TASK_TYPES,
}


def empty_draft() -> dict[str, Any]:
    return deepcopy(EMPTY_DRAFT)


def assess_completeness(draft: dict[str, Any], conversation_text: str) -> tuple[int, list[str], bool]:
    """Return (pct, missing_fields, ready_for_quote)."""
    missing: list[str] = []
    text = conversation_text.lower()

    if not draft.get("outcome_statement") or len(str(draft["outcome_statement"])) < 20:
        missing.append("outcome_statement")
    if not draft.get("deliverables"):
        missing.append("deliverables")
    if not draft.get("acceptance_criteria"):
        missing.append("acceptance_criteria")
    if not draft.get("in_scope"):
        missing.append("in_scope")
    if not draft.get("out_of_scope"):
        missing.append("out_of_scope")

    has_company = any(
        k in text
        for k in ("startup", "company", "product", "health", "fintech", "saas", "healthtrack")
    )
    if not has_company and not draft.get("client_inputs_required"):
        missing.append("company_context")

    has_inputs = any(k in text for k in ("tagline", "reference", "logo file", "brand asset"))
    inputs = draft.get("client_inputs_required") or []
    if not has_inputs and "tagline" not in inputs:
        missing.append("client_inputs")

    if not draft.get("workflow_summary"):
        missing.append("workflow_summary")

    total_checks = 8
    pct = round(((total_checks - len(missing)) / total_checks) * 100)
    ready = len(missing) == 0 and pct >= 85
    return pct, missing, ready


def next_question(missing_fields: list[str]) -> str:
    if not missing_fields:
        return (
            "Your job description looks complete. Review the panel — when you're ready, "
            "click **Get my quote**."
        )
    key = missing_fields[0]
    return FIELD_QUESTIONS.get(
        key,
        "Tell me a bit more so I can finish your job description before we quote.",
    )


def extract_from_message(draft: dict[str, Any], user_message: str, all_user_text: str) -> dict[str, Any]:
    """Merge user utterance into spec draft (fixture — replace with Gemini JSON mode)."""
    out = deepcopy(draft)
    out["version"] = int(out.get("version", 0)) + 1
    text = user_message.strip()
    lower = text.lower()

    if _is_too_vague(lower):
        return out

    if len(text) >= 8:
        out["outcome_statement"] = text[:800]

    if any(k in lower for k in ("brand", "landing", "website", "logo", "health", "page")) or (
        "startup" in lower and len(lower.split()) >= 12
    ):
        for k, v in LAUNCH_STUDIO_DRAFT.items():
            if k != "workflow_summary" or not out.get("workflow_summary"):
                out[k] = deepcopy(v)

    if "healthtrack" in lower or "health track" in lower:
        out["outcome_statement"] = (
            "Launch-ready brand identity and responsive landing page for HealthTrack — "
            "chronic condition tracking with a trustworthy, modern healthcare tone."
        )

    if any(k in lower for k in ("trust", "healthcare", "medical", "clinical")):
        for ac in out.get("acceptance_criteria", []):
            if ac.get("check_type") == "ai_judged":
                ac["rubric"] = "Professional, calm healthcare tone; clear hierarchy; accessible contrast."

    if "tagline" in lower or "reference" in lower:
        out["client_inputs_required"] = ["company_name", "tagline", "reference_sites"]

    if not out.get("workflow_summary") and out.get("mapped_task_types"):
        out["workflow_summary"] = WORKFLOW_BY_TASK_TYPES

    return out


def _is_too_vague(lower: str) -> bool:
    vague = (
        "create my startup",
        "build my startup",
        "make my startup",
        "create a startup",
        "help with my startup",
    )
    return any(v in lower for v in vague) and len(lower.split()) < 12


def opening_assistant_message() -> str:
    return (
        "What outcome do you need delivered? Describe the result you want — "
        "for example a brand and landing page for your startup. I'll build a detailed "
        "job description and ask only what's still missing."
    )


def reply_for_turn(
    *,
    user_message: str,
    draft: dict[str, Any],
    missing: list[str],
    completeness_pct: int,
    ready: bool,
) -> str:
    lower = user_message.lower()
    if _is_too_vague(lower):
        return (
            "I can help — but \"create my startup\" isn't enough to build from yet. "
            "Are you looking for brand identity, a landing page, or a full launch package? "
            "What does your startup do?"
        )
    if ready:
        return next_question([])
    return f"Got it — your job description is about {completeness_pct}% complete. {next_question(missing)}"
