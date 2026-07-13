"""dispute_cases table

Revision ID: 0015_disputes
Revises: 0014_ledger_entries
Create Date: 2026-07-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015_disputes"
down_revision: Union[str, None] = "0014_ledger_entries"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    if "dispute_cases" not in tables:
        op.create_table(
            "dispute_cases",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column(
                "order_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("outcome_orders.id"),
                nullable=False,
            ),
            sa.Column(
                "task_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("fulfillment_tasks.id"),
                nullable=True,
            ),
            sa.Column(
                "raised_by",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id"),
                nullable=False,
            ),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
            sa.Column("ai_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("resolution", sa.Text(), nullable=True),
            sa.Column(
                "resolved_by",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id"),
                nullable=True,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )
        op.create_index("ix_dispute_cases_order_id", "dispute_cases", ["order_id"])
        op.create_index("ix_dispute_cases_status", "dispute_cases", ["status"])

    # Soft flag on orders for open disputes (blocks payout if not yet released)
    cols = {c["name"] for c in inspector.get_columns("outcome_orders")}
    if "dispute_open" not in cols:
        op.add_column(
            "outcome_orders",
            sa.Column("dispute_open", sa.Boolean(), nullable=False, server_default="false"),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = {c["name"] for c in inspector.get_columns("outcome_orders")}
    if "dispute_open" in cols:
        op.drop_column("outcome_orders", "dispute_open")
    if "dispute_cases" in inspector.get_table_names():
        op.drop_index("ix_dispute_cases_status", table_name="dispute_cases")
        op.drop_index("ix_dispute_cases_order_id", table_name="dispute_cases")
        op.drop_table("dispute_cases")
