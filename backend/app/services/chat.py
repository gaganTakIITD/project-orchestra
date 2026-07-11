import asyncio
import uuid
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gateway import compile_spec_turn
from app.ai.stream_chunks import stream_text_chunks
from app.ai.spec_extractor import (
    assess_completeness,
    empty_draft,
    opening_assistant_message,
    reply_for_turn,
)
from app.models.chat import ChatMessage, ChatSession
from app.models.identity import User
from app.models.platform import AiDecisionLog
from app.orchestrator.events import EventWriter
from app.services.chat_turn import TurnResult
from app.services.intent import IntentService


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

    async def get_session(self, session_id: uuid.UUID) -> ChatSession | None:
        return await self.session.get(ChatSession, session_id)

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
        """Yield SSE event payloads for one scope-chat turn."""
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
        turn = compile_spec_turn(
            draft=chat.spec_draft or empty_draft(),
            user_message=body,
            history=history,
        )
        draft = turn.draft
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
        )

    def _apply_turn(self, chat: ChatSession, result: TurnResult, body: str) -> None:
        chat.spec_draft = result.draft
        chat.spec_version = result.draft["version"]
        chat.completeness_pct = result.completeness_pct
        chat.missing_fields = result.missing_fields
        chat.ready_for_quote = result.ready_for_quote

        self.session.add(
            AiDecisionLog(
                session_id=chat.id,
                agent_type=chat.agent_type,
                source=result.turn.source,
                model=result.turn.model,
                input_text=body[:2000],
                output_draft=result.draft,
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
                spec_version_after=result.draft["version"],
            )
        )

    async def finalize_scope(
        self,
        *,
        chat: ChatSession,
        client: User,
    ) -> tuple[str, str]:
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
