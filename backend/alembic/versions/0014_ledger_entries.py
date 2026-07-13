"""ledger_entries double-entry stub for payments sandbox

Revision ID: 0014_ledger_entries
Revises: 0013_worker_stats
Create Date: 2026-07-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014_ledger_entries"
down_revision: Union[str, None] = "0013_worker_stats"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "ledger_entries" in inspector.get_table_names():
        return
    op.create_table(
        "ledger_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("outcome_orders.id"),
            nullable=False,
        ),
        sa.Column("account", sa.String(length=64), nullable=False),
        sa.Column("debit", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("credit", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_ledger_entries_order_id", "ledger_entries", ["order_id"])
    op.create_index("ix_ledger_entries_event_type", "ledger_entries", ["event_type"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "ledger_entries" not in inspector.get_table_names():
        return
    op.drop_index("ix_ledger_entries_event_type", table_name="ledger_entries")
    op.drop_index("ix_ledger_entries_order_id", table_name="ledger_entries")
    op.drop_table("ledger_entries")
