"""amendments table for formal scope changes

Revision ID: 0012_amendments
Revises: 0011_timers
Create Date: 2026-07-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012_amendments"
down_revision: Union[str, None] = "0011_timers"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "amendments" in inspector.get_table_names():
        return
    op.create_table(
        "amendments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("outcome_orders.id"),
            nullable=False,
        ),
        sa.Column(
            "charter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("charters.id"),
            nullable=True,
        ),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("fulfillment_tasks.id"),
            nullable=True,
        ),
        sa.Column(
            "requested_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("delta_description", sa.Text(), nullable=False),
        sa.Column("proposed_delta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("price_delta", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("time_delta_hours", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_criteria", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="requested"),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_amendments_order_id", "amendments", ["order_id"])
    op.create_index("ix_amendments_task_id", "amendments", ["task_id"])
    op.create_index("ix_amendments_status", "amendments", ["status"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "amendments" not in inspector.get_table_names():
        return
    op.drop_index("ix_amendments_status", table_name="amendments")
    op.drop_index("ix_amendments_task_id", table_name="amendments")
    op.drop_index("ix_amendments_order_id", table_name="amendments")
    op.drop_table("amendments")
