"""Read-only admin console API — inspect orders, event_log, ai_decision_log."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.fulfillment import FulfillmentTask, OutcomeOrder
from app.models.identity import User
from app.models.platform import AiDecisionLog, EventLog
from app.schemas.admin import (
    AdminAiDecisionListOut,
    AdminAiDecisionOut,
    AdminEventListOut,
    AdminEventOut,
    AdminOrderListOut,
    AdminOrderOut,
)
from app.services.auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/orders", response_model=AdminOrderListOut)
async def list_orders(
    status: str | None = Query(default=None, description="Filter by order status"),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> AdminOrderListOut:
    stmt = select(OutcomeOrder).order_by(OutcomeOrder.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(OutcomeOrder.status == status)
    rows = (await db.scalars(stmt)).all()
    return AdminOrderListOut(orders=[AdminOrderOut.from_orm_row(r) for r in rows])


@router.get("/orders/{order_id}/events", response_model=AdminEventListOut)
async def list_order_events(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> AdminEventListOut:
    order = await db.get(OutcomeOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    task_ids = list(
        await db.scalars(
            select(FulfillmentTask.id).where(FulfillmentTask.order_id == order_id)
        )
    )

    # Events for the order aggregate + any child task aggregates
    conditions = [
        (EventLog.aggregate_type == "order") & (EventLog.aggregate_id == order_id),
    ]
    if task_ids:
        conditions.append(
            (EventLog.aggregate_type == "task") & (EventLog.aggregate_id.in_(task_ids))
        )

    stmt = (
        select(EventLog)
        .where(or_(*conditions))
        .order_by(EventLog.created_at.asc())
    )
    events = (await db.scalars(stmt)).all()
    return AdminEventListOut(
        order_id=str(order_id),
        events=[AdminEventOut.from_orm_row(e) for e in events],
    )


@router.get("/ai-decisions", response_model=AdminAiDecisionListOut)
async def list_ai_decisions(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
) -> AdminAiDecisionListOut:
    stmt = (
        select(AiDecisionLog)
        .order_by(AiDecisionLog.created_at.desc())
        .limit(limit)
    )
    rows = (await db.scalars(stmt)).all()
    return AdminAiDecisionListOut(
        decisions=[AdminAiDecisionOut.from_orm_row(r) for r in rows]
    )
