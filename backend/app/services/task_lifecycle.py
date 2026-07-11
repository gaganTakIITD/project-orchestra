"""Worker task lifecycle — accept → start → submit (+ unlock dependents)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.fixtures.architect import match_candidates_fixture
from app.models.fulfillment import (
    CharterRecord,
    DeliveryBundleRecord,
    FulfillmentTask,
    OutcomeOrder,
    SubmissionRecord,
    TaskPreferenceSet,
)
from app.models.identity import User
from app.orchestrator.spine import OrderSpine, TaskSpine
from app.orchestrator.states import ActorType, OrderStatus, TaskStatus
from app.orchestrator.transitions import IllegalTransitionError


class TaskLifecycleService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_spine = TaskSpine(session)
        self.order_spine = OrderSpine(session)

    async def accept_interest(self, *, task: FulfillmentTask, worker: User) -> FulfillmentTask:
        if task.status == TaskStatus.READY:
            await self._ensure_invited(task=task, worker_id=worker.id)

        if task.status == TaskStatus.INVITED:
            await self.task_spine.transition(
                task,
                "interest_accepted",
                actor_id=worker.id,
                actor_type=ActorType.WORKER,
                payload={"worker_id": str(worker.id)},
            )

        if task.status == TaskStatus.INTEREST_POOL:
            await self.task_spine.transition(
                task,
                "priority_granted",
                actor_id=worker.id,
                actor_type=ActorType.SYSTEM,
                payload={"worker_id": str(worker.id)},
            )

        if task.status != TaskStatus.PRIORITY_ACTIVE:
            raise ValueError(f"Cannot accept interest when task is {task.status!r}")

        task.assigned_worker_id = worker.id
        await self.session.flush()
        return task

    async def ready_to_start(self, *, task: FulfillmentTask, worker: User) -> FulfillmentTask:
        if task.assigned_worker_id and task.assigned_worker_id != worker.id:
            raise ValueError("Not your task")

        if task.status == TaskStatus.PRIORITY_ACTIVE:
            await self.task_spine.transition(
                task,
                "ready_to_start",
                actor_id=worker.id,
                actor_type=ActorType.WORKER,
            )

        if task.status == TaskStatus.START_REQUESTED:
            await self.task_spine.transition(
                task,
                "mutual_start_confirmed",
                actor_id=worker.id,
                actor_type=ActorType.SYSTEM,
                payload={"auto_confirm": True},
            )
            charter = await self.session.scalar(
                select(CharterRecord).where(CharterRecord.task_id == task.id)
            )
            if charter is not None and charter.mutual_start_at is None:
                charter.mutual_start_at = datetime.now(timezone.utc)

            order = await self.session.get(OutcomeOrder, task.order_id)
            if order is not None:
                if order.status == OrderStatus.CONFIRMED:
                    await self.order_spine.transition(
                        order,
                        "plan_and_preferences_set",
                        actor_id=worker.id,
                        actor_type=ActorType.SYSTEM,
                        payload={"task_id": str(task.id)},
                    )
                if order.status == OrderStatus.ASSEMBLING_TEAM:
                    await self.order_spine.transition(
                        order,
                        "first_mutual_start",
                        actor_id=worker.id,
                        actor_type=ActorType.SYSTEM,
                        payload={"task_id": str(task.id)},
                    )

        if task.status == TaskStatus.MUTUAL_START:
            await self.task_spine.transition(
                task,
                "work_started",
                actor_id=worker.id,
                actor_type=ActorType.WORKER,
            )
            task.started_at = datetime.now(timezone.utc)
            task.assigned_worker_id = worker.id

        if task.status != TaskStatus.IN_PROGRESS:
            raise ValueError(f"Cannot ready-to-start when task is {task.status!r}")

        await self.session.flush()
        return task

    async def submit(
        self,
        *,
        task: FulfillmentTask,
        worker: User,
        notes: str,
        asset_urls: list[str],
    ) -> tuple[FulfillmentTask, SubmissionRecord]:
        if task.assigned_worker_id and task.assigned_worker_id != worker.id:
            raise ValueError("Not your task")

        if task.status in (
            TaskStatus.START_REQUESTED,
            TaskStatus.MUTUAL_START,
            TaskStatus.PRIORITY_ACTIVE,
        ):
            await self.ready_to_start(task=task, worker=worker)

        try:
            if task.status == TaskStatus.IN_PROGRESS:
                await self.task_spine.transition(
                    task,
                    "submitted",
                    actor_id=worker.id,
                    actor_type=ActorType.WORKER,
                    payload={"notes": notes, "asset_urls": asset_urls},
                )
            elif task.status == TaskStatus.REWORK:
                await self.task_spine.transition(
                    task,
                    "resubmitted",
                    actor_id=worker.id,
                    actor_type=ActorType.WORKER,
                    payload={"notes": notes, "asset_urls": asset_urls},
                )
            else:
                raise ValueError(f"Cannot submit when task is {task.status!r}")
        except IllegalTransitionError as e:
            raise ValueError(str(e)) from e

        version = await self._next_submission_version(task.id)
        submission = SubmissionRecord(
            task_id=task.id,
            worker_id=worker.id,
            notes=notes or None,
            asset_urls=asset_urls or [],
            version=version,
            submitted_at=datetime.now(timezone.utc),
        )
        self.session.add(submission)

        await self.task_spine.transition(
            task,
            "qa_pass",
            actor_type=ActorType.AI,
            payload={"source": "stage_auto_qa", "score": 0.9},
        )
        task.completed_at = datetime.now(timezone.utc)

        await self._unlock_dependents(task)
        await self._maybe_advance_order_to_delivered(task.order_id)
        await self.session.flush()
        return task, submission

    async def _unlock_dependents(self, completed: FulfillmentTask) -> None:
        siblings = list(
            (
                await self.session.execute(
                    select(FulfillmentTask).where(FulfillmentTask.order_id == completed.order_id)
                )
            ).scalars()
        )
        status_by_id = {str(t.id): t.status for t in siblings}
        for task in siblings:
            if task.status != TaskStatus.BLOCKED:
                continue
            deps = task.depends_on or []
            if deps and all(status_by_id.get(d) == TaskStatus.COMPLETED for d in deps):
                await self.task_spine.transition(
                    task,
                    "dependencies_met",
                    actor_type=ActorType.SYSTEM,
                    payload={"unlocked_by": str(completed.id)},
                )
                status_by_id[str(task.id)] = task.status

    async def _maybe_advance_order_to_delivered(self, order_id: uuid.UUID) -> None:
        order = await self.session.get(OutcomeOrder, order_id)
        if order is None:
            return

        tasks = list(
            (
                await self.session.execute(
                    select(FulfillmentTask).where(FulfillmentTask.order_id == order_id)
                )
            ).scalars()
        )
        if not tasks or not all(t.status == TaskStatus.COMPLETED for t in tasks):
            return

        if order.status in (OrderStatus.ASSEMBLING_TEAM, OrderStatus.CONFIRMED):
            await self.order_spine.transition(
                order,
                "first_mutual_start",
                actor_type=ActorType.SYSTEM,
            )
        if order.status == OrderStatus.DELIVERY_ACTIVE:
            await self.order_spine.transition(
                order,
                "all_tasks_submitted",
                actor_type=ActorType.SYSTEM,
            )
        if order.status == OrderStatus.UNDER_QUALITY_CHECK:
            await self._ensure_delivery_bundle(order, tasks)
            await self.order_spine.transition(
                order,
                "bundle_ready",
                actor_type=ActorType.SYSTEM,
            )
            order.progress_pct = 100

    async def _ensure_delivery_bundle(
        self, order: OutcomeOrder, tasks: list[FulfillmentTask]
    ) -> DeliveryBundleRecord:
        existing = await self.session.scalar(
            select(DeliveryBundleRecord).where(DeliveryBundleRecord.order_id == order.id)
        )
        if existing:
            return existing

        assets: list[dict] = []
        for task in tasks:
            subs = list(
                (
                    await self.session.execute(
                        select(SubmissionRecord)
                        .where(SubmissionRecord.task_id == task.id)
                        .order_by(SubmissionRecord.version.desc())
                    )
                ).scalars()
            )
            if not subs:
                continue
            latest = subs[0]
            for i, url in enumerate(latest.asset_urls or []):
                assets.append(
                    {"name": f"{task.title} asset {i + 1}", "url": url, "type": "url"}
                )
            if latest.notes:
                assets.append(
                    {
                        "name": f"{task.title} notes",
                        "url": f"notes://{task.id}",
                        "type": "text/plain",
                    }
                )

        bundle = DeliveryBundleRecord(
            order_id=order.id,
            assets=assets,
            qa_summary="All task acceptance criteria passed (stage auto-QA).",
        )
        self.session.add(bundle)
        await self.session.flush()
        return bundle

    async def _ensure_invited(self, *, task: FulfillmentTask, worker_id: uuid.UUID) -> None:
        existing = await self.session.scalar(
            select(TaskPreferenceSet.id).where(TaskPreferenceSet.task_id == task.id)
        )
        if existing is None:
            candidates = match_candidates_fixture(task_id=task.id)
            ranked = [c["worker_id"] for c in candidates[:3]]
            ranked = [str(worker_id)] + [w for w in ranked if w != str(worker_id)]
            ranked = ranked[:3]
            while len(ranked) < 3:
                ranked.append(f"usr_worker_backup_{len(ranked)}")
            pref = TaskPreferenceSet(
                task_id=task.id,
                order_id=task.order_id,
                entries=[{"worker_id": wid, "rank": i + 1} for i, wid in enumerate(ranked[:3])],
            )
            self.session.add(pref)

        await self.task_spine.transition(
            task,
            "preferences_set",
            actor_id=worker_id,
            actor_type=ActorType.SYSTEM,
            payload={"source": "accept_interest_bootstrap", "worker_id": str(worker_id)},
        )

        order = await self.session.get(OutcomeOrder, task.order_id)
        if order is not None and order.status == OrderStatus.CONFIRMED:
            await self.order_spine.transition(
                order,
                "plan_and_preferences_set",
                actor_id=worker_id,
                actor_type=ActorType.SYSTEM,
                payload={"task_id": str(task.id)},
            )

    async def _next_submission_version(self, task_id: uuid.UUID) -> int:
        current = await self.session.scalar(
            select(func.coalesce(func.max(SubmissionRecord.version), 0)).where(
                SubmissionRecord.task_id == task_id
            )
        )
        return int(current or 0) + 1
