import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.fulfillment import (
    DiscussionMessageIn,
    DiscussionThreadOut,
    SubmitWorkIn,
    TaskStatusOut,
)
from app.schemas.worker import CharterOut, TaskPacketOut
from app.services.auth import get_demo_client, get_demo_worker
from app.services.discussion import DiscussionService
from app.services.fulfillment import FulfillmentService
from app.services.task_lifecycle import TaskLifecycleService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}/charter", response_model=CharterOut)
async def get_charter(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> CharterOut:
    service = FulfillmentService(db)
    task = await service.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    charter = await service.get_charter_for_task(task_id)
    if charter is None:
        raise HTTPException(status_code=404, detail="Charter not found for task")
    return CharterOut.from_orm_row(charter)


@router.get("/{task_id}/packet", response_model=TaskPacketOut)
async def get_task_packet(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TaskPacketOut:
    service = FulfillmentService(db)
    task = await service.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    packet = await service.get_packet_for_task(task_id)
    if packet is None:
        raise HTTPException(status_code=404, detail="Task packet not found")
    return TaskPacketOut.from_orm_row(packet)


@router.post("/{task_id}/accept-interest", response_model=TaskStatusOut)
async def accept_interest(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TaskStatusOut:
    worker = await get_demo_worker(db)
    fulfillment = FulfillmentService(db)
    task = await fulfillment.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    lifecycle = TaskLifecycleService(db)
    try:
        task = await lifecycle.accept_interest(task=task, worker=worker)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    await db.commit()
    # Contract: frontend mock returns "accepted" (actual Spine state is priority_active).
    return TaskStatusOut(status="accepted")


@router.post("/{task_id}/ready-to-start", response_model=TaskStatusOut)
async def ready_to_start(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TaskStatusOut:
    worker = await get_demo_worker(db)
    fulfillment = FulfillmentService(db)
    task = await fulfillment.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    lifecycle = TaskLifecycleService(db)
    try:
        task = await lifecycle.ready_to_start(task=task, worker=worker)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    await db.commit()
    return TaskStatusOut(status=task.status)


@router.post("/{task_id}/submit", response_model=TaskStatusOut)
async def submit_work(
    task_id: uuid.UUID,
    body: SubmitWorkIn,
    db: AsyncSession = Depends(get_db),
) -> TaskStatusOut:
    worker = await get_demo_worker(db)
    fulfillment = FulfillmentService(db)
    task = await fulfillment.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    lifecycle = TaskLifecycleService(db)
    try:
        task, _submission = await lifecycle.submit(
            task=task,
            worker=worker,
            notes=body.notes,
            asset_urls=body.asset_urls,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    await db.commit()
    return TaskStatusOut(status=task.status)


@router.get("/{task_id}/discussion", response_model=DiscussionThreadOut)
async def get_discussion(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DiscussionThreadOut:
    fulfillment = FulfillmentService(db)
    task = await fulfillment.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    discussion = DiscussionService(db)
    thread = await discussion.get_or_create_thread(task)
    messages = await discussion.list_messages(thread.id)
    await db.commit()
    return DiscussionThreadOut.from_orm_rows(thread, messages)


@router.post("/{task_id}/discussion", response_model=DiscussionThreadOut)
async def post_discussion_message(
    task_id: uuid.UUID,
    body: DiscussionMessageIn,
    db: AsyncSession = Depends(get_db),
) -> DiscussionThreadOut:
    # Demo stub: client posts by default (client close loop). Workers can use same endpoint later.
    sender = await get_demo_client(db)
    fulfillment = FulfillmentService(db)
    task = await fulfillment.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    discussion = DiscussionService(db)
    thread, messages = await discussion.post_message(
        task=task,
        sender=sender,
        body=body.body,
        message_type=body.message_type,
        attachments=body.attachments,
    )
    await db.commit()
    return DiscussionThreadOut.from_orm_rows(thread, messages)
