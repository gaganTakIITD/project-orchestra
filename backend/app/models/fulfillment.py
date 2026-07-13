import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.orchestrator.states import OrderStatus, TaskStatus


class OutcomeOrder(Base):
    __tablename__ = "outcome_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    quote_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    spec_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    sku_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=OrderStatus.CONFIRMED)
    # Mock money only — Held → Reserved → Released via LedgerService lifecycle hooks.
    ledger_state: Mapped[str] = mapped_column(String(30), nullable=False, default="unfunded")
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0"))
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revision_limit: Mapped[int] = mapped_column(Integer, default=2)
    progress_pct: Mapped[int] = mapped_column(Integer, default=0)
    # Open dispute blocks payout_released until resolved (Sprint 7).
    dispute_open: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class FulfillmentPlan(Base):
    __tablename__ = "fulfillment_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("outcome_orders.id"), unique=True, nullable=False, index=True
    )
    milestones: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    critical_path_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FulfillmentTask(Base):
    __tablename__ = "fulfillment_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fulfillment_plans.id"), nullable=True, index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("outcome_orders.id"), nullable=False, index=True
    )
    task_type_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("task_types.id"), nullable=True)
    task_type_slug: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=TaskStatus.BLOCKED)
    sequence_order: Mapped[int] = mapped_column(Integer, default=0)
    acceptance_criteria: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    payout_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0"))
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_worker_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    revision_count: Mapped[int] = mapped_column(Integer, default=0)
    revision_limit: Mapped[int] = mapped_column(Integer, default=2)
    priority_window_ends: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    depends_on: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TaskPreferenceSet(Base):
    __tablename__ = "task_preference_sets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fulfillment_tasks.id"), nullable=False, index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("outcome_orders.id"), nullable=False, index=True
    )
    entries: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CharterRecord(Base):
    """Frozen per-task job contract (snapshot from OutcomeSpec + Architect task)."""

    __tablename__ = "charters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("outcome_orders.id"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fulfillment_tasks.id"), unique=True, nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    mutual_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TaskPacketRecord(Base):
    """Worker job card — checklist + brief derived from Charter."""

    __tablename__ = "task_packets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fulfillment_tasks.id"), unique=True, nullable=False, index=True
    )
    charter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("charters.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    brief: Mapped[str] = mapped_column(Text, nullable=False, default="")
    checklist: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    client_inputs: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    dependencies: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    references: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SubmissionRecord(Base):
    """Worker work product for a task (notes + asset URLs)."""

    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fulfillment_tasks.id"), nullable=False, index=True
    )
    worker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    asset_urls: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DiscussionThreadRecord(Base):
    """Scoped discussion room per fulfillment task."""

    __tablename__ = "discussion_threads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fulfillment_tasks.id"), unique=True, nullable=False, index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("outcome_orders.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DiscussionMessageRecord(Base):
    __tablename__ = "discussion_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("discussion_threads.id"), nullable=False, index=True
    )
    sender_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(40), nullable=False, default="clarification")
    attachments: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    scope_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DeliveryBundleRecord(Base):
    """Client-facing delivery package for an order."""

    __tablename__ = "delivery_bundles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("outcome_orders.id"), unique=True, nullable=False, index=True
    )
    assets: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    qa_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)


class AmendmentRecord(Base):
    """Formal scope change — only legal path to mutate a frozen Charter."""

    __tablename__ = "amendments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("outcome_orders.id"), nullable=False, index=True
    )
    charter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("charters.id"), nullable=True
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fulfillment_tasks.id"), nullable=True, index=True
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    delta_description: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_delta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    price_delta: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0"))
    time_delta_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_criteria: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="requested", index=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DisputeCaseRecord(Base):
    __tablename__ = "dispute_cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("outcome_orders.id"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fulfillment_tasks.id"), nullable=True
    )
    raised_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", index=True)
    ai_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
