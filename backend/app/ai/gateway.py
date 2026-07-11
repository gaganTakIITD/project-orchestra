"""AI gateway — Gemini Spec Compiler with a deterministic fixture fallback.

Founder rule: **AI never mutates state.** This module only *proposes* a
structured OutcomeSpec draft plus a natural-language reply. The Spine
(`ChatService`) computes completeness deterministically, validates, and
persists. If no `GEMINI_API_KEY` is configured — or any Gemini call fails —
we transparently degrade to the fixture extractor so the product still runs.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from app.ai import spec_extractor
from app.config import settings

SYSTEM_INSTRUCTION = """You are Orchestra's Spec Compiler.

A client describes an outcome they want delivered in plain language. Your job is
to EXTRACT that into a strict OutcomeSpec — never to chit-chat. The schema is an
interrogation engine: it tells you what MUST be known before we can build.

Rules:
- Extract only what the client actually said or clearly implied. You may propose
  sensible defaults for a package, but frame them as proposals to confirm.
- Ask ONLY about fields that are still missing or ambiguous. One or two crisp
  questions per turn — never a wall of questions.
- Prefer concrete deliverables (name + format) and acceptance criteria that are
  checkable (deterministic rule or an ai_judged rubric).
- `workflow_summary` is the ordered plan of how the outcome gets built.
- Keep `assistant_reply` short, warm, and specific to what you still need.
- risk_tier is one of L1 (low), L2 (medium), L3 (high/regulated).

Return ONLY the JSON object described by the response schema."""


class _Deliverable(BaseModel):
    name: str
    format: str = ""
    required: bool = True


class _AcceptanceCriterion(BaseModel):
    criterion: str
    check_type: str = "ai_judged"  # deterministic | ai_judged
    rule: str = ""
    rubric: str = ""


class GeminiSpec(BaseModel):
    """Structured output contract Gemini fills each turn (mirrors OutcomeSpec)."""

    outcome_statement: str = ""
    deliverables: list[_Deliverable] = Field(default_factory=list)
    acceptance_criteria: list[_AcceptanceCriterion] = Field(default_factory=list)
    in_scope: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    client_inputs_required: list[str] = Field(default_factory=list)
    mapped_task_types: list[str] = Field(default_factory=list)
    risk_tier: str = "L1"
    workflow_summary: str = ""
    assistant_reply: str = ""
    confidence: float = 0.0


@dataclass
class SpecTurn:
    """Result of one scope-chat turn — a *proposal*, not persisted state."""

    draft: dict[str, Any]
    reply: str | None  # None → caller builds a deterministic reply
    source: str  # "gemini" | "fixture"
    model: str | None = None
    latency_ms: int = 0
    confidence: float | None = None
    error: str | None = None
    raw_response: str | None = None


def compile_spec_turn(
    *,
    draft: dict[str, Any],
    user_message: str,
    history: list[dict[str, str]] | None = None,
) -> SpecTurn:
    """Propose an updated spec draft + reply for one client turn."""
    if not settings.gemini_enabled:
        return _fixture_turn(draft, user_message)

    try:
        return _gemini_turn(draft, user_message, history or [])
    except Exception as exc:  # network / quota / parse — degrade, never crash the chat
        turn = _fixture_turn(draft, user_message)
        turn.error = f"gemini_fallback: {type(exc).__name__}: {exc}"
        return turn


def _fixture_turn(draft: dict[str, Any], user_message: str) -> SpecTurn:
    all_text = f"{draft.get('outcome_statement', '')} {user_message}"
    new_draft = spec_extractor.extract_from_message(draft, user_message, all_text)
    return SpecTurn(draft=new_draft, reply=None, source="fixture")


def _gemini_turn(
    draft: dict[str, Any],
    user_message: str,
    history: list[dict[str, str]],
) -> SpecTurn:
    # Imported lazily so the package is optional until a key is configured.
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)

    contents: list[Any] = []
    for msg in history:
        role = "user" if msg.get("role") == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg.get("body", ""))]))
    contents.append(
        types.Content(
            role="user",
            parts=[
                types.Part(
                    text=(
                        f"Current draft (JSON):\n{json.dumps(draft, default=str)}\n\n"
                        f"Client says: {user_message}\n\n"
                        "Update the draft and reply."
                    )
                )
            ],
        )
    )

    started = time.perf_counter()
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=GeminiSpec,
            temperature=0.2,
        ),
    )
    latency_ms = int((time.perf_counter() - started) * 1000)

    raw = response.text or "{}"
    parsed = getattr(response, "parsed", None)
    spec = parsed if isinstance(parsed, GeminiSpec) else GeminiSpec.model_validate_json(raw)
    new_draft = _draft_from_gemini(spec, previous=draft)
    reply = spec.assistant_reply.strip() or None

    return SpecTurn(
        draft=new_draft,
        reply=reply,
        source="gemini",
        model=settings.gemini_model,
        latency_ms=latency_ms,
        confidence=spec.confidence,
        raw_response=raw[:8000],
    )


def _draft_from_gemini(spec: GeminiSpec, *, previous: dict[str, Any]) -> dict[str, Any]:
    """Normalize Gemini output into our strict draft shape (full replace per turn)."""
    out = spec_extractor.empty_draft()
    payload = spec.model_dump()
    for key in out:
        value = payload.get(key)
        if value not in (None, "", []):
            out[key] = value
    if out.get("risk_tier") not in ("L1", "L2", "L3"):
        out["risk_tier"] = "L1"
    out["sku_id"] = previous.get("sku_id")
    out["version"] = int(previous.get("version", 0)) + 1
    return out
