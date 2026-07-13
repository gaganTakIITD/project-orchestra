import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(30), nullable=False, default="spec_compiler")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    # Scope (Stage 1) — OutcomeSpec draft fields
    spec_draft: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    spec_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completeness_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    missing_fields: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    ready_for_quote: Mapped[bool] = mapped_column(default=False)
    intent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    # Matcher (Stage 3) — Preference Chat refs + Candidate[] artifact
    ref_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ref_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    candidates_draft: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    ready_to_confirm: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Scope undo — map of str(spec_version) → draft snapshot taken before that version advanced
    spec_snapshots: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    spec_version_after: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
