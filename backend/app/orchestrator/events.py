import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import EventLog
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
        entry = EventLog(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            actor_id=actor_id,
            actor_type=str(actor_type),
            payload=payload or {},
        )
        self.session.add(entry)
        await self.session.flush()
        return entry
