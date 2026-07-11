"""add charters and task_packets

Revision ID: 0002_charters_packets
Revises: 0001_baseline
Create Date: 2026-07-12
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_charters_packets"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if "charters" not in tables:
        op.create_table(
            "charters",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("outcome_orders.id"), nullable=False),
            sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fulfillment_tasks.id"), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("snapshot", postgresql.JSONB(), nullable=False),
            sa.Column("mutual_start_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_charters_order_id", "charters", ["order_id"])
        op.create_index("ix_charters_task_id", "charters", ["task_id"], unique=True)

    if "task_packets" not in tables:
        op.create_table(
            "task_packets",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fulfillment_tasks.id"), nullable=False),
            sa.Column("charter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("charters.id"), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("brief", sa.Text(), nullable=False, server_default=""),
            sa.Column("checklist", postgresql.JSONB(), nullable=False),
            sa.Column("client_inputs", postgresql.JSONB(), nullable=False),
            sa.Column("dependencies", postgresql.JSONB(), nullable=False),
            sa.Column("references", postgresql.JSONB(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_task_packets_task_id", "task_packets", ["task_id"], unique=True)
        op.create_index("ix_task_packets_charter_id", "task_packets", ["charter_id"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    if "task_packets" in tables:
        op.drop_table("task_packets")
    if "charters" in tables:
        op.drop_table("charters")
