"""Amendment schemas — mirrors lib/types.ts Amendment."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AmendmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    charter_id: str | None = None
    task_id: str | None = None
    requested_by: str
    delta_description: str
    proposed_delta: dict | None = None
    price_delta: float = 0
    time_delta_hours: int = 0
    status: str
    approved_at: str | None = None
    created_at: str

    @classmethod
    def from_orm_row(cls, row) -> "AmendmentOut":
        return cls(
            id=str(row.id),
            order_id=str(row.order_id),
            charter_id=str(row.charter_id) if row.charter_id else None,
            task_id=str(row.task_id) if row.task_id else None,
            requested_by=str(row.requested_by),
            delta_description=row.delta_description,
            proposed_delta=row.proposed_delta,
            price_delta=float(row.price_delta or 0),
            time_delta_hours=int(row.time_delta_hours or 0),
            status=row.status,
            approved_at=row.approved_at.isoformat() if row.approved_at else None,
            created_at=row.created_at.isoformat() if isinstance(row.created_at, datetime) else str(row.created_at),
        )


class AmendmentListOut(BaseModel):
    amendments: list[AmendmentOut] = Field(default_factory=list)
