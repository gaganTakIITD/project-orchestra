from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.identity import UserOut
from app.services.auth import get_demo_client

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserOut)
async def me(db: AsyncSession = Depends(get_db)) -> UserOut:
    """Demo auth stub — always returns the seeded demo client until JWT lands."""
    user = await get_demo_client(db)
    return UserOut.from_orm_row(user)
