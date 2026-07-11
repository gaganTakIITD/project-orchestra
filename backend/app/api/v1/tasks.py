import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.worker import CharterOut, TaskPacketOut
from app.services.fulfillment import FulfillmentService

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
