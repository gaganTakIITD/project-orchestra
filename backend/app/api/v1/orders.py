import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.fulfillment import OutcomeOrder
from app.schemas.commerce import OutcomeOrderOut

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/{order_id}", response_model=OutcomeOrderOut)
async def get_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> OutcomeOrderOut:
    order = await db.get(OutcomeOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return OutcomeOrderOut.from_orm_row(order)
