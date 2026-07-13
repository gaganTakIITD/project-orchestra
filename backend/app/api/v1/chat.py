import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.chat import ChatSession
from app.models.identity import User
from app.schemas.chat import (
    ChatSessionOut,
    FinalizeChatIn,
    FinalizeChatOut,
    SendMessageIn,
    StartChatSessionIn,
)
from app.services.auth import get_current_client
from app.services.chat import ChatService

router = APIRouter(prefix="/chat/sessions", tags=["chat"])


async def _load_owned(service: ChatService, session_id: uuid.UUID, client: User) -> ChatSession:
    """Fetch a session and enforce that it belongs to the caller."""
    chat = await service.get_session(session_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat session not found")
    if chat.client_id != client.id:
        raise HTTPException(status_code=403, detail="Not your chat session")
    return chat


@router.post("", response_model=ChatSessionOut, status_code=201)
async def start_session(
    body: StartChatSessionIn | None = None,
    db: AsyncSession = Depends(get_db),
    client: User = Depends(get_current_client),
) -> ChatSessionOut:
    """Start Scope (default), Matcher, or Pricing Reasoner chat."""
    service = ChatService(db)
    payload = body or StartChatSessionIn()

    if payload.agent_type == "matcher":
        if not payload.ref_id or not payload.order_id:
            raise HTTPException(
                status_code=400,
                detail="matcher sessions require order_id and ref_id (task)",
            )
        try:
            chat, messages = await service.start_matcher_session(
                client=client,
                order_id=payload.order_id,
                task_id=payload.ref_id,
            )
        except LookupError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e)) from e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    elif payload.agent_type == "pricing":
        if not payload.ref_id:
            raise HTTPException(
                status_code=400,
                detail="pricing sessions require ref_id (quote)",
            )
        try:
            chat, messages = await service.start_pricing_session(
                client=client,
                quote_id=payload.ref_id,
            )
        except LookupError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e)) from e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    elif payload.agent_type in (None, "", "spec_compiler"):
        chat, messages = await service.start_scope_session(client=client)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported agent_type: {payload.agent_type!r}",
        )

    await db.commit()
    return ChatSessionOut.from_session(chat, messages)


@router.get("/{session_id}", response_model=ChatSessionOut)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    client: User = Depends(get_current_client),
) -> ChatSessionOut:
    service = ChatService(db)
    chat = await _load_owned(service, session_id, client)
    messages = await service.list_messages(session_id)
    return ChatSessionOut.from_session(chat, messages)


@router.post("/{session_id}/messages", response_model=ChatSessionOut)
async def send_message(
    session_id: uuid.UUID,
    body: SendMessageIn,
    db: AsyncSession = Depends(get_db),
    client: User = Depends(get_current_client),
) -> ChatSessionOut:
    service = ChatService(db)
    chat = await _load_owned(service, session_id, client)
    try:
        chat, messages = await service.send_message(chat=chat, body=body.body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    await db.commit()
    return ChatSessionOut.from_session(chat, messages)


@router.post("/{session_id}/messages/stream")
async def send_message_stream(
    session_id: uuid.UUID,
    body: SendMessageIn,
    db: AsyncSession = Depends(get_db),
    client: User = Depends(get_current_client),
) -> StreamingResponse:
    """SSE stream: draft_patch|artifact_updated → token* → turn_complete."""
    service = ChatService(db)
    chat = await _load_owned(service, session_id, client)

    async def event_generator():
        try:
            async for event in service.send_message_stream(chat=chat, body=body.body):
                yield f"data: {json.dumps(event, default=str)}\n\n"
            await db.commit()
        except ValueError as exc:
            await db.rollback()
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
        except Exception:
            await db.rollback()
            yield f"data: {json.dumps({'type': 'error', 'message': 'Stream failed'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{session_id}/finalize", response_model=FinalizeChatOut)
async def finalize_session(
    session_id: uuid.UUID,
    body: FinalizeChatIn | None = None,
    db: AsyncSession = Depends(get_db),
    client: User = Depends(get_current_client),
) -> FinalizeChatOut:
    service = ChatService(db)
    chat = await _load_owned(service, session_id, client)
    payload = body or FinalizeChatIn()
    try:
        if chat.agent_type == "matcher":
            pref_id, order_id, task_id = await service.finalize_matcher(
                chat=chat,
                client=client,
                ranked_worker_ids=payload.ranked_worker_ids,
            )
            await db.commit()
            return FinalizeChatOut(
                preference_set_id=pref_id,
                order_id=order_id,
                task_id=task_id,
            )
        if chat.agent_type == "pricing":
            quote_id, order_id = await service.finalize_pricing(chat=chat, client=client)
            await db.commit()
            return FinalizeChatOut(quote_id=quote_id, order_id=order_id)
        intent_id, quote_id = await service.finalize_scope(chat=chat, client=client)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    await db.commit()
    return FinalizeChatOut(intent_id=intent_id, quote_id=quote_id)


@router.post("/{session_id}/undo", response_model=ChatSessionOut)
async def undo_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    client: User = Depends(get_current_client),
) -> ChatSessionOut:
    """Restore the previous scope draft snapshot (Stage 1 undo)."""
    service = ChatService(db)
    chat = await _load_owned(service, session_id, client)
    try:
        chat, messages = await service.undo_scope_turn(chat=chat)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    await db.commit()
    return ChatSessionOut.from_session(chat, messages)
