"""project_templates for Spec Compiler RAG retrieve

Revision ID: 0016_project_templates
Revises: 0015_disputes
Create Date: 2026-07-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0016_project_templates"
down_revision: Union[str, None] = "0015_disputes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "project_templates" in inspector.get_table_names():
        return
    op.create_table(
        "project_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "sku_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("outcome_skus.id"),
            nullable=True,
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("outcome_orders.id"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("plan_summary", sa.Text(), nullable=True),
        sa.Column("spec_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("dag_template", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="1"),
        # MVP: JSON float list (no pgvector extension required)
        sa.Column("embedding", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_project_templates_sku_id", "project_templates", ["sku_id"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "project_templates" not in inspector.get_table_names():
        return
    op.drop_index("ix_project_templates_sku_id", table_name="project_templates")
    op.drop_table("project_templates")
