"""outcome_orders.ledger_state for mock Held→Reserved→Released

Revision ID: 0010_order_ledger_state
Revises: 0009_notifications
Create Date: 2026-07-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010_order_ledger_state"
down_revision: Union[str, None] = "0009_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = {c["name"] for c in inspector.get_columns("outcome_orders")}
    if "ledger_state" not in cols:
        op.add_column(
            "outcome_orders",
            sa.Column(
                "ledger_state",
                sa.String(30),
                nullable=False,
                server_default="unfunded",
            ),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = {c["name"] for c in inspector.get_columns("outcome_orders")}
    if "ledger_state" in cols:
        op.drop_column("outcome_orders", "ledger_state")
