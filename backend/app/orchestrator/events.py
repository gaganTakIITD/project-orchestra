import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import EventLog
from app.orchestrator.event_bus import get_event_bus
from app.orchestrator.states import ActorType


class EventWriter:
    """Append-only event log writer — must run in the same DB transaction as domain writes."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def emit(
        self,
        *,
        aggregate_type: str,
        aggregate_id: uuid.UUID,
        event_type: str,
        actor_id: uuid.UUID | None = None,
        actor_type: ActorType | str = ActorType.SYSTEM,
        payload: dict[str, Any] | None = None,
    ) -> EventLog:
        body = dict(payload or {})
        if aggregate_type == "task" and "order_id" not in body:
            from app.models.fulfillment import FulfillmentTask

            task = await self.session.get(FulfillmentTask, aggregate_id)
            if task is not None:
                body["order_id"] = str(task.order_id)

        entry = EventLog(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            actor_id=actor_id,
            actor_type=str(actor_type),
            payload=body,
        )
        self.session.add(entry)
        await self.session.flush()

        message: dict[str, Any] = {
            "aggregate_type": aggregate_type,
            "aggregate_id": str(aggregate_id),
            "event_type": event_type,
            "actor_id": str(actor_id) if actor_id else None,
            "actor_type": str(actor_type),
            "payload": body,
        }
        if aggregate_type == "task" and body.get("order_id"):
            message["order_id"] = str(body["order_id"])

        bus = get_event_bus()
        if aggregate_type == "order":
            await bus.publish(f"order:{aggregate_id}", message)
        elif aggregate_type == "task":
            await bus.publish(f"task:{aggregate_id}", message)
            order_id = body.get("order_id")
            if order_id:
                await bus.publish(f"order:{order_id}", message)

        return entry
