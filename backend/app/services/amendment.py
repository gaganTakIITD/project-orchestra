"""AmendmentService — formal scope changes (AI flags only; Spine/services mutate)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commerce import Quote
from app.models.fulfillment import AmendmentRecord, CharterRecord, FulfillmentTask, OutcomeOrder
from app.orchestrator.events import EventWriter
from app.orchestrator.states import ActorType


class AmendmentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.events = EventWriter(session)

    async def create_from_scope_flag(
        self,
        *,
        task: FulfillmentTask,
        requested_by: uuid.UUID,
        delta_description: str,
        proposed_delta: dict | None = None,
    ) -> AmendmentRecord:
        charter = await self.session.scalar(
            select(CharterRecord).where(CharterRecord.task_id == task.id)
        )
        row = AmendmentRecord(
            order_id=task.order_id,
            charter_id=charter.id if charter is not None else None,
            task_id=task.id,
            requested_by=requested_by,
            delta_description=(delta_description or "").strip() or "Scope change requested",
            proposed_delta=proposed_delta or {"source": "scope_guard", "body": delta_description},
            price_delta=Decimal("0"),
            time_delta_hours=0,
            status="requested",
        )
        self.session.add(row)
        await self.session.flush()

        await self.events.emit(
            aggregate_type="order",
            aggregate_id=task.order_id,
            event_type="AmendmentRequested",
            actor_id=requested_by,
            actor_type=ActorType.CLIENT,
            payload={
                "amendment_id": str(row.id),
                "task_id": str(task.id),
                "delta_description": row.delta_description[:500],
            },
        )
        await self.session.flush()
        return row

    async def list_for_order(self, order_id: uuid.UUID) -> list[AmendmentRecord]:
        result = await self.session.execute(
            select(AmendmentRecord)
            .where(AmendmentRecord.order_id == order_id)
            .order_by(AmendmentRecord.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, amendment_id: uuid.UUID) -> AmendmentRecord | None:
        return await self.session.get(AmendmentRecord, amendment_id)

    async def approve(
        self,
        *,
        amendment: AmendmentRecord,
        client_id: uuid.UUID,
        price_delta: Decimal | None = None,
    ) -> AmendmentRecord:
        if amendment.status not in ("requested", "priced"):
            raise ValueError(f"Cannot approve amendment in status {amendment.status!r}")

        order = await self.session.get(OutcomeOrder, amendment.order_id)
        if order is None or order.client_id != client_id:
            raise PermissionError("Only the order client may approve amendments")

        if price_delta is not None:
            amendment.price_delta = price_delta

        # Optional stub: bump quote.price by price_delta (no Razorpay).
        if amendment.price_delta and order.quote_id:
            quote = await self.session.get(Quote, order.quote_id)
            if quote is not None:
                quote.price = Decimal(str(quote.price)) + Decimal(str(amendment.price_delta))
                order.price = Decimal(str(order.price)) + Decimal(str(amendment.price_delta))

        charter = None
        if amendment.charter_id:
            charter = await self.session.get(CharterRecord, amendment.charter_id)
        elif amendment.task_id:
            charter = await self.session.scalar(
                select(CharterRecord).where(CharterRecord.task_id == amendment.task_id)
            )

        if charter is not None:
            snap = dict(charter.snapshot or {})
            meta = dict(snap.get("meta") or {})
            meta["amendments"] = list(meta.get("amendments") or [])
            meta["amendments"].append(
                {
                    "amendment_id": str(amendment.id),
                    "delta_description": amendment.delta_description,
                    "price_delta": float(amendment.price_delta or 0),
                    "applied_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            snap["meta"] = meta
            if amendment.delta_description:
                scope = str(snap.get("scope") or "")
                snap["scope"] = (scope + "\n\n[Amendment] " + amendment.delta_description).strip()
            charter.snapshot = snap
            charter.version = int(charter.version or 1) + 1
            amendment.charter_id = charter.id

        amendment.status = "approved"
        amendment.approved_at = datetime.now(timezone.utc)
        await self.session.flush()

        await self.events.emit(
            aggregate_type="order",
            aggregate_id=amendment.order_id,
            event_type="AmendmentApproved",
            actor_id=client_id,
            actor_type=ActorType.CLIENT,
            payload={
                "amendment_id": str(amendment.id),
                "charter_version": charter.version if charter else None,
                "price_delta": float(amendment.price_delta or 0),
            },
        )

        # Applied immediately for MVP (no separate fund-delta step).
        amendment.status = "applied"
        await self.events.emit(
            aggregate_type="order",
            aggregate_id=amendment.order_id,
            event_type="AmendmentApplied",
            actor_id=client_id,
            actor_type=ActorType.CLIENT,
            payload={"amendment_id": str(amendment.id)},
        )
        await self.session.flush()
        return amendment

    async def reject(
        self,
        *,
        amendment: AmendmentRecord,
        client_id: uuid.UUID,
    ) -> AmendmentRecord:
        if amendment.status not in ("requested", "priced"):
            raise ValueError(f"Cannot reject amendment in status {amendment.status!r}")

        order = await self.session.get(OutcomeOrder, amendment.order_id)
        if order is None or order.client_id != client_id:
            raise PermissionError("Only the order client may reject amendments")

        amendment.status = "rejected"
        await self.events.emit(
            aggregate_type="order",
            aggregate_id=amendment.order_id,
            event_type="AmendmentRejected",
            actor_id=client_id,
            actor_type=ActorType.CLIENT,
            payload={"amendment_id": str(amendment.id)},
        )
        await self.session.flush()
        return amendment
