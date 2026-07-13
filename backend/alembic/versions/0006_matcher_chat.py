"""matcher preference chat columns on chat_sessions

Revision ID: 0006_matcher_chat
Revises: 0005_external_auth
Create Date: 2026-07-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_matcher_chat"
down_revision: Union[str, None] = "0005_external_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = {c["name"] for c in inspector.get_columns("chat_sessions")}

    if "ref_type" not in cols:
        op.add_column("chat_sessions", sa.Column("ref_type", sa.String(20), nullable=True))
    if "ref_id" not in cols:
        op.add_column(
            "chat_sessions",
            sa.Column("ref_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.create_index("ix_chat_sessions_ref_id", "chat_sessions", ["ref_id"])
    if "order_id" not in cols:
        op.add_column(
            "chat_sessions",
            sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.create_index("ix_chat_sessions_order_id", "chat_sessions", ["order_id"])
    if "candidates_draft" not in cols:
        op.add_column(
            "chat_sessions",
            sa.Column("candidates_draft", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )
    if "ready_to_confirm" not in cols:
        op.add_column(
            "chat_sessions",
            sa.Column("ready_to_confirm", sa.Boolean(), nullable=False, server_default=sa.false()),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = {c["name"] for c in inspector.get_columns("chat_sessions")}

    if "ready_to_confirm" in cols:
        op.drop_column("chat_sessions", "ready_to_confirm")
    if "candidates_draft" in cols:
        op.drop_column("chat_sessions", "candidates_draft")
    if "order_id" in cols:
        op.drop_index("ix_chat_sessions_order_id", table_name="chat_sessions")
        op.drop_column("chat_sessions", "order_id")
    if "ref_id" in cols:
        op.drop_index("ix_chat_sessions_ref_id", table_name="chat_sessions")
        op.drop_column("chat_sessions", "ref_id")
    if "ref_type" in cols:
        op.drop_column("chat_sessions", "ref_type")
