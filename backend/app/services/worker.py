import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fulfillment import FulfillmentTask
from app.models.identity import User, WorkerProfileRecord
from app.orchestrator.events import EventWriter
from app.orchestrator.states import ActorType, TaskStatus
from app.schemas.worker import (
    PROFILE_LIVE_THRESHOLD,
    WorkerProfileUpsert,
    compute_profile_completion_pct,
)

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
        self.events = EventWriter(session)

    async def get_profile(self, user_id: uuid.UUID) -> tuple[User, WorkerProfileRecord] | None:
        user = await self.session.get(User, user_id)
        if user is None:
            return None
        profile = await self.session.get(WorkerProfileRecord, user_id)
        # Auto-create empty row only when actively in the worker portal role.
        if profile is None and user.role == "worker":
            profile = WorkerProfileRecord(user_id=user.id, headline="", bio="")
            self.session.add(profile)
            await self.session.flush()
        if profile is None:
            return None
        return user, profile

    async def upsert_profile(
        self, *, user: User, body: WorkerProfileUpsert
    ) -> tuple[User, WorkerProfileRecord]:
        """Create or update WorkerProfileRecord; recompute completion; gate live ≥70%."""
        if user.role not in ("worker", "admin"):
            raise ValueError("Only workers can upsert a worker profile")
        if user.role == "admin":
            # Keep admin identity but ensure a profile row exists for the lane.
            pass

        if body.full_name is not None and body.full_name.strip():
            user.full_name = body.full_name.strip()

        skills = [s.model_dump() for s in body.skills]
        tools = [t.model_dump() for t in body.tools]
        task_types = [tt.model_dump() for tt in body.task_types]
        portfolio = []
        for item in body.portfolio:
            row = item.model_dump()
            if not row.get("worker_id"):
                row["worker_id"] = str(user.id)
            portfolio.append(row)

        completion = compute_profile_completion_pct(
            headline=body.headline,
            bio=body.bio,
            skills=skills,
            tools=tools,
            task_types=task_types,
            portfolio=portfolio,
            availability_status=body.availability_status,
            payout_min=body.payout_min,
            payout_max=body.payout_max,
            github_url=body.github_url,
            figma_url=body.figma_url,
            behance_url=body.behance_url,
            linkedin_url=body.linkedin_url,
        )
        live = bool(body.is_active) and completion >= PROFILE_LIVE_THRESHOLD

        profile = await self.session.get(WorkerProfileRecord, user.id)
        created = profile is None
        if profile is None:
            profile = WorkerProfileRecord(user_id=user.id)
            self.session.add(profile)

        profile.community_type = body.community_type
        profile.headline = body.headline
        profile.bio = body.bio
        profile.availability_status = body.availability_status
        profile.weekly_hours_available = body.weekly_hours_available
        profile.max_concurrent_tasks = body.max_concurrent_tasks
        profile.payout_min = body.payout_min
        profile.payout_max = body.payout_max
        profile.github_url = body.github_url
        profile.figma_url = body.figma_url
        profile.behance_url = body.behance_url
        profile.linkedin_url = body.linkedin_url
        profile.skills = skills
        profile.tools = tools
        profile.task_types = task_types
        profile.portfolio = portfolio
        profile.profile_completion_pct = completion
        profile.is_active = live

        await self.events.emit(
            aggregate_type="worker_profile",
            aggregate_id=user.id,
            event_type="ProfileCreated" if created else "ProfileUpdated",
            actor_id=user.id,
            actor_type=ActorType.WORKER,
            payload={
                "profile_completion_pct": completion,
                "is_active": live,
                "live_threshold": PROFILE_LIVE_THRESHOLD,
            },
        )
        await self.session.flush()
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
