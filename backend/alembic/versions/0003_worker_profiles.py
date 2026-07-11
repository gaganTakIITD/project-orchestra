"""add worker_profiles

Revision ID: 0003_worker_profiles
Revises: 0002_charters_packets
Create Date: 2026-07-12
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_worker_profiles"
down_revision: Union[str, None] = "0002_charters_packets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "worker_profiles" in inspector.get_table_names():
        return

    op.create_table(
        "worker_profiles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("community_type", sa.String(20), nullable=False, server_default="design"),
        sa.Column("headline", sa.String(255), nullable=False, server_default=""),
        sa.Column("bio", sa.Text(), nullable=False, server_default=""),
        sa.Column("availability_status", sa.String(20), nullable=False, server_default="available"),
        sa.Column("weekly_hours_available", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("max_concurrent_tasks", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("payout_min", sa.Float(), nullable=True),
        sa.Column("payout_max", sa.Float(), nullable=True),
        sa.Column("campus_verified", sa.Boolean(), server_default="false"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("profile_completion_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("github_url", sa.String(512), nullable=True),
        sa.Column("figma_url", sa.String(512), nullable=True),
        sa.Column("behance_url", sa.String(512), nullable=True),
        sa.Column("linkedin_url", sa.String(512), nullable=True),
        sa.Column("skills", postgresql.JSONB(), nullable=False),
        sa.Column("tools", postgresql.JSONB(), nullable=False),
        sa.Column("task_types", postgresql.JSONB(), nullable=False),
        sa.Column("portfolio", postgresql.JSONB(), nullable=False),
        sa.Column("stats", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "worker_profiles" in inspector.get_table_names():
        op.drop_table("worker_profiles")
