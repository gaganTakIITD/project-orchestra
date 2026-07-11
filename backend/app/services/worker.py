import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fulfillment import FulfillmentTask
from app.models.identity import User, WorkerProfileRecord
from app.orchestrator.states import TaskStatus

# Statuses a worker would see in their inbox / active work.
WORKER_INBOX_STATUSES = (
    TaskStatus.READY,
    TaskStatus.INVITED,
    TaskStatus.INTEREST_POOL,
    TaskStatus.PRIORITY_ACTIVE,
    TaskStatus.START_REQUESTED,
    TaskStatus.MUTUAL_START,
    TaskStatus.IN_PROGRESS,
    TaskStatus.SUBMITTED,
    TaskStatus.REWORK,
)


class WorkerService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_profile(self, user_id: uuid.UUID) -> tuple[User, WorkerProfileRecord] | None:
        user = await self.session.get(User, user_id)
        if user is None or user.role != "worker":
            return None
        profile = await self.session.get(WorkerProfileRecord, user_id)
        if profile is None:
            return None
        return user, profile

    async def list_my_tasks(self, worker_id: uuid.UUID) -> list[FulfillmentTask]:
        """Inbox: assigned to worker, or open pool (ready/invited/…) for demo matching."""
        result = await self.session.execute(
            select(FulfillmentTask)
            .where(
                FulfillmentTask.status.in_(WORKER_INBOX_STATUSES),
                or_(
                    FulfillmentTask.assigned_worker_id == worker_id,
                    FulfillmentTask.assigned_worker_id.is_(None),
                ),
            )
            .order_by(FulfillmentTask.sequence_order)
        )
        return list(result.scalars().all())
