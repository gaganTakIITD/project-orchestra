import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.fulfillment import OutcomeOrder
from app.models.identity import User
from app.schemas.commerce import OutcomeOrderOut
from app.schemas.fulfillment import (
    CandidateOut,
    DeliveryBundleOut,
    FulfillmentPlanOut,
    PreferenceSetOut,
    SetPreferencesIn,
    TaskStatusOut,
)
from app.services.auth import get_current_client
from app.services.delivery import DeliveryService
from app.services.fulfillment import FulfillmentService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[OutcomeOrderOut])
async def list_orders(
    db: AsyncSession = Depends(get_db),
    client: User = Depends(get_current_client),
) -> list[OutcomeOrderOut]:
    """The current client's outcomes, newest first — powers the /orders dashboard."""
    stmt = (
        select(OutcomeOrder)
        .where(OutcomeOrder.client_id == client.id)
        .order_by(OutcomeOrder.created_at.desc())
    )
    rows = (await db.scalars(stmt)).all()
    return [OutcomeOrderOut.from_orm_row(r) for r in rows]


@router.get("/{order_id}", response_model=OutcomeOrderOut)
async def get_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> OutcomeOrderOut:
    order = await db.get(OutcomeOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return OutcomeOrderOut.from_orm_row(order)


@router.get("/{order_id}/milestones", response_model=FulfillmentPlanOut)
async def get_order_milestones(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> FulfillmentPlanOut:
    service = FulfillmentService(db)
    try:
        plan = await service.get_plan_for_order(order_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    tasks = await service.list_tasks_for_order(order_id)
    return FulfillmentPlanOut.from_orm_rows(plan, tasks)


@router.get("/{order_id}/tasks/{task_id}/candidates", response_model=list[CandidateOut])
async def get_task_candidates(
    order_id: uuid.UUID,
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[CandidateOut]:
    service = FulfillmentService(db)
    task = await service.get_task(order_id, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return [CandidateOut(**c) for c in await service.list_candidates(task_id)]


@router.post("/{order_id}/tasks/{task_id}/preferences", response_model=PreferenceSetOut)
async def set_task_preferences(
    order_id: uuid.UUID,
    task_id: uuid.UUID,
    body: SetPreferencesIn,
    db: AsyncSession = Depends(get_db),
    client: User = Depends(get_current_client),
) -> PreferenceSetOut:
    order = await db.get(OutcomeOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    service = FulfillmentService(db)
    task = await service.get_task(order_id, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        pref = await service.set_preferences(
            order=order,
            task=task,
            ranked_worker_ids=body.ranked_worker_ids,
            client_id=client.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    await db.commit()
    return PreferenceSetOut.from_orm_row(pref)


@router.get("/{order_id}/delivery", response_model=DeliveryBundleOut)
async def get_delivery(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DeliveryBundleOut:
    order = await db.get(OutcomeOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    delivery = DeliveryService(db)
    try:
        await delivery.ensure_delivered(order)
        bundle = await delivery.get_or_build_bundle(order)
    except (LookupError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    await db.commit()
    return DeliveryBundleOut.from_orm_row(bundle)


@router.post("/{order_id}/accept-delivery", response_model=TaskStatusOut)
async def accept_delivery(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    client: User = Depends(get_current_client),
) -> TaskStatusOut:
    order = await db.get(OutcomeOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    delivery = DeliveryService(db)
    try:
        order, _bundle = await delivery.accept_delivery(order=order, client_id=client.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    await db.commit()
    return TaskStatusOut(status=order.status)
