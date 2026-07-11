from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateIntentIn(BaseModel):
    raw_text: str = Field(min_length=10)
    attachments: list[str] = Field(default_factory=list)


class CreateIntentOut(BaseModel):
    intent_id: str
    quote_id: str


class DeliverableOut(BaseModel):
    name: str
    format: str
    required: bool


class AcceptanceCriterionOut(BaseModel):
    criterion: str
    check_type: str
    rule: str | None = None
    rubric: str | None = None


class OutcomeSpecOut(BaseModel):
    id: str
    intent_id: str
    sku_id: str | None = None
    outcome_statement: str
    deliverables: list[DeliverableOut]
    acceptance_criteria: list[AcceptanceCriterionOut]
    in_scope: list[str]
    out_of_scope: list[str]
    assumptions: list[str]
    client_inputs_required: list[str]
    mapped_task_types: list[str]
    risk_tier: str
    version: int
    frozen_at: datetime | None = None

    @classmethod
    def from_orm_row(cls, row) -> "OutcomeSpecOut":
        return cls(
            id=str(row.id),
            intent_id=str(row.intent_id),
            sku_id=str(row.sku_id) if row.sku_id else None,
            outcome_statement=row.outcome_statement,
            deliverables=row.deliverables,
            acceptance_criteria=row.acceptance_criteria,
            in_scope=row.in_scope,
            out_of_scope=row.out_of_scope,
            assumptions=row.assumptions,
            client_inputs_required=row.client_inputs_required,
            mapped_task_types=row.mapped_task_types,
            risk_tier=row.risk_tier,
            version=row.version,
            frozen_at=row.frozen_at,
        )


class QuoteOut(BaseModel):
    id: str
    spec_id: str
    client_id: str
    price: float
    deadline: datetime
    revision_limit: int
    status: str
    valid_until: datetime
    ai_confidence: float | None = None
    ai_rationale: str | None = None
    created_at: datetime

    @classmethod
    def from_orm_row(cls, row) -> "QuoteOut":
        return cls(
            id=str(row.id),
            spec_id=str(row.spec_id),
            client_id=str(row.client_id),
            price=float(row.price),
            deadline=row.deadline,
            revision_limit=row.revision_limit,
            status=row.status,
            valid_until=row.valid_until,
            ai_confidence=float(row.ai_confidence) if row.ai_confidence is not None else None,
            ai_rationale=row.ai_rationale,
            created_at=row.created_at,
        )


class AcceptQuoteOut(BaseModel):
    order_id: str


class OutcomeOrderOut(BaseModel):
    id: str
    client_id: str
    quote_id: str
    spec_id: str
    sku_id: str | None = None
    status: str
    price: float
    deadline: datetime
    revision_limit: int
    progress_pct: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_row(cls, row) -> "OutcomeOrderOut":
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
