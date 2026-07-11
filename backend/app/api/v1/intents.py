import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.identity import User
from app.schemas.commerce import CreateIntentIn, CreateIntentOut, OutcomeSpecOut
from app.services.auth import get_current_client
from app.services.intent import IntentService

router = APIRouter(prefix="/intents", tags=["intents"])


@router.post("", response_model=CreateIntentOut, status_code=201)
async def create_intent(
    body: CreateIntentIn,
    db: AsyncSession = Depends(get_db),
    client: User = Depends(get_current_client),
) -> CreateIntentOut:
    service = IntentService(db)
    intent, _spec, quote = await service.create_intent(
        client=client,
        raw_text=body.raw_text,
        attachments=body.attachments,
    )
    await db.commit()
    return CreateIntentOut(intent_id=str(intent.id), quote_id=str(quote.id))


@router.get("/{intent_id}", response_model=OutcomeSpecOut)
async def get_intent_spec(
    intent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> OutcomeSpecOut:
    service = IntentService(db)
    spec = await service.get_spec_for_intent(intent_id)
    if spec is None:
        raise HTTPException(status_code=404, detail="Spec not found for intent")
    return OutcomeSpecOut.from_orm_row(spec)
