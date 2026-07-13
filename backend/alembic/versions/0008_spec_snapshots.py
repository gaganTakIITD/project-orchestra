"""chat_sessions.spec_snapshots for scope draft undo

Revision ID: 0008_spec_snapshots
Revises: 0007_spec_workflow_summary
Create Date: 2026-07-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_spec_snapshots"
down_revision: Union[str, None] = "0007_spec_workflow_summary"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = {c["name"] for c in inspector.get_columns("chat_sessions")}
    if "spec_snapshots" not in cols:
        op.add_column(
            "chat_sessions",
            sa.Column("spec_snapshots", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = {c["name"] for c in inspector.get_columns("chat_sessions")}
    if "spec_snapshots" in cols:
        op.drop_column("chat_sessions", "spec_snapshots")
