import asyncio
import uuid
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gateway import SpecTurn, compile_spec_turn
from app.ai.matcher import match_candidates
from app.ai.matcher_chat import (
    MIN_RANKED,
    compile_matcher_turn,
    opening_matcher_message,
)
from app.ai.pricing_reasoner import compile_pricing_turn, opening_pricing_message
from app.ai.spec_extractor import (
    apply_package_defaults,
    assess_completeness,
    empty_draft,
    opening_assistant_message,
    reply_for_turn,
)
from app.ai.stream_chunks import stream_text_chunks
from app.models.catalog import OutcomeSku
from app.models.chat import ChatMessage, ChatSession
from app.models.commerce import OutcomeSpecRecord, Quote
from app.models.fulfillment import FulfillmentTask, OutcomeOrder
from app.models.identity import User
from app.models.platform import AiDecisionLog
from app.orchestrator.events import EventWriter
from app.services.chat_turn import TurnResult
from app.services.fulfillment import FulfillmentService
from app.services.intent import IntentService
from app.services.quote import QuoteService


class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.events = EventWriter(session)

    async def start_scope_session(self, *, client: User) -> tuple[ChatSession, list[ChatMessage]]:
        chat = ChatSession(
            client_id=client.id,
            agent_type="spec_compiler",
            status="active",
            spec_draft=empty_draft(),
            spec_version=0,
            completeness_pct=0,
            missing_fields=["outcome_statement"],
            ready_for_quote=False,
            spec_snapshots={},
        )
        self.session.add(chat)
        await self.session.flush()

        opening = ChatMessage(
            session_id=chat.id,
            role="assistant",
            body=opening_assistant_message(),
            spec_version_after=0,
        )
        self.session.add(opening)
        await self.session.flush()
        return chat, [opening]

    async def start_matcher_session(
        self,
        *,
        client: User,
        order_id: uuid.UUID,
        task_id: uuid.UUID,
    ) -> tuple[ChatSession, list[ChatMessage]]:
        order = await self.session.get(OutcomeOrder, order_id)
        if order is None:
            raise LookupError("Order not found")
        if order.client_id != client.id:
            raise PermissionError("Not your order")

        task = await self.session.scalar(
            select(FulfillmentTask).where(
                FulfillmentTask.order_id == order_id,
                FulfillmentTask.id == task_id,
            )
        )
        if task is None:
            raise LookupError("Task not found")
        if task.status not in ("ready", "invited"):
            raise ValueError(f"Task must be ready or invited to set preferences (is {task.status!r})")

        candidates = await match_candidates(self.session, task=task)
        ready = len(candidates) >= MIN_RANKED

        chat = ChatSession(
            client_id=client.id,
            agent_type="matcher",
            status="active",
            spec_draft=empty_draft(),
            spec_version=0,
            completeness_pct=0,
            missing_fields=[],
            ready_for_quote=False,
            ref_type="task",
            ref_id=task_id,
            order_id=order_id,
            candidates_draft=candidates,
            ready_to_confirm=ready,
        )
        self.session.add(chat)
        await self.session.flush()

        opening = ChatMessage(
            session_id=chat.id,
            role="assistant",
            body=opening_matcher_message(candidates, task_title=task.title),
            spec_version_after=0,
        )
        self.session.add(opening)
        await self.session.flush()
        return chat, [opening]

    async def start_pricing_session(
        self,
        *,
        client: User,
        quote_id: uuid.UUID,
    ) -> tuple[ChatSession, list[ChatMessage]]:
        quote = await self.session.get(Quote, quote_id)
        if quote is None:
            raise LookupError("Quote not found")
        if quote.client_id != client.id:
            raise PermissionError("Not your quote")
        if quote.status != "issued":
            raise ValueError(f"Quote must be issued to discuss pricing (is {quote.status!r})")

        ctx = await self._quote_context(quote)
        ready = True

        chat = ChatSession(
            client_id=client.id,
            agent_type="pricing",
            status="active",
            spec_draft={**empty_draft(), "quote_context": ctx},
            spec_version=0,
            completeness_pct=100,
            missing_fields=[],
            ready_for_quote=False,
            ref_type="quote",
            ref_id=quote_id,
            ready_to_confirm=ready,
            spec_snapshots={},
        )
        self.session.add(chat)
        await self.session.flush()

        opening = ChatMessage(
            session_id=chat.id,
            role="assistant",
            body=opening_pricing_message(ctx),
            spec_version_after=0,
        )
        self.session.add(opening)
        await self.session.flush()
        return chat, [opening]

    async def _quote_context(self, quote: Quote) -> dict[str, Any]:
        spec = await self.session.get(OutcomeSpecRecord, quote.spec_id)
        sku = None
        if spec and spec.sku_id:
            sku = await self.session.get(OutcomeSku, spec.sku_id)
        return {
            "quote_id": str(quote.id),
            "price": float(quote.price),
            "deadline": quote.deadline.isoformat() if quote.deadline else None,
            "revision_limit": quote.revision_limit,
            "ai_rationale": quote.ai_rationale,
            "ai_confidence": float(quote.ai_confidence) if quote.ai_confidence is not None else None,
            "risk_tier": (spec.risk_tier if spec else "L1"),
            "outcome_statement": (spec.outcome_statement if spec else ""),
            "deliverable_count": len(spec.deliverables or []) if spec else 0,
            "mapped_task_types": list(spec.mapped_task_types or []) if spec else [],
            "sku_name": sku.name if sku else None,
            "sku_slug": sku.slug if sku else None,
            "sku_base_price": float(sku.base_price) if sku else None,
            "sku_typical_days": sku.typical_days if sku else None,
        }

    async def get_session(self, session_id: uuid.UUID) -> ChatSession | None:
        return await self.session.get(ChatSession, session_id)

    async def list_scope_sessions(self, *, client_id: uuid.UUID) -> list[ChatSession]:
        """Active (unfinalized) scope drafts for a client, newest first — 'Resume scope'."""
        result = await self.session.execute(
            select(ChatSession)
            .where(
                ChatSession.client_id == client_id,
                ChatSession.agent_type == "spec_compiler",
                ChatSession.status == "active",
            )
            .order_by(ChatSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_messages(self, session_id: uuid.UUID) -> list[ChatMessage]:
        result = await self.session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
        )
        return list(result.scalars().all())

    async def send_message(
        self,
        *,
        chat: ChatSession,
        body: str,
    ) -> tuple[ChatSession, list[ChatMessage]]:
        if chat.status != "active":
            raise ValueError("Chat session is not active")

        prior = await self.list_messages(chat.id)
        history = [{"role": m.role, "body": m.body} for m in prior]
        all_user_text = " ".join(m.body for m in prior if m.role == "user") + " " + body

        user_msg = ChatMessage(session_id=chat.id, role="user", body=body)
        self.session.add(user_msg)
        await self.session.flush()

        result = self._compute_turn(
            chat=chat,
            body=body,
            history=history,
            all_user_text=all_user_text,
        )
        self._apply_turn(chat, result, body)
        await self.session.flush()

        messages = await self.list_messages(chat.id)
        return chat, messages

    async def send_message_stream(
        self,
        *,
        chat: ChatSession,
        body: str,
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield SSE event payloads for one chat turn (scope, matcher, or pricing)."""
        if chat.status != "active":
            raise ValueError("Chat session is not active")

        prior = await self.list_messages(chat.id)
        history = [{"role": m.role, "body": m.body} for m in prior]
        all_user_text = " ".join(m.body for m in prior if m.role == "user") + " " + body

        user_msg = ChatMessage(session_id=chat.id, role="user", body=body)
        self.session.add(user_msg)
        await self.session.flush()

        result = self._compute_turn(
            chat=chat,
            body=body,
            history=history,
            all_user_text=all_user_text,
        )

        if result.agent_kind in ("matcher", "pricing"):
            yield {
                "type": "artifact_updated",
                "candidates": result.candidates or [],
                "version": result.artifact_version,
                "ready_to_confirm": result.ready_to_confirm,
            }
        else:
            yield {
                "type": "draft_patch",
                "spec_draft": result.draft,
                "spec_version": result.draft["version"],
                "completeness_pct": result.completeness_pct,
                "missing_fields": result.missing_fields,
                "ready_for_quote": result.ready_for_quote,
            }

        for chunk in stream_text_chunks(result.assistant_body):
            yield {"type": "token", "content": chunk}
            await asyncio.sleep(0)

        self._apply_turn(chat, result, body)
        await self.session.flush()
        messages = await self.list_messages(chat.id)

        from app.schemas.chat import ChatSessionOut

        yield {
            "type": "turn_complete",
            "session": ChatSessionOut.from_session(chat, messages).model_dump(mode="json"),
        }

    def _compute_turn(
        self,
        *,
        chat: ChatSession,
        body: str,
        history: list[dict[str, str]],
        all_user_text: str,
    ) -> TurnResult:
        if chat.agent_type == "matcher":
            return self._compute_matcher_turn(chat=chat, body=body)
        if chat.agent_type == "pricing":
            return self._compute_pricing_turn(chat=chat, body=body)

        turn = compile_spec_turn(
            draft=chat.spec_draft or empty_draft(),
            user_message=body,
            history=history,
        )
        draft = apply_package_defaults(turn.draft)
        pct, missing, ready = assess_completeness(draft, all_user_text)
        assistant_body = turn.reply or reply_for_turn(
            user_message=body,
            draft=draft,
            missing=missing,
            completeness_pct=pct,
            ready=ready,
        )
        return TurnResult(
            draft=draft,
            assistant_body=assistant_body,
            completeness_pct=pct,
            missing_fields=missing,
            ready_for_quote=ready,
            turn=turn,
            agent_kind="spec_compiler",
        )

    def _compute_matcher_turn(self, *, chat: ChatSession, body: str) -> TurnResult:
        current = list(chat.candidates_draft or [])
        version = int(chat.spec_version or 0)
        mt = compile_matcher_turn(candidates=current, user_message=body, version=version)
        # Reuse SpecTurn shell for AiDecisionLog compatibility
        stub = SpecTurn(
            draft={"candidates": mt.candidates, "version": mt.version},
            reply=mt.reply,
            source=mt.source,
            model=mt.model,
            latency_ms=mt.latency_ms,
            confidence=mt.confidence,
            error=mt.error,
        )
        return TurnResult(
            draft=empty_draft(),
            assistant_body=mt.reply,
            completeness_pct=100 if mt.ready_to_confirm else min(99, len(mt.candidates) * 25),
            missing_fields=[] if mt.ready_to_confirm else ["ranked_shortlist"],
            ready_for_quote=False,
            turn=stub,
            candidates=mt.candidates,
            ready_to_confirm=mt.ready_to_confirm,
            artifact_version=mt.version,
            agent_kind="matcher",
        )

    def _compute_pricing_turn(self, *, chat: ChatSession, body: str) -> TurnResult:
        draft = chat.spec_draft or empty_draft()
        ctx = dict(draft.get("quote_context") or {})
        if not ctx.get("quote_id") and chat.ref_id:
            ctx["quote_id"] = str(chat.ref_id)
        version = int(chat.spec_version or 0)
        pt = compile_pricing_turn(quote=ctx, user_message=body, version=version)
        stub = SpecTurn(
            draft={"quote_id": pt.quote_id, "version": pt.version},
            reply=pt.reply,
            source=pt.source,
            model=pt.model,
            latency_ms=pt.latency_ms,
            confidence=pt.confidence,
            error=pt.error,
        )
        return TurnResult(
            draft=draft,
            assistant_body=pt.reply,
            completeness_pct=100,
            missing_fields=[],
            ready_for_quote=False,
            turn=stub,
            candidates=[],
            ready_to_confirm=pt.ready_to_confirm,
            artifact_version=pt.version,
            agent_kind="pricing",
        )

    def _snapshot_scope_draft(self, chat: ChatSession) -> None:
        """Persist draft state keyed by current version before a scope turn advances it."""
        if chat.agent_type != "spec_compiler":
            return
        snapshots = dict(chat.spec_snapshots or {})
        snapshots[str(chat.spec_version)] = {
            "spec_draft": chat.spec_draft or empty_draft(),
            "completeness_pct": chat.completeness_pct,
            "missing_fields": list(chat.missing_fields or []),
            "ready_for_quote": bool(chat.ready_for_quote),
        }
        chat.spec_snapshots = snapshots

    def _apply_turn(self, chat: ChatSession, result: TurnResult, body: str) -> None:
        if result.agent_kind == "matcher":
            chat.candidates_draft = result.candidates or []
            chat.ready_to_confirm = result.ready_to_confirm
            chat.spec_version = result.artifact_version
            chat.completeness_pct = result.completeness_pct
            chat.missing_fields = result.missing_fields
            output_draft: dict[str, Any] = {
                "candidates": result.candidates or [],
                "version": result.artifact_version,
                "ready_to_confirm": result.ready_to_confirm,
            }
            version_after = result.artifact_version
        elif result.agent_kind == "pricing":
            chat.ready_to_confirm = result.ready_to_confirm
            chat.spec_version = result.artifact_version
            chat.completeness_pct = result.completeness_pct
            chat.missing_fields = result.missing_fields
            output_draft = {
                "quote_id": str(chat.ref_id) if chat.ref_id else None,
                "version": result.artifact_version,
                "ready_to_confirm": result.ready_to_confirm,
            }
            version_after = result.artifact_version
        else:
            self._snapshot_scope_draft(chat)
            chat.spec_draft = result.draft
            chat.spec_version = result.draft["version"]
            chat.completeness_pct = result.completeness_pct
            chat.missing_fields = result.missing_fields
            chat.ready_for_quote = result.ready_for_quote
            output_draft = result.draft
            version_after = result.draft["version"]

        self.session.add(
            AiDecisionLog(
                session_id=chat.id,
                agent_type=chat.agent_type,
                source=result.turn.source,
                model=result.turn.model,
                input_text=body[:2000],
                output_draft=output_draft,
                reply=result.assistant_body,
                completeness_pct=result.completeness_pct,
                ready_for_quote=result.ready_for_quote,
                confidence=result.turn.confidence,
                latency_ms=result.turn.latency_ms,
                error=result.turn.error,
            )
        )

        self.session.add(
            ChatMessage(
                session_id=chat.id,
                role="assistant",
                body=result.assistant_body,
                spec_version_after=version_after,
            )
        )

    async def finalize_scope(
        self,
        *,
        chat: ChatSession,
        client: User,
    ) -> tuple[str, str]:
        if chat.agent_type != "spec_compiler":
            raise ValueError("Not a scope chat session")
        if chat.status != "active":
            raise ValueError("Chat session already finalized")
        if not chat.ready_for_quote:
            missing = ", ".join(chat.missing_fields or [])
            raise ValueError(f"Job description incomplete — still need: {missing}")

        draft = chat.spec_draft or {}
        raw_text = draft.get("outcome_statement") or ""
        if len(raw_text) < 20:
            raise ValueError("Outcome statement too short to finalize")

        intent_service = IntentService(self.session)
        intent, spec, quote = await intent_service.create_intent_from_draft(
            client=client,
            raw_text=raw_text,
            draft=draft,
        )

        chat.status = "completed"
        chat.intent_id = intent.id
        await self.events.emit(
            aggregate_type="chat_session",
            aggregate_id=chat.id,
            event_type="ScopeChatFinalized",
            actor_id=client.id,
            actor_type="client",
            payload={"intent_id": str(intent.id), "completeness_pct": chat.completeness_pct},
        )
        await self.session.flush()
        return str(intent.id), str(quote.id)

    async def finalize_matcher(
        self,
        *,
        chat: ChatSession,
        client: User,
        ranked_worker_ids: list[str] | None = None,
    ) -> tuple[str, str, str]:
        """Persist PreferenceSet via FulfillmentService; return (pref_id, order_id, task_id)."""
        if chat.agent_type != "matcher":
            raise ValueError("Not a matcher chat session")
        if chat.status != "active":
            raise ValueError("Chat session already finalized")
        if not chat.order_id or not chat.ref_id:
            raise ValueError("Matcher session missing order/task refs")

        candidates = list(chat.candidates_draft or [])
        if ranked_worker_ids:
            ids = ranked_worker_ids
        else:
            ids = [c["worker_id"] for c in candidates]

        if len(ids) < MIN_RANKED:
            raise ValueError(f"Need at least {MIN_RANKED} ranked workers to confirm preferences")

        order = await self.session.get(OutcomeOrder, chat.order_id)
        if order is None:
            raise LookupError("Order not found")
        if order.client_id != client.id:
            raise PermissionError("Not your order")

        task = await self.session.get(FulfillmentTask, chat.ref_id)
        if task is None:
            raise LookupError("Task not found")

        fulfillment = FulfillmentService(self.session)
        pref = await fulfillment.set_preferences(
            order=order,
            task=task,
            ranked_worker_ids=ids,
            client_id=client.id,
        )

        chat.status = "completed"
        chat.ready_to_confirm = True
        await self.events.emit(
            aggregate_type="chat_session",
            aggregate_id=chat.id,
            event_type="MatcherChatFinalized",
            actor_id=client.id,
            actor_type="client",
            payload={
                "preference_set_id": str(pref.id),
                "order_id": str(order.id),
                "task_id": str(task.id),
                "ranked_worker_ids": ids,
            },
        )
        await self.session.flush()
        return str(pref.id), str(order.id), str(task.id)

    async def finalize_pricing(
        self,
        *,
        chat: ChatSession,
        client: User,
    ) -> tuple[str, str]:
        """Accept the bound quote via QuoteService; return (quote_id, order_id)."""
        if chat.agent_type != "pricing":
            raise ValueError("Not a pricing chat session")
        if chat.status != "active":
            raise ValueError("Chat session already finalized")
        if not chat.ref_id:
            raise ValueError("Pricing session missing quote ref")
        if not chat.ready_to_confirm:
            raise ValueError("Confirm the quote in chat before accepting")

        quote = await self.session.get(Quote, chat.ref_id)
        if quote is None:
            raise LookupError("Quote not found")
        if quote.client_id != client.id:
            raise PermissionError("Not your quote")

        spec = await self.session.get(OutcomeSpecRecord, quote.spec_id)
        if spec is None:
            raise LookupError("Spec not found for quote")

        order = await QuoteService(self.session).accept_quote(
            quote=quote,
            spec=spec,
            client_id=client.id,
        )

        chat.status = "completed"
        chat.ready_to_confirm = True
        await self.events.emit(
            aggregate_type="chat_session",
            aggregate_id=chat.id,
            event_type="PricingChatFinalized",
            actor_id=client.id,
            actor_type="client",
            payload={
                "quote_id": str(quote.id),
                "order_id": str(order.id),
            },
        )
        await self.session.flush()
        return str(quote.id), str(order.id)

    async def undo_scope_turn(
        self,
        *,
        chat: ChatSession,
    ) -> tuple[ChatSession, list[ChatMessage]]:
        """Restore the previous scope draft snapshot and drop the last user/assistant pair."""
        if chat.agent_type != "spec_compiler":
            raise ValueError("Undo is only supported for scope chat sessions")
        if chat.status != "active":
            raise ValueError("Chat session is not active")

        snapshots = dict(chat.spec_snapshots or {})
        if not snapshots:
            raise ValueError("Nothing to undo")

        # Prefer snapshot for version-1 (state before last advance); else highest key < current.
        target_key: str | None = None
        current = int(chat.spec_version or 0)
        if str(current - 1) in snapshots:
            target_key = str(current - 1)
        else:
            numeric_keys = sorted(
                (int(k) for k in snapshots if str(k).isdigit()),
                reverse=True,
            )
            for k in numeric_keys:
                if k < current:
                    target_key = str(k)
                    break
            if target_key is None and numeric_keys:
                target_key = str(numeric_keys[0])

        if target_key is None:
            raise ValueError("Nothing to undo")

        snap = snapshots[target_key]
        chat.spec_draft = snap.get("spec_draft") or empty_draft()
        chat.spec_version = int(target_key)
        chat.completeness_pct = int(snap.get("completeness_pct") or 0)
        chat.missing_fields = list(snap.get("missing_fields") or [])
        chat.ready_for_quote = bool(snap.get("ready_for_quote"))

        # Drop the restored key so a second undo walks further back
        snapshots.pop(target_key, None)
        chat.spec_snapshots = dict(snapshots)

        messages = await self.list_messages(chat.id)
        # Remove trailing user + assistant pair from the last turn (if present)
        if len(messages) >= 2 and messages[-1].role == "assistant" and messages[-2].role == "user":
            await self.session.delete(messages[-1])
            await self.session.delete(messages[-2])
        elif messages and messages[-1].role == "user":
            await self.session.delete(messages[-1])

        await self.session.flush()
        remaining = await self.list_messages(chat.id)
        return chat, remaining

