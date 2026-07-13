"""Amendment approve/reject + list-by-order."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.identity import User
from app.schemas.amendments import AmendmentListOut, AmendmentOut
from app.services.amendment import AmendmentService
from app.services.auth import get_current_client

router = APIRouter(tags=["amendments"])


@router.get("/orders/{order_id}/amendments", response_model=AmendmentListOut)
async def list_order_amendments(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    client: User = Depends(get_current_client),
) -> AmendmentListOut:
    from app.models.fulfillment import OutcomeOrder

    order = await db.get(OutcomeOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.client_id != client.id:
        raise HTTPException(status_code=403, detail="Not your order")
    rows = await AmendmentService(db).list_for_order(order_id)
    return AmendmentListOut(amendments=[AmendmentOut.from_orm_row(r) for r in rows])


@router.post("/amendments/{amendment_id}/approve", response_model=AmendmentOut)
async def approve_amendment(
    amendment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    client: User = Depends(get_current_client),
) -> AmendmentOut:
    svc = AmendmentService(db)
    row = await svc.get(amendment_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Amendment not found")
    try:
        row = await svc.approve(amendment=row, client_id=client.id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    await db.commit()
    return AmendmentOut.from_orm_row(row)


@router.post("/amendments/{amendment_id}/reject", response_model=AmendmentOut)
async def reject_amendment(
    amendment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    client: User = Depends(get_current_client),
) -> AmendmentOut:
    svc = AmendmentService(db)
    row = await svc.get(amendment_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Amendment not found")
    try:
        row = await svc.reject(amendment=row, client_id=client.id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    await db.commit()
    return AmendmentOut.from_orm_row(row)
