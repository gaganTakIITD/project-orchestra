from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.catalog import OutcomeSku
from app.schemas.catalog import OutcomeSkuOut

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/skus", response_model=list[OutcomeSkuOut])
async def list_skus(db: AsyncSession = Depends(get_db)) -> list[OutcomeSkuOut]:
    result = await db.execute(
        select(OutcomeSku).where(OutcomeSku.is_active.is_(True)).order_by(OutcomeSku.name)
    )
    rows = result.scalars().all()
    return [OutcomeSkuOut.from_orm_row(r) for r in rows]


@router.get("/skus/{slug}", response_model=OutcomeSkuOut)
async def get_sku(slug: str, db: AsyncSession = Depends(get_db)) -> OutcomeSkuOut:
    result = await db.execute(
        select(OutcomeSku).where(OutcomeSku.slug == slug, OutcomeSku.is_active.is_(True))
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="SKU not found")
    return OutcomeSkuOut.from_orm_row(row)
