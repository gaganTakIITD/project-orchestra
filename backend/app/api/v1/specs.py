import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.commerce import OutcomeSpecOut
from app.services.intent import IntentService

router = APIRouter(prefix="/specs", tags=["specs"])


@router.get("/{spec_id}", response_model=OutcomeSpecOut)
async def get_spec(
    spec_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> OutcomeSpecOut:
    service = IntentService(db)
    spec = await service.get_spec_by_id(spec_id)
    if spec is None:
        raise HTTPException(status_code=404, detail="Spec not found")
    return OutcomeSpecOut.from_orm_row(spec)
