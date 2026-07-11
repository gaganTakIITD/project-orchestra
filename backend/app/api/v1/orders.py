import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.fulfillment import OutcomeOrder
from app.schemas.commerce import OutcomeOrderOut
from app.schemas.fulfillment import (
    CandidateOut,
    FulfillmentPlanOut,
    PreferenceSetOut,
    SetPreferencesIn,
)
from app.services.auth import get_demo_client
from app.services.fulfillment import FulfillmentService

router = APIRouter(prefix="/orders", tags=["orders"])


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
    return [CandidateOut(**c) for c in service.list_candidates(task_id)]


@router.post("/{order_id}/tasks/{task_id}/preferences", response_model=PreferenceSetOut)
async def set_task_preferences(
    order_id: uuid.UUID,
    task_id: uuid.UUID,
    body: SetPreferencesIn,
    db: AsyncSession = Depends(get_db),
) -> PreferenceSetOut:
    client = await get_demo_client(db)
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
