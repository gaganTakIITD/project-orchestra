import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.commerce import OutcomeSpecRecord, Quote
from app.schemas.commerce import AcceptQuoteOut, QuoteOut
from app.services.auth import get_demo_client
from app.services.quote import QuoteService

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.get("/{quote_id}", response_model=QuoteOut)
async def get_quote(
    quote_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> QuoteOut:
    quote = await db.get(Quote, quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Quote not found")
    return QuoteOut.from_orm_row(quote)


@router.post("/{quote_id}/accept", response_model=AcceptQuoteOut)
async def accept_quote(
    quote_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AcceptQuoteOut:
    client = await get_demo_client(db)
    quote = await db.get(Quote, quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Quote not found")

    result = await db.execute(
        select(OutcomeSpecRecord).where(OutcomeSpecRecord.id == quote.spec_id)
    )
    spec = result.scalar_one_or_none()
    if spec is None:
        raise HTTPException(status_code=404, detail="Spec not found for quote")

    service = QuoteService(db)
    try:
        order = await service.accept_quote(quote=quote, spec=spec, client_id=client.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    await db.commit()
    return AcceptQuoteOut(order_id=str(order.id))
