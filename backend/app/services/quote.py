import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commerce import OutcomeSpecRecord, Quote
from app.models.fulfillment import OutcomeOrder
from app.orchestrator.events import EventWriter
from app.orchestrator.states import ActorType, OrderStatus
from app.services.fulfillment import FulfillmentService
from app.services.ledger import LedgerService


class QuoteService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.events = EventWriter(session)

    async def accept_quote(
        self,
        *,
        quote: Quote,
        spec: OutcomeSpecRecord,
        client_id: uuid.UUID,
    ) -> OutcomeOrder:
        if quote.status != "issued":
            raise ValueError(f"Quote cannot be accepted in status {quote.status!r}")
        if quote.client_id != client_id:
            raise ValueError("Quote does not belong to this client")

        now = datetime.now(timezone.utc)
        spec.frozen_at = now
        quote.status = "accepted"

        order = OutcomeOrder(
            client_id=client_id,
            quote_id=quote.id,
            spec_id=spec.id,
            sku_id=spec.sku_id,
            status=OrderStatus.CONFIRMED,
            ledger_state="unfunded",
            price=quote.price,
            deadline=quote.deadline,
            revision_limit=quote.revision_limit,
            progress_pct=0,
        )
        self.session.add(order)
        await self.session.flush()

        await self.events.emit(
            aggregate_type="order",
            aggregate_id=order.id,
            event_type="OrderConfirmed",
            actor_id=client_id,
            actor_type="client",
            payload={"quote_id": str(quote.id), "spec_id": str(spec.id)},
        )

        # Held — mock authorize on confirm (no real payment gateway).
        await LedgerService(self.session).authorize(
            order, actor_id=client_id, actor_type=ActorType.CLIENT
        )

        fulfillment = FulfillmentService(self.session)
        await fulfillment.build_plan(order=order, spec=spec)

        await self.session.flush()
        return order
