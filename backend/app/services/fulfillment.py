import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.fixtures.architect import build_plan_fixture, match_candidates_fixture
from app.models.catalog import TaskType
from app.models.fulfillment import FulfillmentPlan, FulfillmentTask, OutcomeOrder, TaskPreferenceSet
from app.models.commerce import OutcomeSpecRecord
from app.orchestrator.events import EventWriter
from app.orchestrator.spine import OrderSpine, TaskSpine
from app.orchestrator.states import ActorType, TaskStatus


class FulfillmentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.events = EventWriter(session)

    async def build_plan(self, *, order: OutcomeOrder, spec: OutcomeSpecRecord) -> FulfillmentPlan:
        existing = await self.session.scalar(
            select(FulfillmentPlan.id).where(FulfillmentPlan.order_id == order.id)
        )
        if existing:
            return await self.get_plan_for_order(order.id)

        if order.deadline is None:
            raise ValueError("Order deadline required to build fulfillment plan")

        blueprint = build_plan_fixture(
            order_id=order.id,
            order_deadline=order.deadline,
            revision_limit=order.revision_limit,
        )

        plan = FulfillmentPlan(
            order_id=order.id,
            milestones=blueprint["milestones"],
            critical_path_hours=blueprint["critical_path_hours"],
        )
        self.session.add(plan)
        await self.session.flush()

        task_spine = TaskSpine(self.session)
        for task_def in blueprint["tasks"]:
            task_type = await self._task_type_by_slug(task_def["task_type_slug"])
            task = FulfillmentTask(
                id=task_def["id"],
                plan_id=plan.id,
                order_id=order.id,
                task_type_id=task_type.id if task_type else None,
                task_type_slug=task_def["task_type_slug"],
                title=task_def["title"],
                description=task_def["description"],
                status=TaskStatus.BLOCKED,
                sequence_order=task_def["sequence_order"],
                acceptance_criteria=task_def["acceptance_criteria"],
                payout_amount=Decimal(str(task_def["payout_amount"])),
                deadline=task_def["deadline"],
                revision_limit=order.revision_limit,
                depends_on=task_def["depends_on"],
            )
            self.session.add(task)
            await self.session.flush()

            if not task_def["depends_on"]:
                await task_spine.transition(
                    task,
                    "dependencies_met",
                    actor_type=ActorType.SYSTEM,
                    payload={"source": "architect_fixture"},
                )

        await self.events.emit(
            aggregate_type="order",
            aggregate_id=order.id,
            event_type="PlanApproved",
            actor_type=ActorType.AI,
            payload={"task_count": len(blueprint["tasks"]), "spec_id": str(spec.id)},
        )
        await self.session.flush()
        return plan

    async def get_plan_for_order(self, order_id: uuid.UUID) -> FulfillmentPlan:
        plan = await self.session.scalar(
            select(FulfillmentPlan).where(FulfillmentPlan.order_id == order_id)
        )
        if plan is None:
            raise LookupError(f"No plan for order {order_id}")
        return plan

    async def list_tasks_for_order(self, order_id: uuid.UUID) -> list[FulfillmentTask]:
        result = await self.session.execute(
            select(FulfillmentTask)
            .where(FulfillmentTask.order_id == order_id)
            .order_by(FulfillmentTask.sequence_order)
        )
        return list(result.scalars().all())

    async def get_task(self, order_id: uuid.UUID, task_id: uuid.UUID) -> FulfillmentTask | None:
        return await self.session.scalar(
            select(FulfillmentTask).where(
                FulfillmentTask.order_id == order_id,
                FulfillmentTask.id == task_id,
            )
        )

    def list_candidates(self, task_id: uuid.UUID) -> list[dict]:
        return match_candidates_fixture(task_id=task_id)

    async def set_preferences(
        self,
        *,
        order: OutcomeOrder,
        task: FulfillmentTask,
        ranked_worker_ids: list[str],
        client_id: uuid.UUID,
    ) -> TaskPreferenceSet:
        if task.status not in (TaskStatus.READY, TaskStatus.INVITED):
            raise ValueError(f"Cannot set preferences when task is {task.status!r}")

        entries = [{"worker_id": wid, "rank": i + 1} for i, wid in enumerate(ranked_worker_ids)]
        pref = TaskPreferenceSet(
            task_id=task.id,
            order_id=order.id,
            entries=entries,
        )
        self.session.add(pref)

        task_spine = TaskSpine(self.session)
        if task.status == TaskStatus.READY:
            await task_spine.transition(
                task,
                "preferences_set",
                actor_id=client_id,
                actor_type=ActorType.CLIENT,
                payload={"ranked_worker_ids": ranked_worker_ids},
            )

        order_spine = OrderSpine(self.session)
        if order.status == "confirmed":
            await order_spine.transition(
                order,
                "plan_and_preferences_set",
                actor_id=client_id,
                actor_type=ActorType.CLIENT,
                payload={"task_id": str(task.id)},
            )

        await self.session.flush()
        return pref

    async def _task_type_by_slug(self, slug: str) -> TaskType | None:
        return await self.session.scalar(select(TaskType).where(TaskType.slug == slug))
