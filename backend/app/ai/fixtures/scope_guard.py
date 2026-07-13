"""Fixture Scope Guard — keyword heuristics when Gemini is unavailable."""

from __future__ import annotations

import re

# (pattern, reason) — first match wins.
_DRIFT_HEURISTICS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\balso\s+add\b", re.IGNORECASE),
        "Message requests adding work outside the frozen charter (also add…).",
    ),
    (
        re.compile(r"\binstead\s+of\b", re.IGNORECASE),
        "Message proposes replacing scoped deliverables (instead of…).",
    ),
    (
        re.compile(
            r"\b(more|extra|additional)\s+(budget|money|payment|pay|cost|price|fee)\b",
            re.IGNORECASE,
        ),
        "Message expands price / budget beyond the charter.",
    ),
    (
        re.compile(
            r"\b(increase|raise|bump)\s+(the\s+)?(budget|price|fee|cost|payment)\b",
            re.IGNORECASE,
        ),
        "Message expands price / budget beyond the charter.",
    ),
    (
        re.compile(
            r"\b(extend|push|delay)\s+(the\s+)?(deadline|due\s+date|timeline)\b",
            re.IGNORECASE,
        ),
        "Message expands time / deadline beyond the charter.",
    ),
    (
        re.compile(
            r"\b(more|extra|additional)\s+(time|days?|weeks?|hours?)\b",
            re.IGNORECASE,
        ),
        "Message expands time beyond the charter.",
    ),
    (
        re.compile(r"\bneed\s+(it\s+)?(sooner|faster|earlier)\b", re.IGNORECASE),
        "Message compresses the charter timeline.",
    ),
    (
        re.compile(r"\brush\s+(this|job|task|delivery)?\b", re.IGNORECASE),
        "Message requests a rush outside the agreed timeline.",
    ),
]


def classify_fixture(message: str, charter_summary: str = "") -> dict[str, str | bool]:
    """Return {scope_drift, reason} from keyword heuristics (charter_summary unused)."""
    _ = charter_summary
    text = (message or "").strip()
    if not text:
        return {
            "scope_drift": False,
            "reason": "Empty message — no scope drift detected.",
        }

    for pattern, reason in _DRIFT_HEURISTICS:
        if pattern.search(text):
            return {"scope_drift": True, "reason": reason}

    return {
        "scope_drift": False,
        "reason": "No scope-drift keywords matched (fixture).",
    }
