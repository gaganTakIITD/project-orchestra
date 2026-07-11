import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fulfillment import FulfillmentTask, OutcomeOrder
from app.orchestrator.events import EventWriter
from app.orchestrator.states import ActorType
from app.orchestrator.transitions import (
    ORDER_TRANSITIONS,
    TASK_TRANSITIONS,
    IllegalTransitionError,
    resolve_transition,
)


class TaskSpine:
    """Deterministic task state machine — AI never calls this directly."""

    AGGREGATE = "task"

    def __init__(self, session: AsyncSession):
        self.session = session
        self.events = EventWriter(session)

    async def transition(
        self,
        task: FulfillmentTask,
        event: str,
        *,
        actor_id: uuid.UUID | None = None,
        actor_type: ActorType | str = ActorType.SYSTEM,
        payload: dict[str, Any] | None = None,
    ) -> FulfillmentTask:
        from_status = task.status
        to_status = resolve_transition(self.AGGREGATE, TASK_TRANSITIONS, from_status, event)

        if from_status == to_status and event == "priority_expired":
            # Same-state promotion (backup worker) — still log the event
            pass
        else:
            task.status = to_status

        await self.events.emit(
            aggregate_type=self.AGGREGATE,
            aggregate_id=task.id,
            event_type=_event_log_name(event, from_status, to_status),
            actor_id=actor_id,
            actor_type=actor_type,
            payload={
                "from_status": from_status,
                "to_status": to_status,
                "trigger": event,
                **(payload or {}),
            },
        )
        await self.session.flush()
        return task


class OrderSpine:
    """Deterministic order state machine."""

    AGGREGATE = "order"

    def __init__(self, session: AsyncSession):
        self.session = session
        self.events = EventWriter(session)

    async def transition(
        self,
        order: OutcomeOrder,
        event: str,
        *,
        actor_id: uuid.UUID | None = None,
        actor_type: ActorType | str = ActorType.SYSTEM,
        payload: dict[str, Any] | None = None,
    ) -> OutcomeOrder:
        from_status = order.status
        to_status = resolve_transition(self.AGGREGATE, ORDER_TRANSITIONS, from_status, event)
        order.status = to_status

        await self.events.emit(
            aggregate_type=self.AGGREGATE,
            aggregate_id=order.id,
            event_type=_event_log_name(event, from_status, to_status),
            actor_id=actor_id,
            actor_type=actor_type,
            payload={
                "from_status": from_status,
                "to_status": to_status,
                "trigger": event,
                **(payload or {}),
            },
        )
        await self.session.flush()
        return order


def _event_log_name(trigger: str, from_status: str, to_status: str) -> str:
    """Map internal trigger to catalog event names where possible."""
    catalog = {
        "dependencies_met": "TaskReady",
        "preferences_set": "PreferencesSet",
        "interest_accepted": "InterestAccepted",
        "priority_granted": "ActivationGranted",
        "priority_expired": "ActivationExpired",
        "mutual_start_confirmed": "MutualStartConfirmed",
        "submitted": "SubmissionReceived",
        "qa_pass": "QualityPassed",
        "qa_fail": "QualityFailed",
        "plan_and_preferences_set": "PreferencesSet",
        "first_mutual_start": "MutualStartConfirmed",
        "bundle_ready": "OutcomeDelivered",
        "client_accept": "OutcomeClosed",
    }
    return catalog.get(trigger, f"StateChanged:{from_status}->{to_status}")
