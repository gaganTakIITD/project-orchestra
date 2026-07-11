"""Fixture-first Spec Compiler — no Gemini key required."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone


def compile_spec_fixture(
    *,
    intent_id: uuid.UUID,
    sku_id: uuid.UUID,
    raw_text: str,
) -> dict:
    """Return OutcomeSpec-shaped fields for MVP bind gate #2."""
    _ = raw_text  # reserved for future Gemini scoping
    return {
        "intent_id": intent_id,
        "sku_id": sku_id,
        "outcome_statement": "Launch-ready brand identity and responsive landing page.",
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
                "criterion": "Visual design matches a trustworthy, modern tone",
                "check_type": "ai_judged",
                "rubric": "Professional, calm palette; clear hierarchy; accessible contrast.",
            },
            {
                "criterion": "Page is responsive on mobile and desktop",
                "check_type": "deterministic",
                "rule": "responsive_check_pass",
            },
        ],
        "in_scope": ["1 landing page", "2 revision rounds", "Logo + brand guide"],
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
        "risk_tier": "L1",
        "version": 1,
        "frozen_at": None,
    }


def quote_from_sku(*, sku_base_price: float, typical_days: int, revision_limit: int) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "price": sku_base_price,
        "deadline": now + timedelta(days=typical_days),
        "revision_limit": revision_limit,
        "valid_until": now + timedelta(days=7),
        "ai_confidence": 0.88,
        "ai_rationale": "Standard Launch Studio scope; effort within typical band for 5-task DAG.",
    }
