from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.identity import SetRoleIn, UserOut
from app.services.auth import get_current_user_for_me, set_user_role

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserOut)
async def me(
    user=Depends(get_current_user_for_me),
) -> UserOut:
    """Current user — demo stubs when AUTH_MODE=demo; Clerk JWT when AUTH_MODE=clerk."""
    return UserOut.from_orm_row(user)


@router.patch("/role", response_model=UserOut)
async def choose_role(
    body: SetRoleIn,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user_for_me),
) -> UserOut:
    """Choose client or worker portal. Creates empty worker profile when switching to worker."""
    try:
        updated = await set_user_role(db, user, body.role)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    await db.commit()
    await db.refresh(updated)
    return UserOut.from_orm_row(updated)
