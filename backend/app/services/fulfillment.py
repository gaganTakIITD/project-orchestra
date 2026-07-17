import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gateway import generate_plan_proposal, generate_task_packet_proposal
from app.ai.matcher import match_candidates
from app.ai.matcher_chat import required_ranked_count
from app.models.catalog import TaskType
from app.models.fulfillment import (
    CharterRecord,
    FulfillmentPlan,
    FulfillmentTask,
    OutcomeOrder,
    TaskPacketRecord,
    TaskPreferenceSet,
)
from app.models.commerce import OutcomeSpecRecord
from app.models.platform import AiDecisionLog
from app.orchestrator.events import EventWriter
from app.orchestrator.spine import OrderSpine, TaskSpine
from app.orchestrator.states import ActorType, TaskStatus


class FulfillmentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.events = EventWriter(session)

    async def build_plan(
        self,
        *,
        order: OutcomeOrder,
        spec: OutcomeSpecRecord,
        force_fixtures: bool = False,
    ) -> FulfillmentPlan:
        existing = await self.session.scalar(
            select(FulfillmentPlan.id).where(FulfillmentPlan.order_id == order.id)
        )
        if existing:
            return await self.get_plan_for_order(order.id)

        if order.deadline is None:
            raise ValueError("Order deadline required to build fulfillment plan")

        mapped = list(spec.mapped_task_types or [])
        proposal = generate_plan_proposal(
            order_id=order.id,
            order_deadline=order.deadline,
            revision_limit=order.revision_limit,
            order_price=order.price,
            spec={
                "outcome_statement": spec.outcome_statement,
                "mapped_task_types": mapped,
                "workflow_summary": getattr(spec, "workflow_summary", None) or "",
                "deliverables": spec.deliverables or [],
                "acceptance_criteria": spec.acceptance_criteria or [],
            },
            force_fixtures=force_fixtures,
        )
        blueprint = proposal.plan

        self.session.add(
            AiDecisionLog(
                session_id=None,
                agent_type="architect",
                source=proposal.source,
                model=proposal.model,
                input_text=(spec.outcome_statement or "")[:2000],
                output_draft={
                    "order_id": str(order.id),
                    "task_count": len(blueprint["tasks"]),
                    "mapped_task_types": mapped,
                    "task_slugs": [t["task_type_slug"] for t in blueprint["tasks"]],
                    "critical_path_hours": blueprint.get("critical_path_hours"),
                },
                reply=None,
                confidence=proposal.confidence,
                latency_ms=proposal.latency_ms,
                error=proposal.error,
            )
        )

        plan = FulfillmentPlan(
            order_id=order.id,
            milestones=blueprint["milestones"],
            critical_path_hours=blueprint["critical_path_hours"],
        )
        self.session.add(plan)
        await self.session.flush()

        created_tasks: list[FulfillmentTask] = []
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
            created_tasks.append(task)

            if not task_def["depends_on"]:
                await task_spine.transition(
                    task,
                    "dependencies_met",
                    actor_type=ActorType.SYSTEM,
                    payload={"source": "architect"},
                )

        # Task Packet Generator — Charter + job card per task (from OutcomeSpec slice)
        title_by_id = {str(t.id): t.title for t in created_tasks}
        spec_dict = {
            "outcome_statement": spec.outcome_statement,
            "deliverables": spec.deliverables or [],
            "acceptance_criteria": spec.acceptance_criteria or [],
            "out_of_scope": spec.out_of_scope or [],
            "client_inputs_required": spec.client_inputs_required or [],
        }
        for task in created_tasks:
            dep_titles = [title_by_id[d] for d in (task.depends_on or []) if d in title_by_id]
            await self._create_charter_and_packet(
                order=order,
                task=task,
                spec_dict=spec_dict,
                dependency_titles=dep_titles,
                force_fixtures=force_fixtures,
            )

        await self.events.emit(
            aggregate_type="order",
            aggregate_id=order.id,
            event_type="PlanApproved",
            actor_type=ActorType.AI,
            payload={
                "task_count": len(blueprint["tasks"]),
                "spec_id": str(spec.id),
                "architect_source": proposal.source,
            },
        )
        await self.session.flush()
        return plan

    async def _create_charter_and_packet(
        self,
        *,
        order: OutcomeOrder,
        task: FulfillmentTask,
        spec_dict: dict,
        dependency_titles: list[str],
        force_fixtures: bool = False,
    ) -> tuple[CharterRecord, TaskPacketRecord]:
        proposal = generate_task_packet_proposal(
            order_id=order.id,
            task=task,
            spec=spec_dict,
            order_price_share=float(task.payout_amount),
            order_deadline=order.deadline,
            revision_limit=order.revision_limit,
            dependency_titles=dependency_titles,
            force_fixtures=force_fixtures,
        )
        charter_fields = proposal.charter
        packet_fields = proposal.packet

        self.session.add(
            AiDecisionLog(
                session_id=None,
                agent_type="task_packet_generator",
                source=proposal.source,
                model=proposal.model,
                input_text=(task.title or "")[:2000],
                output_draft={
                    "task_id": str(task.id),
                    "order_id": str(order.id),
                    "brief": packet_fields.get("brief"),
                    "checklist": packet_fields.get("checklist"),
                    "charter_snapshot": charter_fields.get("snapshot"),
                },
                reply=packet_fields.get("brief"),
                confidence=proposal.confidence,
                latency_ms=proposal.latency_ms,
                error=proposal.error,
            )
        )

        charter = CharterRecord(
            id=charter_fields["id"],
            order_id=charter_fields["order_id"],
            task_id=charter_fields["task_id"],
            version=charter_fields["version"],
            snapshot=charter_fields["snapshot"],
            mutual_start_at=charter_fields["mutual_start_at"],
        )
        self.session.add(charter)
        await self.session.flush()

        packet = TaskPacketRecord(
            id=packet_fields["id"],
            task_id=packet_fields["task_id"],
            charter_id=packet_fields["charter_id"],
            version=packet_fields["version"],
            brief=packet_fields["brief"],
            checklist=packet_fields["checklist"],
            client_inputs=packet_fields["client_inputs"],
            dependencies=packet_fields["dependencies"],
            references=packet_fields["references"],
        )
        self.session.add(packet)
        await self.session.flush()
        return charter, packet

    async def get_charter_for_task(self, task_id: uuid.UUID) -> CharterRecord | None:
        return await self.session.scalar(select(CharterRecord).where(CharterRecord.task_id == task_id))

    async def get_packet_for_task(self, task_id: uuid.UUID) -> TaskPacketRecord | None:
        return await self.session.scalar(
            select(TaskPacketRecord).where(TaskPacketRecord.task_id == task_id)
        )

    async def get_task_by_id(self, task_id: uuid.UUID) -> FulfillmentTask | None:
        return await self.session.get(FulfillmentTask, task_id)

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

    async def list_candidates(self, task_id: uuid.UUID) -> list[dict]:
        task = await self.session.get(FulfillmentTask, task_id)
        if task is None:
            return []
        return await match_candidates(self.session, task=task)

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

        candidates = await self.list_candidates(task.id)
        candidate_ids = {c["worker_id"] for c in candidates}
        min_needed = required_ranked_count(len(candidates))
        if len(ranked_worker_ids) < min_needed:
            raise ValueError(
                f"Need at least {min_needed} ranked worker(s) "
                f"(live pool has {len(candidates)} candidate(s))"
            )
        if not candidate_ids:
            raise ValueError("No live candidates available for this task")
        unknown = [wid for wid in ranked_worker_ids if wid not in candidate_ids]
        if unknown:
            raise ValueError(f"Ranked workers not in candidate pool: {unknown}")

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
