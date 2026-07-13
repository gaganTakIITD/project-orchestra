"""Mock ledger states — Held → Reserved → Released (no real money).

State advances only via lifecycle hooks (order confirm, mutual start, delivery accept).
Also writes balanced ledger_entries (double-entry stub) on each advance.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Final

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fulfillment import OutcomeOrder
from app.models.platform import LedgerEntryRecord
from app.orchestrator.events import EventWriter
from app.orchestrator.states import ActorType

# Client-facing strip steps (mirrors lib/types.ts LedgerState subset).
FUNDS_AUTHORIZED: Final = "funds_authorized"
MILESTONE_RESERVED: Final = "milestone_reserved"
PAYOUT_RELEASED: Final = "payout_released"
UNFUNDED: Final = "unfunded"
REFUNDED: Final = "refunded"

_RANK: Final[dict[str, int]] = {
    UNFUNDED: 0,
    FUNDS_AUTHORIZED: 1,
    MILESTONE_RESERVED: 2,
    PAYOUT_RELEASED: 3,
    REFUNDED: -1,
}


class LedgerService:
    """Persist coarse ledger state per order; emit event_log on each advance."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.events = EventWriter(session)

    async def authorize(
        self,
        order: OutcomeOrder,
        *,
        actor_id: uuid.UUID | None = None,
        actor_type: ActorType | str = ActorType.CLIENT,
    ) -> OutcomeOrder:
        """Order confirmed → Held / funds_authorized."""
        return await self._advance(
            order,
            FUNDS_AUTHORIZED,
            event_type="FundsAuthorized",
            actor_id=actor_id,
            actor_type=actor_type,
        )

    async def reserve(
        self,
        order: OutcomeOrder,
        *,
        actor_id: uuid.UUID | None = None,
        actor_type: ActorType | str = ActorType.SYSTEM,
    ) -> OutcomeOrder:
        """Mutual start / charter → Reserved / milestone_reserved."""
        return await self._advance(
            order,
            MILESTONE_RESERVED,
            event_type="MilestoneReserved",
            actor_id=actor_id,
            actor_type=actor_type,
        )

    async def release(
        self,
        order: OutcomeOrder,
        *,
        actor_id: uuid.UUID | None = None,
        actor_type: ActorType | str = ActorType.CLIENT,
    ) -> OutcomeOrder:
        """Delivery accepted → Released / payout_released.

        Open dispute blocks payout until resolved (Sprint 7) — no-op skip.
        """
        if getattr(order, "dispute_open", False):
            return order
        return await self._advance(
            order,
            PAYOUT_RELEASED,
            event_type="PayoutReleased",
            actor_id=actor_id,
            actor_type=actor_type,
        )

    async def list_entries(self, order_id: uuid.UUID) -> list[LedgerEntryRecord]:
        result = await self.session.execute(
            select(LedgerEntryRecord)
            .where(LedgerEntryRecord.order_id == order_id)
            .order_by(LedgerEntryRecord.created_at.asc())
        )
        return list(result.scalars().all())

    async def _write_entries(
        self,
        *,
        order: OutcomeOrder,
        event_type: str,
        amount: Decimal,
    ) -> None:
        """Balanced double-entry stub keyed off order.price."""
        amt = Decimal(str(amount or 0))
        pairs: list[tuple[str, Decimal, Decimal]] = []
        if event_type == "FundsAuthorized":
            pairs = [
                ("client_funds", amt, Decimal("0")),
                ("platform_clearing", Decimal("0"), amt),
            ]
        elif event_type == "MilestoneReserved":
            pairs = [
                ("platform_clearing", amt, Decimal("0")),
                ("milestone_reserve", Decimal("0"), amt),
            ]
        elif event_type == "PayoutReleased":
            pairs = [
                ("milestone_reserve", amt, Decimal("0")),
                ("worker_payable", Decimal("0"), amt),
            ]
        else:
            return

        for account, debit, credit in pairs:
            self.session.add(
                LedgerEntryRecord(
                    order_id=order.id,
                    account=account,
                    debit=debit,
                    credit=credit,
                    event_type=event_type,
                )
            )
        await self.session.flush()

    async def _advance(
        self,
        order: OutcomeOrder,
        to_state: str,
        *,
        event_type: str,
        actor_id: uuid.UUID | None,
        actor_type: ActorType | str,
    ) -> OutcomeOrder:
        current = getattr(order, "ledger_state", None) or UNFUNDED
        if current == REFUNDED:
            return order

        cur_rank = _RANK.get(current, 0)
        to_rank = _RANK.get(to_state, 0)
        if to_rank <= cur_rank:
            return order

        from_state = current
        order.ledger_state = to_state
        amount = Decimal(str(order.price)) if order.price is not None else Decimal("0")
        await self.events.emit(
            aggregate_type="order",
            aggregate_id=order.id,
            event_type=event_type,
            actor_id=actor_id,
            actor_type=actor_type,
            payload={
                "from_state": from_state,
                "to_state": to_state,
                "amount": float(amount),
            },
        )
        await self._write_entries(order=order, event_type=event_type, amount=amount)
        await self.session.flush()
        return order
