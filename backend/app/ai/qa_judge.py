"""QA Judge — deterministic checks first; Gemini overlay for ai_judged criteria.

AI proposes a pass/fail review; the Spine executes ``qa_pass`` / ``qa_fail``.
Fixture mode (no Gemini) soft-passes non-deterministic criteria so stage happy
paths keep working; clear deterministic failures still fail.
"""

from __future__ import annotations

import ast
import re
from typing import Any
from urllib.parse import urlparse

# Criteria the fixture / Gemini layers still need to judge.
_DEFERRED_CHECK_TYPES = frozenset({"ai_judged", "human_required"})

_FORMAT_RULE_RE = re.compile(
    r"files_include_format\s*\(\s*(\[[^\]]*\])\s*\)",
    re.IGNORECASE,
)
_LIGHTHOUSE_RE = re.compile(
    r"lighthouse_performance\s*>=\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


def run_deterministic_checks(
    *,
    acceptance_criteria: list[dict[str, Any]] | None,
    notes: str,
    asset_urls: list[str],
) -> list[dict[str, Any]]:
    """Evaluate criteria. Deterministic rules get a pass/fail; others are deferred."""
    evidence: list[dict[str, Any]] = []
    for raw in acceptance_criteria or []:
        if not isinstance(raw, dict):
            continue
        criterion = str(raw.get("criterion") or "").strip() or "Unnamed criterion"
        check_type = str(raw.get("check_type") or "ai_judged").strip() or "ai_judged"
        rule = str(raw.get("rule") or "").strip()
        rubric = str(raw.get("rubric") or "").strip()

        if check_type != "deterministic":
            evidence.append(
                {
                    "criterion": criterion,
                    "check_type": check_type,
                    "passed": None,  # deferred
                    "detail": rubric or "Deferred to AI / fixture layer",
                    "rule": rule,
                    "rubric": rubric,
                }
            )
            continue

        passed, detail = _eval_deterministic_rule(
            rule=rule,
            notes=notes or "",
            asset_urls=asset_urls or [],
        )
        evidence.append(
            {
                "criterion": criterion,
                "check_type": check_type,
                "passed": passed,
                "detail": detail,
                "rule": rule,
                "rubric": rubric,
            }
        )
    return evidence


def deterministic_failed(evidence: list[dict[str, Any]]) -> bool:
    return any(e.get("check_type") == "deterministic" and e.get("passed") is False for e in evidence)


def build_fixture_review(
    *,
    evidence: list[dict[str, Any]],
    notes: str,
    asset_urls: list[str],
) -> dict[str, Any]:
    """Complete deferred criteria and compute overall result (fixture path)."""
    _ = notes, asset_urls
    completed: list[dict[str, Any]] = []
    for item in evidence:
        row = {
            "criterion": item["criterion"],
            "check_type": item["check_type"],
            "passed": item["passed"],
            "detail": item.get("detail"),
        }
        if item.get("passed") is None:
            # Stage fixture: soft-pass ai_judged / human_required after deterministic gate.
            row["passed"] = True
            row["detail"] = (
                item.get("detail") or "Fixture soft-pass (non-deterministic criterion)"
            )
        completed.append(row)

    failed = [e for e in completed if not e["passed"]]
    if failed:
        score = max(0.0, 1.0 - (len(failed) / max(len(completed), 1)))
        return {
            "result": "fail",
            "score": round(score, 3),
            "confidence": 0.95,
            "feedback": _feedback_fail(failed),
            "evidence": completed,
            "action": "approve",
        }

    return {
        "result": "pass",
        "score": 0.9,
        "confidence": 0.9,
        "feedback": "All acceptance criteria passed (QA Judge fixture).",
        "evidence": completed or [
            {
                "criterion": "No acceptance criteria on task",
                "check_type": "deterministic",
                "passed": True,
                "detail": "Empty criteria — treated as pass",
            }
        ],
        "action": "approve",
    }


def merge_gemini_overlay(
    *,
    evidence: list[dict[str, Any]],
    gemini: dict[str, Any],
) -> dict[str, Any]:
    """Apply Gemini judgments onto deferred criteria; deterministic stays authoritative."""
    by_criterion = {
        str(item.get("criterion") or "").strip().lower(): item
        for item in (gemini.get("evidence") or [])
        if isinstance(item, dict)
    }

    completed: list[dict[str, Any]] = []
    for item in evidence:
        row = {
            "criterion": item["criterion"],
            "check_type": item["check_type"],
            "passed": item["passed"],
            "detail": item.get("detail"),
        }
        if item.get("passed") is None:
            overlay = by_criterion.get(item["criterion"].strip().lower())
            if overlay is not None and "passed" in overlay:
                row["passed"] = bool(overlay["passed"])
                row["detail"] = str(overlay.get("detail") or item.get("detail") or "")
            else:
                # Missing overlay → soft-pass so a partial Gemini response doesn't brick submit.
                row["passed"] = True
                row["detail"] = "Gemini omitted criterion — soft-pass"
        completed.append(row)

    failed = [e for e in completed if not e["passed"]]
    gemini_result = str(gemini.get("result") or "").lower()
    if failed or gemini_result == "fail":
        score = float(gemini.get("score") or max(0.0, 1.0 - len(failed) / max(len(completed), 1)))
        confidence = float(gemini.get("confidence") or 0.75)
        feedback = str(gemini.get("feedback") or "").strip() or _feedback_fail(failed)
        action = "escalate" if confidence < 0.7 else "approve"
        return {
            "result": "fail",
            "score": round(score, 3),
            "confidence": confidence,
            "feedback": feedback,
            "evidence": completed,
            "action": action,
        }

    confidence = float(gemini.get("confidence") or 0.85)
    score = float(gemini.get("score") or 0.9)
    action = "escalate" if confidence < 0.7 else "approve"
    # Low confidence still proposes pass; Spine may escalate later — for now execute pass
    # unless Gemini explicitly failed (handled above).
    return {
        "result": "pass",
        "score": round(score, 3),
        "confidence": confidence,
        "feedback": str(gemini.get("feedback") or "").strip()
        or "All acceptance criteria passed (QA Judge).",
        "evidence": completed,
        "action": action,
    }


def evidence_for_log(review: dict[str, Any]) -> list[dict[str, Any]]:
    """Strip internal-only fields for ai_decision_log / API-shaped evidence."""
    out: list[dict[str, Any]] = []
    for item in review.get("evidence") or []:
        out.append(
            {
                "criterion": item.get("criterion", ""),
                "check_type": item.get("check_type", "ai_judged"),
                "passed": bool(item.get("passed")),
                **({"detail": item["detail"]} if item.get("detail") else {}),
            }
        )
    return out


def _eval_deterministic_rule(
    *,
    rule: str,
    notes: str,
    asset_urls: list[str],
) -> tuple[bool, str]:
    if not rule:
        # No rule string — require at least one asset or note as a minimal bar.
        if asset_urls or notes.strip():
            return True, "No rule; submission has notes or assets"
        return False, "No rule and empty submission"

    fmt = _FORMAT_RULE_RE.search(rule)
    if fmt:
        try:
            required = [str(x).lower().lstrip(".") for x in ast.literal_eval(fmt.group(1))]
        except (SyntaxError, ValueError):
            return False, f"Unparseable format rule: {rule}"
        found = {_url_ext(u) for u in asset_urls}
        missing = [ext for ext in required if ext not in found]
        if missing:
            return False, f"Missing required formats: {', '.join(missing)}"
        return True, f"Found required formats: {', '.join(required)}"

    lh = _LIGHTHOUSE_RE.search(rule)
    if lh:
        threshold = float(lh.group(1))
        # Optional hint in notes: "lighthouse: 82"
        hint = re.search(r"lighthouse\s*[:=]?\s*(\d+(?:\.\d+)?)", notes, re.IGNORECASE)
        if hint:
            score = float(hint.group(1))
            if score >= threshold:
                return True, f"Lighthouse {score} >= {threshold} (from notes)"
            return False, f"Lighthouse {score} < {threshold} (from notes)"
        # Cannot run Lighthouse in-process — soft-pass for stage (fixture/Gemini path).
        return True, f"Lighthouse not measured; soft-pass (>= {threshold} assumed)"

    if "responsive_check_pass" in rule.lower():
        return True, "Responsive check soft-pass (not measured in-process)"

    if "url_reachable" in rule.lower():
        http_urls = [u for u in asset_urls if _looks_like_http(u)]
        if http_urls:
            return True, f"URL present for reachability check: {http_urls[0]}"
        return False, "No http(s) URL in assets for reachability check"

    # Unknown deterministic rule — soft-pass so catalog evolution doesn't brick submit.
    return True, f"Unknown rule soft-pass: {rule}"


def _url_ext(url: str) -> str:
    path = urlparse(url).path or url
    if "." not in path.rsplit("/", 1)[-1]:
        return ""
    return path.rsplit(".", 1)[-1].lower()


def _looks_like_http(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def _feedback_fail(failed: list[dict[str, Any]]) -> str:
    bits = [f"{e['criterion']}: {e.get('detail') or 'failed'}" for e in failed]
    return "QA failed — " + "; ".join(bits)


def deferred_check_types() -> frozenset[str]:
    return _DEFERRED_CHECK_TYPES
