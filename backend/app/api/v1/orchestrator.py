"""PM / orchestrator control-loop tick — timers + suggestions."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.orchestrator.events import EventWriter
from app.orchestrator.states import ActorType
from app.services.timer_tick import tick_due_timers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/orchestrator", tags=["internal"])

# Allowlisted auto-actions for the PM tick (never invent new ones here).
_AUTO_ACTIONS = frozenset({"promote_backup"})


class OrchestratorTickOut(BaseModel):
    fired: int = 0
    auto_actions: list[dict] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    results: list[dict] = Field(default_factory=list)


@router.post("/tick", response_model=OrchestratorTickOut)
async def orchestrator_tick(session: AsyncSession = Depends(get_db)) -> OrchestratorTickOut:
    """Detect overdue priority timers; auto promote_backup only; log PM suggestions."""
    results = await tick_due_timers(session)
    auto_actions: list[dict] = []
    suggestions: list[str] = []

    for r in results:
        action = r.get("action")
        if action in _AUTO_ACTIONS:
            auto_actions.append(r)
        elif action == "error":
            suggestions.append(
                f"Review timer {r.get('timer_id')}: error {r.get('error')}"
            )
        elif action == "skipped" and r.get("reason") not in (None, "task_missing"):
            suggestions.append(
                f"Unhandled timer kind for {r.get('aggregate_id')}: {r.get('reason')}"
            )

    overdue = [r for r in results if r.get("action") == "promote_backup"]
    if overdue:
        suggestions.append(
            f"Promoted backup on {len(overdue)} overdue priority window(s)."
        )
    if not results:
        suggestions.append("No due timers; control loop idle.")

    await EventWriter(session).emit(
        aggregate_type="system",
        aggregate_id=__import__("uuid").UUID("00000000-0000-4000-8000-000000000099"),
        event_type="PmTickCompleted",
        actor_type=ActorType.SYSTEM,
        payload={
            "fired": len(results),
            "auto_actions": len(auto_actions),
            "suggestions": suggestions[:10],
        },
    )
    await session.commit()
    logger.info("PM tick fired=%s autos=%s", len(results), len(auto_actions))
    return OrchestratorTickOut(
        fired=len(results),
        auto_actions=auto_actions,
        suggestions=suggestions,
        results=results,
    )
