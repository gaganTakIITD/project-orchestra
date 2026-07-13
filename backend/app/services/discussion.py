"""Task-scoped discussion threads."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.scope_guard import classify, summarize_charter
from app.models.fulfillment import (
    CharterRecord,
    DiscussionMessageRecord,
    DiscussionThreadRecord,
    FulfillmentTask,
)
from app.models.identity import User
from app.models.platform import AiDecisionLog
from app.orchestrator.events import EventWriter
from app.orchestrator.states import ActorType


class DiscussionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.events = EventWriter(session)

    async def get_or_create_thread(self, task: FulfillmentTask) -> DiscussionThreadRecord:
        thread = await self.session.scalar(
            select(DiscussionThreadRecord).where(DiscussionThreadRecord.task_id == task.id)
        )
        if thread is not None:
            return thread

        thread = DiscussionThreadRecord(
            task_id=task.id,
            order_id=task.order_id,
            status="active",
        )
        self.session.add(thread)
        await self.session.flush()

        system = DiscussionMessageRecord(
            thread_id=thread.id,
            sender_id="system",
            sender_name="Orchestra",
            body="Charter locked. This room is scoped to this task.",
            message_type="system",
            attachments=[],
            scope_flagged=False,
        )
        self.session.add(system)
        await self.session.flush()
        return thread

    async def list_messages(self, thread_id: uuid.UUID) -> list[DiscussionMessageRecord]:
        result = await self.session.execute(
            select(DiscussionMessageRecord)
            .where(DiscussionMessageRecord.thread_id == thread_id)
            .order_by(DiscussionMessageRecord.created_at)
        )
        return list(result.scalars().all())

    async def post_message(
        self,
        *,
        task: FulfillmentTask,
        sender: User,
        body: str,
        message_type: str = "clarification",
        attachments: list[str] | None = None,
    ) -> tuple[DiscussionThreadRecord, list[DiscussionMessageRecord]]:
        thread = await self.get_or_create_thread(task)

        charter = await self.session.scalar(
            select(CharterRecord).where(CharterRecord.task_id == task.id)
        )
        charter_summary = summarize_charter(
            task_title=task.title or "",
            task_description=task.description or "",
            snapshot=charter.snapshot if charter is not None else None,
        )
        guard = classify(body, charter_summary)

        self.session.add(
            AiDecisionLog(
                session_id=None,
                agent_type="scope_guard",
                source=guard.source,
                model=guard.model,
                input_text=(body or "")[:2000],
                output_draft={
                    "task_id": str(task.id),
                    "thread_id": str(thread.id),
                    "scope_drift": guard.scope_drift,
                    "reason": guard.reason,
                    "charter_summary": charter_summary[:2000],
                },
                reply=guard.reason,
                confidence=guard.confidence,
                latency_ms=guard.latency_ms,
                error=guard.error,
            )
        )

        # Flag-only: never mutate Charter / OutcomeSpec.
        flagged = bool(guard.scope_drift)
        effective_type = "scope_change_request" if flagged else message_type

        msg = DiscussionMessageRecord(
            thread_id=thread.id,
            sender_id=str(sender.id),
            sender_name=sender.full_name,
            body=body,
            message_type=effective_type,
            attachments=attachments or [],
            scope_flagged=flagged,
        )
        self.session.add(msg)
        await self.events.emit(
            aggregate_type="task",
            aggregate_id=task.id,
            event_type="DiscussionMessagePosted",
            actor_id=sender.id,
            actor_type=ActorType.CLIENT if sender.role == "client" else ActorType.WORKER,
            payload={
                "thread_id": str(thread.id),
                "message_type": effective_type,
                "scope_flagged": flagged,
            },
        )
        await self.session.flush()
        messages = await self.list_messages(thread.id)
        return thread, messages
