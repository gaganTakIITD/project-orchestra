"""worker_stats table for per-task-type reputation

Revision ID: 0013_worker_stats
Revises: 0012_amendments
Create Date: 2026-07-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013_worker_stats"
down_revision: Union[str, None] = "0012_amendments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "worker_stats" in inspector.get_table_names():
        return
    op.create_table(
        "worker_stats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "worker_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("task_type_slug", sa.String(length=64), nullable=False),
        sa.Column("completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reworked", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_qa_confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("worker_id", "task_type_slug", name="uq_worker_stats_worker_slug"),
    )
    op.create_index("ix_worker_stats_worker_id", "worker_stats", ["worker_id"])
    op.create_index("ix_worker_stats_task_type_slug", "worker_stats", ["task_type_slug"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "worker_stats" not in inspector.get_table_names():
        return
    op.drop_index("ix_worker_stats_task_type_slug", table_name="worker_stats")
    op.drop_index("ix_worker_stats_worker_id", table_name="worker_stats")
    op.drop_table("worker_stats")
