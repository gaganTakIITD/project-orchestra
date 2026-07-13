"""Internal timer tick — Cloud Scheduler or lifespan loop."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.timer_tick import tick_due_timers

router = APIRouter(prefix="/internal/timers", tags=["internal"])


class TimerTickOut(BaseModel):
    fired: int = Field(description="Number of due timers processed")
    results: list[dict] = Field(default_factory=list)


@router.post("/tick", response_model=TimerTickOut)
async def timers_tick(session: AsyncSession = Depends(get_db)) -> TimerTickOut:
    results = await tick_due_timers(session)
    await session.commit()
    return TimerTickOut(fired=len(results), results=results)
