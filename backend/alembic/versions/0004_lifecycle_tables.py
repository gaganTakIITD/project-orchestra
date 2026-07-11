"""add submissions, discussion, delivery_bundles

Revision ID: 0004_lifecycle_tables
Revises: 0003_worker_profiles
Create Date: 2026-07-12
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_lifecycle_tables"
down_revision: Union[str, None] = "0003_worker_profiles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = set(inspector.get_table_names())

    if "submissions" not in existing:
        op.create_table(
            "submissions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "task_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("fulfillment_tasks.id"),
                nullable=False,
            ),
            sa.Column("worker_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("asset_urls", postgresql.JSONB(), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_submissions_task_id", "submissions", ["task_id"])
        op.create_index("ix_submissions_worker_id", "submissions", ["worker_id"])

    if "discussion_threads" not in existing:
        op.create_table(
            "discussion_threads",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "task_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("fulfillment_tasks.id"),
                nullable=False,
                unique=True,
            ),
            sa.Column(
                "order_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("outcome_orders.id"),
                nullable=False,
            ),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_discussion_threads_task_id", "discussion_threads", ["task_id"])
        op.create_index("ix_discussion_threads_order_id", "discussion_threads", ["order_id"])

    if "discussion_messages" not in existing:
        op.create_table(
            "discussion_messages",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "thread_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("discussion_threads.id"),
                nullable=False,
            ),
            sa.Column("sender_id", sa.String(64), nullable=False),
            sa.Column("sender_name", sa.String(255), nullable=False, server_default=""),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("message_type", sa.String(40), nullable=False, server_default="clarification"),
            sa.Column("attachments", postgresql.JSONB(), nullable=False),
            sa.Column("scope_flagged", sa.Boolean(), server_default="false"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_discussion_messages_thread_id", "discussion_messages", ["thread_id"])

    if "delivery_bundles" not in existing:
        op.create_table(
            "delivery_bundles",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "order_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("outcome_orders.id"),
                nullable=False,
                unique=True,
            ),
            sa.Column("assets", postgresql.JSONB(), nullable=False),
            sa.Column("qa_summary", sa.Text(), nullable=False, server_default=""),
            sa.Column("delivered_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("accepted_by", postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.create_index("ix_delivery_bundles_order_id", "delivery_bundles", ["order_id"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = set(inspector.get_table_names())
    for table in ("delivery_bundles", "discussion_messages", "discussion_threads", "submissions"):
        if table in existing:
            op.drop_table(table)
