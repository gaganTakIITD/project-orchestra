"""notifications table for event-projected in-app feed

Revision ID: 0009_notifications
Revises: 0008_spec_snapshots
Create Date: 2026-07-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_notifications"
down_revision: Union[str, None] = "0008_spec_snapshots"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = set(inspector.get_table_names())

    if "notifications" not in existing:
        op.create_table(
            "notifications",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("type", sa.String(50), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("body", sa.Text(), nullable=False, server_default=""),
            sa.Column("ref_type", sa.String(50), nullable=True),
            sa.Column("ref_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("source_event_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
            ),
        )
        op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
        op.create_index(
            "ix_notifications_source_event_id", "notifications", ["source_event_id"]
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = set(inspector.get_table_names())
    if "notifications" in existing:
        op.drop_index("ix_notifications_source_event_id", table_name="notifications")
        op.drop_index("ix_notifications_user_id", table_name="notifications")
        op.drop_table("notifications")
