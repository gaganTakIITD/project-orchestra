"""Dispute cases — open / list / admin resolve."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fulfillment import DisputeCaseRecord, OutcomeOrder
from app.orchestrator.events import EventWriter
from app.orchestrator.states import ActorType
from app.services.ledger import PAYOUT_RELEASED


class DisputeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.events = EventWriter(session)

    async def open(
        self,
        *,
        order: OutcomeOrder,
        raised_by: uuid.UUID,
        reason: str,
        task_id: uuid.UUID | None = None,
    ) -> DisputeCaseRecord:
        row = DisputeCaseRecord(
            order_id=order.id,
            task_id=task_id,
            raised_by=raised_by,
            reason=(reason or "").strip() or "Dispute opened",
            status="open",
        )
        self.session.add(row)
        # Block payout if not yet released.
        if (order.ledger_state or "") != PAYOUT_RELEASED:
            order.dispute_open = True
        await self.session.flush()

        await self.events.emit(
            aggregate_type="order",
            aggregate_id=order.id,
            event_type="DisputeOpened",
            actor_id=raised_by,
            actor_type=ActorType.CLIENT,
            payload={
                "dispute_id": str(row.id),
                "reason": row.reason[:500],
                "blocks_payout": order.dispute_open,
            },
        )
        await self.session.flush()
        return row

    async def list_for_order(self, order_id: uuid.UUID) -> list[DisputeCaseRecord]:
        result = await self.session.execute(
            select(DisputeCaseRecord)
            .where(DisputeCaseRecord.order_id == order_id)
            .order_by(DisputeCaseRecord.created_at.desc())
        )
        return list(result.scalars().all())

    async def resolve(
        self,
        *,
        dispute: DisputeCaseRecord,
        resolved_by: uuid.UUID,
        resolution: str,
    ) -> DisputeCaseRecord:
        if dispute.status in ("resolved", "closed"):
            raise ValueError(f"Dispute already {dispute.status}")

        dispute.status = "resolved"
        dispute.resolution = resolution
        dispute.resolved_by = resolved_by

        order = await self.session.get(OutcomeOrder, dispute.order_id)
        if order is not None:
            open_left = await self.session.scalar(
                select(DisputeCaseRecord.id).where(
                    DisputeCaseRecord.order_id == order.id,
                    DisputeCaseRecord.status == "open",
                    DisputeCaseRecord.id != dispute.id,
                )
            )
            if open_left is None:
                order.dispute_open = False

        await self.events.emit(
            aggregate_type="order",
            aggregate_id=dispute.order_id,
            event_type="DisputeResolved",
            actor_id=resolved_by,
            actor_type=ActorType.ADMIN,
            payload={
                "dispute_id": str(dispute.id),
                "resolution": (resolution or "")[:500],
            },
        )
        await self.session.flush()
        return dispute
