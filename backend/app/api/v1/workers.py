from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.identity import User
from app.schemas.fulfillment import FulfillmentTaskOut
from app.schemas.worker import WorkerProfileOut
from app.services.auth import get_current_worker
from app.services.worker import WorkerService

router = APIRouter(prefix="/workers", tags=["workers"])


@router.get("/profile", response_model=WorkerProfileOut)
async def get_worker_profile(
    db: AsyncSession = Depends(get_db),
    worker: User = Depends(get_current_worker),
) -> WorkerProfileOut:
    service = WorkerService(db)
    result = await service.get_profile(worker.id)
    if result is None:
        raise HTTPException(status_code=404, detail="Worker profile not found")
    user, profile = result
    return WorkerProfileOut.from_orm_rows(user, profile)


@router.get("/me/tasks", response_model=list[FulfillmentTaskOut])
async def list_my_tasks(
    db: AsyncSession = Depends(get_db),
    worker: User = Depends(get_current_worker),
) -> list[FulfillmentTaskOut]:
    service = WorkerService(db)
    tasks = await service.list_my_tasks(worker.id)
    return [FulfillmentTaskOut.from_orm_row(t) for t in tasks]
