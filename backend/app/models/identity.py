import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Stable demo identities until JWT auth lands.
DEMO_CLIENT_ID = uuid.UUID("00000000-0000-4000-8000-000000000010")
DEMO_WORKER_ID = uuid.UUID("00000000-0000-4000-8000-000000000020")
DEMO_WORKER_MEERA_ID = uuid.UUID("00000000-0000-4000-8000-000000000021")
DEMO_WORKER_KABIR_ID = uuid.UUID("00000000-0000-4000-8000-000000000022")
DEMO_WORKER_AISHA_ID = uuid.UUID("00000000-0000-4000-8000-000000000023")
DEMO_WORKER_DEV_ID = uuid.UUID("00000000-0000-4000-8000-000000000024")
DEMO_WORKER_JAYA_ID = uuid.UUID("00000000-0000-4000-8000-000000000025")
DEMO_WORKER_NEEL_ID = uuid.UUID("00000000-0000-4000-8000-000000000026")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="client")
    profile_photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    # Clerk (or other IdP) subject — null for seeded demo users until linked
    external_auth_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkerProfileRecord(Base):
    """Worker talent profile — JSONB bags for skills/tools/portfolio (MVP)."""

    __tablename__ = "worker_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True
    )
    community_type: Mapped[str] = mapped_column(String(20), nullable=False, default="design")
    headline: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    bio: Mapped[str] = mapped_column(Text, nullable=False, default="")
    availability_status: Mapped[str] = mapped_column(String(20), nullable=False, default="available")
    weekly_hours_available: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    max_concurrent_tasks: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    payout_min: Mapped[float | None] = mapped_column(nullable=True)
    payout_max: Mapped[float | None] = mapped_column(nullable=True)
    campus_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    profile_completion_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    github_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    figma_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    behance_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    skills: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    tools: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    task_types: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    portfolio: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    stats: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
