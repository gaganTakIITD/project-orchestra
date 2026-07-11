from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.identity import UserOut
from app.services.auth import get_current_user_for_me

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserOut)
async def me(
    user=Depends(get_current_user_for_me),
) -> UserOut:
    """Current user — demo stubs when AUTH_MODE=demo; Clerk JWT when AUTH_MODE=clerk."""
    return UserOut.from_orm_row(user)
