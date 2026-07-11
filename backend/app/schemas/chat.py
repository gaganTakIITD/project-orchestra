from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


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


class ChatSessionOut(BaseModel):
    id: str
    agent_type: str
    status: str
    spec_draft: OutcomeSpecDraftOut
    spec_version: int
    completeness_pct: int
    missing_fields: list[str]
    ready_for_quote: bool
    messages: list[ChatMessageOut]
    created_at: datetime

    @classmethod
    def from_session(cls, session, messages: list) -> "ChatSessionOut":
        draft = session.spec_draft or {}
        return cls(
            id=str(session.id),
            agent_type=session.agent_type,
            status=session.status,
            spec_draft=OutcomeSpecDraftOut(**draft),
            spec_version=session.spec_version,
            completeness_pct=session.completeness_pct,
            missing_fields=session.missing_fields or [],
            ready_for_quote=session.ready_for_quote,
            messages=[ChatMessageOut.from_orm_row(m) for m in messages],
            created_at=session.created_at,
        )


class SendMessageIn(BaseModel):
    body: str = Field(min_length=1)


class FinalizeChatOut(BaseModel):
    intent_id: str
    quote_id: str
