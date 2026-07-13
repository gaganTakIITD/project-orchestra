"""timers table for durable priority-window jobs

Revision ID: 0011_timers
Revises: 0010_order_ledger_state
Create Date: 2026-07-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011_timers"
down_revision: Union[str, None] = "0010_order_ledger_state"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "timers" in inspector.get_table_names():
        return
    op.create_table(
        "timers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("aggregate_type", sa.String(length=50), nullable=False, server_default="task"),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fire_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("fired_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_timers_kind", "timers", ["kind"])
    op.create_index("ix_timers_aggregate_id", "timers", ["aggregate_id"])
    op.create_index("ix_timers_fire_at", "timers", ["fire_at"])
    op.create_index("ix_timers_status", "timers", ["status"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "timers" not in inspector.get_table_names():
        return
    op.drop_index("ix_timers_status", table_name="timers")
    op.drop_index("ix_timers_fire_at", table_name="timers")
    op.drop_index("ix_timers_aggregate_id", table_name="timers")
    op.drop_index("ix_timers_kind", table_name="timers")
    op.drop_table("timers")
