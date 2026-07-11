import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.fixtures.spec_compiler import compile_spec_fixture, quote_from_sku
from app.db.seed import SKU_IDS
from app.models.catalog import OutcomeSku
from app.models.commerce import Intent, OutcomeSpecRecord, Quote
from app.models.identity import User
from app.orchestrator.events import EventWriter


class IntentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.events = EventWriter(session)

    async def create_intent(
        self,
        *,
        client: User,
        raw_text: str,
        attachments: list[str],
    ) -> tuple[Intent, OutcomeSpecRecord, Quote]:
        sku = await self._default_sku()
        intent = Intent(
            client_id=client.id,
            raw_text=raw_text,
            attachments=attachments,
            status="captured",
        )
        self.session.add(intent)
        await self.session.flush()

        spec_fields = compile_spec_fixture(
            intent_id=intent.id,
            sku_id=sku.id,
            raw_text=raw_text,
        )
        spec = OutcomeSpecRecord(**spec_fields)
        self.session.add(spec)
        await self.session.flush()

        quote_fields = quote_from_sku(
            sku_base_price=float(sku.base_price),
            typical_days=sku.typical_days,
            revision_limit=sku.revision_limit,
        )
        quote = Quote(
            spec_id=spec.id,
            client_id=client.id,
            price=Decimal(str(quote_fields["price"])),
            deadline=quote_fields["deadline"],
            revision_limit=quote_fields["revision_limit"],
            status="issued",
            valid_until=quote_fields["valid_until"],
            ai_confidence=Decimal(str(quote_fields["ai_confidence"])),
            ai_rationale=quote_fields["ai_rationale"],
        )
        self.session.add(quote)

        intent.status = "compiled"
        await self.events.emit(
            aggregate_type="intent",
            aggregate_id=intent.id,
            event_type="IntentCaptured",
            actor_id=client.id,
            actor_type="client",
            payload={"raw_text_len": len(raw_text), "sku_slug": sku.slug},
        )
        await self.session.flush()
        return intent, spec, quote

    async def create_intent_from_draft(
        self,
        *,
        client: User,
        raw_text: str,
        draft: dict,
    ) -> tuple[Intent, OutcomeSpecRecord, Quote]:
        """Persist a completed scope-chat draft as intent + spec + quote."""
        sku = await self._default_sku()
        intent = Intent(
            client_id=client.id,
            raw_text=raw_text,
            attachments=[],
            status="compiled",
        )
        self.session.add(intent)
        await self.session.flush()

        spec = OutcomeSpecRecord(
            intent_id=intent.id,
            sku_id=sku.id,
            outcome_statement=draft.get("outcome_statement") or raw_text,
            deliverables=draft.get("deliverables") or [],
            acceptance_criteria=draft.get("acceptance_criteria") or [],
            in_scope=draft.get("in_scope") or [],
            out_of_scope=draft.get("out_of_scope") or [],
            assumptions=draft.get("assumptions") or [],
            client_inputs_required=draft.get("client_inputs_required") or [],
            mapped_task_types=draft.get("mapped_task_types") or [],
            risk_tier=draft.get("risk_tier") or "L1",
            version=int(draft.get("version") or 1),
        )
        self.session.add(spec)
        await self.session.flush()

        quote_fields = quote_from_sku(
            sku_base_price=float(sku.base_price),
            typical_days=sku.typical_days,
            revision_limit=sku.revision_limit,
        )
        quote = Quote(
            spec_id=spec.id,
            client_id=client.id,
            price=Decimal(str(quote_fields["price"])),
            deadline=quote_fields["deadline"],
            revision_limit=quote_fields["revision_limit"],
            status="issued",
            valid_until=quote_fields["valid_until"],
            ai_confidence=Decimal(str(quote_fields["ai_confidence"])),
            ai_rationale=quote_fields["ai_rationale"],
        )
        self.session.add(quote)

        await self.events.emit(
            aggregate_type="intent",
            aggregate_id=intent.id,
            event_type="IntentCaptured",
            actor_id=client.id,
            actor_type="client",
            payload={"source": "scope_chat", "completeness": "final"},
        )
        await self.session.flush()
        return intent, spec, quote

    async def get_spec_for_intent(self, intent_id: uuid.UUID) -> OutcomeSpecRecord | None:
        result = await self.session.execute(
            select(OutcomeSpecRecord).where(OutcomeSpecRecord.intent_id == intent_id)
        )
        return result.scalar_one_or_none()

    async def get_spec_by_id(self, spec_id: uuid.UUID) -> OutcomeSpecRecord | None:
        return await self.session.get(OutcomeSpecRecord, spec_id)

    async def _default_sku(self) -> OutcomeSku:
        result = await self.session.execute(
            select(OutcomeSku).where(OutcomeSku.id == SKU_IDS["launch_studio"])
        )
        sku = result.scalar_one_or_none()
        if sku is None:
            raise RuntimeError("Launch Studio SKU not seeded")
        return sku
