from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.fulfillment import CandidateOut


class OutcomeSpecDraftOut(BaseModel):
    outcome_statement: str = ""
    deliverables: list[dict] = Field(default_factory=list)
    acceptance_criteria: list[dict] = Field(default_factory=list)
    in_scope: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    client_inputs_required: list[str] = Field(default_factory=list)
    mapped_task_types: list[str] = Field(default_factory=list)
    risk_tier: str = "L1"
    workflow_summary: str = ""
    sku_id: str | None = None
    version: int = 0


class ChatMessageOut(BaseModel):
    id: str
    session_id: str
    role: str
    body: str
    spec_version_after: int | None = None
    created_at: datetime

    @classmethod
    def from_orm_row(cls, row) -> "ChatMessageOut":
        return cls(
            id=str(row.id),
            session_id=str(row.session_id),
            role=row.role,
            body=row.body,
            spec_version_after=row.spec_version_after,
            created_at=row.created_at,
        )


class StartChatSessionIn(BaseModel):
    """POST /chat/sessions — default starts Scope; matcher/pricing need refs."""

    agent_type: str = "spec_compiler"
    ref_type: str | None = None
    ref_id: UUID | None = None
    order_id: UUID | None = None


class ChatSessionOut(BaseModel):
    id: str
    agent_type: str
    status: str
    spec_draft: OutcomeSpecDraftOut
    spec_version: int
    completeness_pct: int
    missing_fields: list[str]
    ready_for_quote: bool
    ref_type: str | None = None
    ref_id: str | None = None
    order_id: str | None = None
    candidates: list[CandidateOut] | None = None
    ready_to_confirm: bool = False
    can_undo: bool = False
    messages: list[ChatMessageOut]
    created_at: datetime

    @classmethod
    def from_session(cls, session, messages: list) -> "ChatSessionOut":
        draft = session.spec_draft or {}
        # Strip pricing-only helper keys from the OutcomeSpec draft view
        draft_view = {k: v for k, v in draft.items() if k != "quote_context"}
        raw_candidates = session.candidates_draft
        candidates = None
        if isinstance(raw_candidates, list) and raw_candidates:
            candidates = [CandidateOut(**c) for c in raw_candidates]
        snapshots = session.spec_snapshots or {}
        can_undo = (
            session.agent_type == "spec_compiler"
            and session.status == "active"
            and bool(snapshots)
        )
        return cls(
            id=str(session.id),
            agent_type=session.agent_type,
            status=session.status,
            spec_draft=OutcomeSpecDraftOut(**draft_view) if draft_view else OutcomeSpecDraftOut(),
            spec_version=session.spec_version,
            completeness_pct=session.completeness_pct,
            missing_fields=session.missing_fields or [],
            ready_for_quote=session.ready_for_quote,
            ref_type=session.ref_type,
            ref_id=str(session.ref_id) if session.ref_id else None,
            order_id=str(session.order_id) if session.order_id else None,
            candidates=candidates,
            ready_to_confirm=bool(getattr(session, "ready_to_confirm", False)),
            can_undo=can_undo,
            messages=[ChatMessageOut.from_orm_row(m) for m in messages],
            created_at=session.created_at,
        )


class ChatSessionSummaryOut(BaseModel):
    """Lightweight row for the 'Resume scope' list (GET /chat/sessions)."""

    id: str
    agent_type: str
    status: str
    title: str
    completeness_pct: int
    ready_for_quote: bool
    spec_version: int
    created_at: datetime

    @classmethod
    def from_session(cls, session) -> "ChatSessionSummaryOut":
        draft = session.spec_draft or {}
        title = (draft.get("outcome_statement") or "").strip() or "Untitled outcome"
        return cls(
            id=str(session.id),
            agent_type=session.agent_type,
            status=session.status,
            title=title,
            completeness_pct=session.completeness_pct,
            ready_for_quote=session.ready_for_quote,
            spec_version=session.spec_version,
            created_at=session.created_at,
        )


class SendMessageIn(BaseModel):
    body: str = Field(min_length=1)


class FinalizeChatIn(BaseModel):
    """Optional override for matcher finalize when the UI ranking diverged from chat."""

    ranked_worker_ids: list[str] | None = None


class FinalizeChatOut(BaseModel):
    """Scope → intent/quote; matcher → preference_set; pricing → quote/order."""

    intent_id: str | None = None
    quote_id: str | None = None
    preference_set_id: str | None = None
    order_id: str | None = None
    task_id: str | None = None
