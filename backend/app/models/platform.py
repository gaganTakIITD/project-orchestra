import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EventLog(Base):
    __tablename__ = "event_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    aggregate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actor_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TimerRecord(Base):
    """Durable scheduled jobs (priority window, quote expiry, auto-accept)."""

    __tablename__ = "timers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    aggregate_type: Mapped[str] = mapped_column(String(50), nullable=False, default="task")
    aggregate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    fire_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AiDecisionLog(Base):
    """Append-only audit of every AI proposal. AI proposes; the Spine decides."""

    __tablename__ = "ai_decision_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    agent_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # gemini | fixture
    model: Mapped[str | None] = mapped_column(String(60), nullable=True)
    input_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_draft: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    completeness_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ready_for_quote: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    """In-app notification projected from event_log (same transaction as emit)."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ref_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ref_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkerStatsRecord(Base):
    """Per-task-type reputation counters updated on QA pass/fail."""

    __tablename__ = "worker_stats"
    __table_args__ = (
        UniqueConstraint("worker_id", "task_type_slug", name="uq_worker_stats_worker_slug"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    task_type_slug: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reworked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_qa_confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class LedgerEntryRecord(Base):
    """Double-entry stub lines (mock amounts; no real money)."""

    __tablename__ = "ledger_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("outcome_orders.id"), nullable=False, index=True
    )
    account: Mapped[str] = mapped_column(String(64), nullable=False)
    debit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    credit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProjectTemplateRecord(Base):
    """Closed-outcome templates for Spec Compiler RAG retrieve (MVP keyword overlap)."""

    __tablename__ = "project_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("outcome_skus.id"), nullable=True, index=True
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("outcome_orders.id"), nullable=True
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    plan_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    spec_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    dag_template: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    embedding: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
