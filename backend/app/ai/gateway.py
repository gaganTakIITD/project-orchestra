"""AI gateway — Gemini Spec Compiler + Architect + Task Packet + QA Judge.

Founder rule: **AI never mutates state.** This module only *proposes* structured
JSON. The Spine validates and persists. In development, missing/failed Gemini
calls degrade to fixtures. When `gemini_required` (production / REQUIRE_GEMINI),
missing Vertex config and call failures fail loud — no silent fixture for Spec
Compiler, Architect, Task Packet, or QA Judge.

Credit schema: Vertex AI on ``VERTEX_PROJECT=raystartup`` via ADC — never AI Studio
API keys (see ``docs/GCP_BILLING_SPLIT.md``).
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.ai import qa_judge, spec_extractor
from app.ai.architect import (
    ALLOWED_TASK_TYPE_SLUGS,
    InvalidPlanError,
    build_plan_from_spec,
    normalize_mapped_task_types,
    validate_dag,
)
from app.ai.gemini_client import make_gemini_client
from app.ai.task_packet_generator import generate_charter_and_packet as fixture_charter_and_packet
from app.config import settings

_VERTEX_REQUIRED = (
    "GEMINI_AUTH=vertex and VERTEX_PROJECT=raystartup required "
    "(APP_ENV=production or REQUIRE_GEMINI=true). "
    "Do not use GEMINI_API_KEY / AI Studio — see docs/GCP_BILLING_SPLIT.md"
)

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
- Always fill `in_scope`, `out_of_scope`, and `workflow_summary` with sensible
  package defaults when the outcome is clear enough to quote — do not leave them
  empty while asking follow-ups.
- `workflow_summary` is the ordered plan of how the outcome gets built.
- Keep `assistant_reply` short, warm, and specific to what you still need.
- risk_tier is one of L1 (low), L2 (medium), L3 (high/regulated).

Return ONLY the JSON object described by the response schema."""

PACKET_SYSTEM_INSTRUCTION = """You are Orchestra's Task Packet Generator.

Given a frozen OutcomeSpec slice and one Architect task, produce a worker job
card: a short brief and a practical checklist. Do not invent scope that
contradicts the spec. Checklist items should be concrete and checkable.
Return ONLY the JSON object described by the response schema."""

ARCHITECT_SYSTEM_INSTRUCTION = """You are Orchestra's Architect agent.

Given a frozen OutcomeSpec, enrich the fulfillment task DAG: titles,
descriptions, and acceptance criteria for each task. Do not invent task types
outside the allowed catalog. Preserve the given task order and dependency
chain (linear). Keep criteria checkable (deterministic rule or ai_judged rubric).
Return ONLY the JSON object described by the response schema."""

QA_SYSTEM_INSTRUCTION = """You are Orchestra's QA Judge agent.

A worker submitted deliverables against task acceptance criteria. Deterministic
checks already ran; you only judge deferred criteria (ai_judged / human_required
rubrics). Be strict but fair. Score 0–1. Confidence < 0.7 means escalate.
Return ONLY the JSON object described by the response schema."""


class GeminiNotConfiguredError(RuntimeError):
    """Raised when Gemini is required but no API key is set."""


class GeminiCallError(RuntimeError):
    """Raised when Gemini is required and the call fails (no fixture fallback)."""


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


class _ChecklistItem(BaseModel):
    label: str
    required: bool = True


class GeminiPacket(BaseModel):
    """Structured Task Packet proposal from Gemini."""

    brief: str = ""
    scope: str = ""
    checklist: list[_ChecklistItem] = Field(default_factory=list)
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


@dataclass
class PacketProposal:
    """Charter + TaskPacket proposal — AI proposes; Spine freezes Charter."""

    charter: dict[str, Any]
    packet: dict[str, Any]
    source: str  # "gemini" | "fixture"
    model: str | None = None
    latency_ms: int = 0
    confidence: float | None = None
    error: str | None = None
    raw_response: str | None = None


@dataclass
class PlanProposal:
    """Fulfillment DAG proposal — AI proposes; Spine validates + persists."""

    plan: dict[str, Any]
    source: str  # "gemini" | "fixture"
    model: str | None = None
    latency_ms: int = 0
    confidence: float | None = None
    error: str | None = None
    raw_response: str | None = None


@dataclass
class QAProposal:
    """QA review proposal — AI proposes; Spine runs qa_pass / qa_fail."""

    result: str  # pass | fail
    score: float
    confidence: float
    feedback: str
    evidence: list[dict[str, Any]]
    action: str  # approve | escalate
    source: str  # "gemini" | "fixture"
    model: str | None = None
    latency_ms: int = 0
    error: str | None = None
    raw_response: str | None = None


class _PlanCriterion(BaseModel):
    criterion: str
    check_type: str = "human_required"
    rule: str = ""
    rubric: str = ""


class GeminiPlanTask(BaseModel):
    task_type_slug: str
    title: str = ""
    description: str = ""
    acceptance_criteria: list[_PlanCriterion] = Field(default_factory=list)


class GeminiPlan(BaseModel):
    """Structured Architect overlay — enriches fixture skeleton tasks."""

    tasks: list[GeminiPlanTask] = Field(default_factory=list)
    confidence: float = 0.0


class _QAEvidence(BaseModel):
    criterion: str
    check_type: str = "ai_judged"
    passed: bool = True
    detail: str = ""


class GeminiQA(BaseModel):
    """Structured QA Judge overlay for deferred (non-deterministic) criteria."""

    result: str = "pass"  # pass | fail
    score: float = 0.9
    confidence: float = 0.85
    feedback: str = ""
    evidence: list[_QAEvidence] = Field(default_factory=list)


def compile_spec_turn(
    *,
    draft: dict[str, Any],
    user_message: str,
    history: list[dict[str, str]] | None = None,
) -> SpecTurn:
    """Propose an updated spec draft + reply for one client turn."""
    if not settings.gemini_enabled:
        if settings.gemini_required:
            raise GeminiNotConfiguredError(
                f"Vertex Gemini required for Spec Compiler — {_VERTEX_REQUIRED}"
            )
        return _fixture_turn(draft, user_message)

    try:
        return _gemini_turn(draft, user_message, history or [])
    except Exception as exc:  # network / quota / parse
        if settings.gemini_required:
            raise GeminiCallError(
                f"Spec Compiler Gemini call failed: {type(exc).__name__}: {exc}"
            ) from exc
        turn = _fixture_turn(draft, user_message)
        turn.error = f"gemini_fallback: {type(exc).__name__}: {exc}"
        return turn


def generate_plan_proposal(
    *,
    order_id: uuid.UUID,
    order_deadline: datetime,
    revision_limit: int,
    order_price: Decimal | float | None = None,
    spec: dict[str, Any] | None = None,
    force_fixtures: bool = False,
) -> PlanProposal:
    """Propose a fulfillment plan DAG (fixture or Gemini overlay + validate_dag).

    ``force_fixtures`` is used on quote accept so Confirm & begin work returns in
    milliseconds (OutcomeSpec is already Gemini-quality; DAG skeleton is enough).
    """
    spec = spec or {}
    if force_fixtures or not settings.gemini_enabled:
        if not force_fixtures and settings.gemini_required:
            raise GeminiNotConfiguredError(
                f"Vertex Gemini required for Architect — {_VERTEX_REQUIRED}"
            )
        return _fixture_plan(
            order_id=order_id,
            order_deadline=order_deadline,
            revision_limit=revision_limit,
            order_price=order_price,
            spec=spec,
        )

    try:
        return _gemini_plan(
            order_id=order_id,
            order_deadline=order_deadline,
            revision_limit=revision_limit,
            order_price=order_price,
            spec=spec,
        )
    except Exception as exc:
        if settings.gemini_required:
            raise GeminiCallError(
                f"Architect Gemini call failed: {type(exc).__name__}: {exc}"
            ) from exc
        proposal = _fixture_plan(
            order_id=order_id,
            order_deadline=order_deadline,
            revision_limit=revision_limit,
            order_price=order_price,
            spec=spec,
        )
        proposal.error = f"gemini_fallback: {type(exc).__name__}: {exc}"
        return proposal


def generate_task_packet_proposal(
    *,
    order_id: uuid.UUID,
    task: Any,
    spec: dict[str, Any],
    order_price_share: float,
    order_deadline: datetime | None,
    revision_limit: int,
    dependency_titles: list[str] | None = None,
    force_fixtures: bool = False,
) -> PacketProposal:
    """Propose Charter + TaskPacket fields (fixture or Gemini structured JSON)."""
    if force_fixtures or not settings.gemini_enabled:
        if not force_fixtures and settings.gemini_required:
            raise GeminiNotConfiguredError(
                f"Vertex Gemini required for Task Packet Generator — {_VERTEX_REQUIRED}"
            )
        return _fixture_packet(
            order_id=order_id,
            task=task,
            spec=spec,
            order_price_share=order_price_share,
            order_deadline=order_deadline,
            revision_limit=revision_limit,
            dependency_titles=dependency_titles,
        )

    try:
        return _gemini_packet(
            order_id=order_id,
            task=task,
            spec=spec,
            order_price_share=order_price_share,
            order_deadline=order_deadline,
            revision_limit=revision_limit,
            dependency_titles=dependency_titles,
        )
    except Exception as exc:
        if settings.gemini_required:
            raise GeminiCallError(
                f"Task Packet Gemini call failed: {type(exc).__name__}: {exc}"
            ) from exc
        proposal = _fixture_packet(
            order_id=order_id,
            task=task,
            spec=spec,
            order_price_share=order_price_share,
            order_deadline=order_deadline,
            revision_limit=revision_limit,
            dependency_titles=dependency_titles,
        )
        proposal.error = f"gemini_fallback: {type(exc).__name__}: {exc}"
        return proposal


def generate_qa_proposal(
    *,
    task: Any,
    notes: str,
    asset_urls: list[str],
    outcome_statement: str = "",
) -> QAProposal:
    """Propose QA pass/fail. Deterministic first; Gemini overlays deferred criteria."""
    criteria = list(getattr(task, "acceptance_criteria", None) or [])
    evidence = qa_judge.run_deterministic_checks(
        acceptance_criteria=criteria,
        notes=notes,
        asset_urls=asset_urls,
    )

    # Hard fail on deterministic before calling Gemini / fixture soft-pass.
    if qa_judge.deterministic_failed(evidence):
        review = qa_judge.build_fixture_review(
            evidence=evidence,
            notes=notes,
            asset_urls=asset_urls,
        )
        return QAProposal(
            result=review["result"],
            score=review["score"],
            confidence=review["confidence"],
            feedback=review["feedback"],
            evidence=qa_judge.evidence_for_log(review),
            action=review.get("action", "approve"),
            source="fixture",
        )

    if not settings.gemini_enabled:
        if settings.gemini_required:
            raise GeminiNotConfiguredError(
                f"Vertex Gemini required for QA Judge — {_VERTEX_REQUIRED}"
            )
        return _fixture_qa(evidence=evidence, notes=notes, asset_urls=asset_urls)

    try:
        return _gemini_qa(
            task=task,
            evidence=evidence,
            notes=notes,
            asset_urls=asset_urls,
            outcome_statement=outcome_statement,
        )
    except Exception as exc:
        if settings.gemini_required:
            raise GeminiCallError(
                f"QA Judge Gemini call failed: {type(exc).__name__}: {exc}"
            ) from exc
        proposal = _fixture_qa(evidence=evidence, notes=notes, asset_urls=asset_urls)
        proposal.error = f"gemini_fallback: {type(exc).__name__}: {exc}"
        return proposal


def _fixture_qa(
    *,
    evidence: list[dict[str, Any]],
    notes: str,
    asset_urls: list[str],
) -> QAProposal:
    review = qa_judge.build_fixture_review(
        evidence=evidence,
        notes=notes,
        asset_urls=asset_urls,
    )
    return QAProposal(
        result=review["result"],
        score=review["score"],
        confidence=review["confidence"],
        feedback=review["feedback"],
        evidence=qa_judge.evidence_for_log(review),
        action=review.get("action", "approve"),
        source="fixture",
    )


def _fixture_turn(draft: dict[str, Any], user_message: str) -> SpecTurn:
    all_text = f"{draft.get('outcome_statement', '')} {user_message}"
    new_draft = spec_extractor.extract_from_message(draft, user_message, all_text)
    return SpecTurn(draft=new_draft, reply=None, source="fixture")


def _fixture_packet(
    *,
    order_id: uuid.UUID,
    task: Any,
    spec: dict[str, Any],
    order_price_share: float,
    order_deadline: datetime | None,
    revision_limit: int,
    dependency_titles: list[str] | None,
) -> PacketProposal:
    charter, packet = fixture_charter_and_packet(
        order_id=order_id,
        task=task,
        spec=spec,
        order_price_share=order_price_share,
        order_deadline=order_deadline,
        revision_limit=revision_limit,
        dependency_titles=dependency_titles,
    )
    return PacketProposal(charter=charter, packet=packet, source="fixture")


def _fixture_plan(
    *,
    order_id: uuid.UUID,
    order_deadline: datetime,
    revision_limit: int,
    order_price: Decimal | float | None,
    spec: dict[str, Any],
) -> PlanProposal:
    mapped = list(spec.get("mapped_task_types") or [])
    plan = build_plan_from_spec(
        order_id=order_id,
        order_deadline=order_deadline,
        revision_limit=revision_limit,
        order_price=order_price,
        mapped_task_types=mapped,
        outcome_statement=str(spec.get("outcome_statement") or ""),
    )
    return PlanProposal(plan=plan, source="fixture")


def _gemini_plan(
    *,
    order_id: uuid.UUID,
    order_deadline: datetime,
    revision_limit: int,
    order_price: Decimal | float | None,
    spec: dict[str, Any],
) -> PlanProposal:
    from google.genai import types

    base = _fixture_plan(
        order_id=order_id,
        order_deadline=order_deadline,
        revision_limit=revision_limit,
        order_price=order_price,
        spec=spec,
    )
    plan = dict(base.plan)
    tasks = [dict(t) for t in plan["tasks"]]

    client = make_gemini_client()
    prompt = {
        "outcome_spec": {
            "outcome_statement": spec.get("outcome_statement"),
            "mapped_task_types": spec.get("mapped_task_types") or [],
            "workflow_summary": spec.get("workflow_summary") or "",
            "deliverables": spec.get("deliverables") or [],
            "acceptance_criteria": spec.get("acceptance_criteria") or [],
        },
        "allowed_task_type_slugs": sorted(ALLOWED_TASK_TYPE_SLUGS),
        "skeleton_tasks": [
            {
                "task_type_slug": t["task_type_slug"],
                "title": t["title"],
                "description": t["description"],
                "acceptance_criteria": t["acceptance_criteria"],
                "sequence_order": t["sequence_order"],
            }
            for t in tasks
        ],
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
                            "Enrich this fulfillment DAG for the frozen OutcomeSpec.\n\n"
                            f"{json.dumps(prompt, default=str)}"
                        )
                    )
                ],
            )
        ],
        config=types.GenerateContentConfig(
            system_instruction=ARCHITECT_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=GeminiPlan,
            temperature=0.2,
        ),
    )
    latency_ms = int((time.perf_counter() - started) * 1000)

    raw = response.text or "{}"
    parsed = getattr(response, "parsed", None)
    gemini_plan = parsed if isinstance(parsed, GeminiPlan) else GeminiPlan.model_validate_json(raw)

    by_slug = {item.task_type_slug: item for item in gemini_plan.tasks}
    for task in tasks:
        overlay = by_slug.get(task["task_type_slug"])
        if overlay is None:
            continue
        if overlay.title.strip():
            task["title"] = overlay.title.strip()
        if overlay.description.strip():
            task["description"] = overlay.description.strip()
        if overlay.acceptance_criteria:
            task["acceptance_criteria"] = [
                {
                    "criterion": c.criterion,
                    "check_type": c.check_type or "human_required",
                    **({"rule": c.rule} if c.rule else {}),
                    **({"rubric": c.rubric} if c.rubric else {}),
                }
                for c in overlay.acceptance_criteria
                if c.criterion.strip()
            ]

    plan["tasks"] = tasks
    mapped = normalize_mapped_task_types(list(spec.get("mapped_task_types") or []))
    try:
        validate_dag(plan, mapped_task_types=mapped, allowed_slugs=ALLOWED_TASK_TYPE_SLUGS)
    except InvalidPlanError:
        # Overlay corrupted the DAG — fall back to validated fixture skeleton.
        return PlanProposal(
            plan=base.plan,
            source="fixture",
            model=settings.gemini_model,
            latency_ms=latency_ms,
            confidence=gemini_plan.confidence,
            error="gemini_overlay_invalid_dag",
            raw_response=raw[:8000],
        )

    return PlanProposal(
        plan=plan,
        source="gemini",
        model=settings.gemini_model,
        latency_ms=latency_ms,
        confidence=gemini_plan.confidence,
        raw_response=raw[:8000],
    )


def _gemini_turn(
    draft: dict[str, Any],
    user_message: str,
    history: list[dict[str, str]],
) -> SpecTurn:
    # Imported lazily so google-genai is optional until Vertex is configured.
    from google.genai import types

    client = make_gemini_client()

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


def _gemini_packet(
    *,
    order_id: uuid.UUID,
    task: Any,
    spec: dict[str, Any],
    order_price_share: float,
    order_deadline: datetime | None,
    revision_limit: int,
    dependency_titles: list[str] | None,
) -> PacketProposal:
    from google.genai import types

    # Start from fixture skeleton (IDs, price, deadline, deliverable slice) then
    # overlay Gemini brief/checklist/scope — Spine still freezes the Charter.
    base = _fixture_packet(
        order_id=order_id,
        task=task,
        spec=spec,
        order_price_share=order_price_share,
        order_deadline=order_deadline,
        revision_limit=revision_limit,
        dependency_titles=dependency_titles,
    )

    client = make_gemini_client()
    prompt = {
        "task": {
            "title": getattr(task, "title", ""),
            "description": getattr(task, "description", ""),
            "task_type_slug": getattr(task, "task_type_slug", None),
            "acceptance_criteria": getattr(task, "acceptance_criteria", None) or [],
        },
        "outcome_spec": spec,
        "dependency_titles": dependency_titles or [],
        "fixture_brief": base.packet.get("brief"),
        "fixture_checklist": base.packet.get("checklist"),
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
                            "Build a worker Task Packet for this task.\n\n"
                            f"{json.dumps(prompt, default=str)}"
                        )
                    )
                ],
            )
        ],
        config=types.GenerateContentConfig(
            system_instruction=PACKET_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=GeminiPacket,
            temperature=0.2,
        ),
    )
    latency_ms = int((time.perf_counter() - started) * 1000)

    raw = response.text or "{}"
    parsed = getattr(response, "parsed", None)
    packet_spec = (
        parsed if isinstance(parsed, GeminiPacket) else GeminiPacket.model_validate_json(raw)
    )

    charter = dict(base.charter)
    packet = dict(base.packet)
    if packet_spec.brief.strip():
        packet["brief"] = packet_spec.brief.strip()
    if packet_spec.scope.strip():
        snap = dict(charter.get("snapshot") or {})
        snap["scope"] = packet_spec.scope.strip()
        charter["snapshot"] = snap
    if packet_spec.checklist:
        packet["checklist"] = [
            {
                "id": f"chk_{i + 1}",
                "label": item.label,
                "source_criterion": item.label,
                "required": item.required,
                "done": False,
            }
            for i, item in enumerate(packet_spec.checklist)
        ]

    return PacketProposal(
        charter=charter,
        packet=packet,
        source="gemini",
        model=settings.gemini_model,
        latency_ms=latency_ms,
        confidence=packet_spec.confidence,
        raw_response=raw[:8000],
    )


def _gemini_qa(
    *,
    task: Any,
    evidence: list[dict[str, Any]],
    notes: str,
    asset_urls: list[str],
    outcome_statement: str,
) -> QAProposal:
    from google.genai import types

    deferred = [
        {
            "criterion": e["criterion"],
            "check_type": e["check_type"],
            "rule": e.get("rule") or "",
            "rubric": e.get("rubric") or "",
            "detail": e.get("detail") or "",
        }
        for e in evidence
        if e.get("passed") is None
    ]

    # Nothing deferred — deterministic already decided pass.
    if not deferred:
        return _fixture_qa(evidence=evidence, notes=notes, asset_urls=asset_urls)

    client = make_gemini_client()
    prompt = {
        "outcome_statement": outcome_statement,
        "task": {
            "title": getattr(task, "title", ""),
            "description": getattr(task, "description", ""),
            "task_type_slug": getattr(task, "task_type_slug", None),
        },
        "submission": {"notes": notes, "asset_urls": asset_urls},
        "deterministic_evidence": [
            {
                "criterion": e["criterion"],
                "check_type": e["check_type"],
                "passed": e["passed"],
                "detail": e.get("detail"),
            }
            for e in evidence
            if e.get("passed") is not None
        ],
        "deferred_criteria": deferred,
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
                            "Judge the deferred acceptance criteria for this submission.\n\n"
                            f"{json.dumps(prompt, default=str)}"
                        )
                    )
                ],
            )
        ],
        config=types.GenerateContentConfig(
            system_instruction=QA_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=GeminiQA,
            temperature=0.1,
        ),
    )
    latency_ms = int((time.perf_counter() - started) * 1000)

    raw = response.text or "{}"
    parsed = getattr(response, "parsed", None)
    gemini_qa = parsed if isinstance(parsed, GeminiQA) else GeminiQA.model_validate_json(raw)
    review = qa_judge.merge_gemini_overlay(
        evidence=evidence,
        gemini=gemini_qa.model_dump(),
    )
    return QAProposal(
        result=review["result"],
        score=review["score"],
        confidence=review["confidence"],
        feedback=review["feedback"],
        evidence=qa_judge.evidence_for_log(review),
        action=review.get("action", "approve"),
        source="gemini",
        model=settings.gemini_model,
        latency_ms=latency_ms,
        raw_response=raw[:8000],
    )


def _draft_from_gemini(spec: GeminiSpec, *, previous: dict[str, Any]) -> dict[str, Any]:
    """Merge Gemini output into the draft; keep prior fields when Gemini omits them."""
    from copy import deepcopy

    out = spec_extractor.empty_draft()
    for key in out:
        if key in ("version", "sku_id"):
            continue
        prev = previous.get(key)
        if prev not in (None, "", []):
            out[key] = deepcopy(prev)
    payload = spec.model_dump()
    for key in out:
        if key in ("version", "sku_id"):
            continue
        value = payload.get(key)
        if value not in (None, "", []):
            out[key] = value
    if out.get("risk_tier") not in ("L1", "L2", "L3"):
        out["risk_tier"] = previous.get("risk_tier") or "L1"
    out["sku_id"] = previous.get("sku_id")
    out["version"] = int(previous.get("version", 0)) + 1
    return spec_extractor.apply_package_defaults(out)
