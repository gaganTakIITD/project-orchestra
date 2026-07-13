"""Scope Guard — flag discussion messages that drift from the frozen Charter.

AI proposes {scope_drift, reason} only. The DiscussionService sets
``scope_flagged`` / ``message_type``; Charter and OutcomeSpec are never mutated.
Fixture mode uses keyword heuristics when Gemini is off or fails.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from app.ai.fixtures.scope_guard import classify_fixture
from app.config import settings

SCOPE_SYSTEM_INSTRUCTION = """You are Orchestra's Scope Guard agent.

A client or worker posted a message in a task discussion thread. The Charter for
this task is frozen. Decide whether the message requests scope drift — new
deliverables, replacements, price changes, or timeline changes outside the
charter. Clarifications that stay within scope are NOT drift.

Return ONLY the JSON object described by the response schema."""


class GeminiScopeGuard(BaseModel):
    """Structured Scope Guard output from Gemini Flash."""

    scope_drift: bool = False
    reason: str = ""
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


@dataclass
class ScopeGuardResult:
    """Classification proposal — AI proposes; DiscussionService applies flags."""

    scope_drift: bool
    reason: str
    source: str  # "gemini" | "fixture"
    model: str | None = None
    latency_ms: int = 0
    confidence: float | None = None
    error: str | None = None
    raw_response: str | None = None


def summarize_charter(
    *,
    task_title: str = "",
    task_description: str = "",
    snapshot: dict[str, Any] | None = None,
) -> str:
    """Compact charter context for the classifier."""
    snap = snapshot or {}
    parts = [
        f"Task: {task_title}" if task_title else "",
        f"Description: {task_description}" if task_description else "",
        f"Scope: {snap.get('scope') or ''}" if snap.get("scope") else "",
        (
            f"Out of scope: {', '.join(str(x) for x in (snap.get('out_of_scope') or []))}"
            if snap.get("out_of_scope")
            else ""
        ),
        f"Price: {snap.get('price')}" if snap.get("price") is not None else "",
        f"Deadline: {snap.get('deadline')}" if snap.get("deadline") else "",
    ]
    return " | ".join(p for p in parts if p) or "No charter summary available."


def classify(message: str, charter_summary: str) -> ScopeGuardResult:
    """Classify whether ``message`` drifts from ``charter_summary``.

    Uses Gemini Flash when enabled; otherwise fixture keyword heuristics.
    Soft-falls back to fixture on Gemini errors so discussion posts never fail.
    """
    if not settings.gemini_enabled:
        return _from_fixture(message, charter_summary)

    try:
        return _gemini_classify(message=message, charter_summary=charter_summary)
    except Exception as exc:
        result = _from_fixture(message, charter_summary)
        result.error = f"gemini_fallback: {type(exc).__name__}: {exc}"
        return result


def _from_fixture(message: str, charter_summary: str) -> ScopeGuardResult:
    raw = classify_fixture(message, charter_summary)
    return ScopeGuardResult(
        scope_drift=bool(raw["scope_drift"]),
        reason=str(raw["reason"]),
        source="fixture",
        confidence=0.9 if raw["scope_drift"] else 0.85,
    )


def _gemini_classify(*, message: str, charter_summary: str) -> ScopeGuardResult:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = {
        "charter_summary": charter_summary,
        "message": message,
    }

    started = time.perf_counter()
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=(
                            "Classify whether this discussion message drifts from "
                            "the frozen charter.\n\n"
                            f"{json.dumps(prompt, default=str)}"
                        )
                    )
                ],
            )
        ],
        config=types.GenerateContentConfig(
            system_instruction=SCOPE_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=GeminiScopeGuard,
            temperature=0.1,
        ),
    )
    latency_ms = int((time.perf_counter() - started) * 1000)

    raw = response.text or "{}"
    parsed = getattr(response, "parsed", None)
    result = (
        parsed
        if isinstance(parsed, GeminiScopeGuard)
        else GeminiScopeGuard.model_validate_json(raw)
    )
    reason = (result.reason or "").strip() or (
        "Gemini flagged scope drift."
        if result.scope_drift
        else "Gemini found no scope drift."
    )
    return ScopeGuardResult(
        scope_drift=bool(result.scope_drift),
        reason=reason,
        source="gemini",
        model=settings.gemini_model,
        latency_ms=latency_ms,
        confidence=float(result.confidence),
        raw_response=raw[:8000],
    )
