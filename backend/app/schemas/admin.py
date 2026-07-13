"""Read-only admin console response shapes."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AdminOrderOut(BaseModel):
    id: str
    client_id: str
    quote_id: str
    spec_id: str
    sku_id: str | None = None
    status: str
    price: float
    deadline: datetime | None = None
    revision_limit: int
    progress_pct: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_row(cls, row) -> "AdminOrderOut":
        return cls(
            id=str(row.id),
            client_id=str(row.client_id),
            quote_id=str(row.quote_id) if row.quote_id else "",
            spec_id=str(row.spec_id) if row.spec_id else "",
            sku_id=str(row.sku_id) if row.sku_id else None,
            status=row.status,
            price=float(row.price),
            deadline=row.deadline,
            revision_limit=row.revision_limit,
            progress_pct=row.progress_pct,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class AdminEventOut(BaseModel):
    id: str
    aggregate_type: str
    aggregate_id: str
    event_type: str
    actor_id: str | None = None
    actor_type: str | None = None
    payload: dict[str, Any] | None = None
    created_at: datetime

    @classmethod
    def from_orm_row(cls, row) -> "AdminEventOut":
        return cls(
            id=str(row.id),
            aggregate_type=row.aggregate_type,
            aggregate_id=str(row.aggregate_id),
            event_type=row.event_type,
            actor_id=str(row.actor_id) if row.actor_id else None,
            actor_type=row.actor_type,
            payload=row.payload,
            created_at=row.created_at,
        )


class AdminAiDecisionOut(BaseModel):
    id: str
    session_id: str | None = None
    agent_type: str
    source: str
    model: str | None = None
    input_text: str | None = None
    output_draft: dict[str, Any] | None = None
    reply: str | None = None
    completeness_pct: int | None = None
    ready_for_quote: bool = False
    confidence: float | None = None
    latency_ms: int | None = None
    error: str | None = None
    created_at: datetime

    @classmethod
    def from_orm_row(cls, row) -> "AdminAiDecisionOut":
        return cls(
            id=str(row.id),
            session_id=str(row.session_id) if row.session_id else None,
            agent_type=row.agent_type,
            source=row.source,
            model=row.model,
            input_text=row.input_text,
            output_draft=row.output_draft,
            reply=row.reply,
            completeness_pct=row.completeness_pct,
            ready_for_quote=bool(row.ready_for_quote),
            confidence=float(row.confidence) if row.confidence is not None else None,
            latency_ms=row.latency_ms,
            error=row.error,
            created_at=row.created_at,
        )


class AdminOrderListOut(BaseModel):
    orders: list[AdminOrderOut] = Field(default_factory=list)


class AdminEventListOut(BaseModel):
    order_id: str
    events: list[AdminEventOut] = Field(default_factory=list)


class AdminAiDecisionListOut(BaseModel):
    decisions: list[AdminAiDecisionOut] = Field(default_factory=list)
