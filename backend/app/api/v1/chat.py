import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.chat import ChatSession
from app.models.identity import User
from app.schemas.chat import ChatSessionOut, FinalizeChatOut, SendMessageIn
from app.services.auth import get_demo_client
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
async def start_scope_session(
    db: AsyncSession = Depends(get_db),
) -> ChatSessionOut:
    client = await get_demo_client(db)
    service = ChatService(db)
    chat, messages = await service.start_scope_session(client=client)
    await db.commit()
    return ChatSessionOut.from_session(chat, messages)


@router.get("/{session_id}", response_model=ChatSessionOut)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ChatSessionOut:
    client = await get_demo_client(db)
    service = ChatService(db)
    chat = await _load_owned(service, session_id, client)
    messages = await service.list_messages(session_id)
    return ChatSessionOut.from_session(chat, messages)


@router.post("/{session_id}/messages", response_model=ChatSessionOut)
async def send_message(
    session_id: uuid.UUID,
    body: SendMessageIn,
    db: AsyncSession = Depends(get_db),
) -> ChatSessionOut:
    client = await get_demo_client(db)
    service = ChatService(db)
    chat = await _load_owned(service, session_id, client)
    try:
        chat, messages = await service.send_message(chat=chat, body=body.body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    await db.commit()
    return ChatSessionOut.from_session(chat, messages)


@router.post("/{session_id}/finalize", response_model=FinalizeChatOut)
async def finalize_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> FinalizeChatOut:
    client = await get_demo_client(db)
    service = ChatService(db)
    chat = await _load_owned(service, session_id, client)
    try:
        intent_id, quote_id = await service.finalize_scope(chat=chat, client=client)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    await db.commit()
    return FinalizeChatOut(intent_id=intent_id, quote_id=quote_id)
