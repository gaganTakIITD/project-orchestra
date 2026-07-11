import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gateway import compile_spec_turn
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

        # Conversation history before this turn — context for the AI gateway.
        prior = await self.list_messages(chat.id)
        history = [{"role": m.role, "body": m.body} for m in prior]
        all_user_text = " ".join(m.body for m in prior if m.role == "user") + " " + body

        user_msg = ChatMessage(session_id=chat.id, role="user", body=body)
        self.session.add(user_msg)
        await self.session.flush()

        # AI proposes a draft + reply. The Spine (below) decides completeness.
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

        chat.spec_draft = draft
        chat.spec_version = draft["version"]
        chat.completeness_pct = pct
        chat.missing_fields = missing
        chat.ready_for_quote = ready

        self.session.add(
            AiDecisionLog(
                session_id=chat.id,
                agent_type=chat.agent_type,
                source=turn.source,
                model=turn.model,
                input_text=body[:2000],
                output_draft=draft,
                reply=assistant_body,
                completeness_pct=pct,
                ready_for_quote=ready,
                confidence=turn.confidence,
                latency_ms=turn.latency_ms,
                error=turn.error,
            )
        )

        assistant_msg = ChatMessage(
            session_id=chat.id,
            role="assistant",
            body=assistant_body,
            spec_version_after=draft["version"],
        )
        self.session.add(assistant_msg)
        await self.session.flush()

        messages = await self.list_messages(chat.id)
        return chat, messages

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
