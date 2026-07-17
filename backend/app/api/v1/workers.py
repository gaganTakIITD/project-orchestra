from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.identity import User
from app.schemas.fulfillment import FulfillmentTaskOut
from app.schemas.worker import WorkerProfileOut, WorkerProfileUpsert
from app.services.auth import get_current_worker, resolve_user
from app.services.worker import WorkerService

router = APIRouter(prefix="/workers", tags=["workers"])


@router.get("/profile", response_model=WorkerProfileOut)
async def get_worker_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> WorkerProfileOut:
    """Return the caller's worker profile if it exists (any portal role).

    Resolves identity with prefer_role=worker so demo mode returns the seeded
    worker without a header; Clerk JWT identity is the same either way, so a
    hybrid account can still read their profile from /account as client.
    """
    user = await resolve_user(db, request, prefer_role="worker")
    service = WorkerService(db)
    result = await service.get_profile(user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="Worker profile not found")
    owner, profile = result
    # Persist auto-created empty profiles from get_profile.
    await db.commit()
    from app.services.worker_stats import WorkerStatsService

    tt_stats = await WorkerStatsService(db).list_for_worker(owner.id)
    return WorkerProfileOut.from_orm_rows(owner, profile, task_type_stats=tt_stats)


@router.patch("/profile", response_model=WorkerProfileOut)
@router.post("/profile", response_model=WorkerProfileOut)
async def upsert_worker_profile(
    body: WorkerProfileUpsert,
    db: AsyncSession = Depends(get_db),
    worker: User = Depends(get_current_worker),
) -> WorkerProfileOut:
    service = WorkerService(db)
    try:
        user, profile = await service.upsert_profile(user=worker, body=body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    await db.commit()
    await db.refresh(user)
    await db.refresh(profile)
    return WorkerProfileOut.from_orm_rows(user, profile)


@router.get("/me/tasks", response_model=list[FulfillmentTaskOut])
async def list_my_tasks(
    db: AsyncSession = Depends(get_db),
    worker: User = Depends(get_current_worker),
) -> list[FulfillmentTaskOut]:
    service = WorkerService(db)
    tasks = await service.list_my_tasks(worker.id)
    return [FulfillmentTaskOut.from_orm_row(t) for t in tasks]
