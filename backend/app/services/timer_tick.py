"""Fire due durable timers into Spine side-effects (promote_backup, etc.)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fulfillment import FulfillmentTask
from app.orchestrator.timers import DurableTimerService, TimerKind
from app.services.task_lifecycle import TaskLifecycleService


async def tick_due_timers(session: AsyncSession) -> list[dict[str, Any]]:
    """Claim and fire all due pending timers. Returns per-timer result dicts."""
    timers = DurableTimerService(session)
    due = await timers.due()
    lifecycle = TaskLifecycleService(session)
    results: list[dict[str, Any]] = []

    for timer in due:
        await timers.mark_fired(timer)
        outcome: dict[str, Any] = {
            "timer_id": str(timer.id),
            "kind": timer.kind,
            "aggregate_id": str(timer.aggregate_id),
        }
        try:
            if timer.kind == TimerKind.PRIORITY_WINDOW:
                task = await session.get(FulfillmentTask, timer.aggregate_id)
                if task is None:
                    outcome["action"] = "skipped"
                    outcome["reason"] = "task_missing"
                else:
                    task = await lifecycle.promote_backup(task=task)
                    outcome["action"] = "promote_backup"
                    outcome["task_status"] = task.status
                    outcome["assigned_worker_id"] = (
                        str(task.assigned_worker_id) if task.assigned_worker_id else None
                    )
            else:
                outcome["action"] = "skipped"
                outcome["reason"] = f"unhandled_kind:{timer.kind}"
        except Exception as exc:  # noqa: BLE001 — tick must continue for other timers
            outcome["action"] = "error"
            outcome["error"] = str(exc)
        outcome["fired_at"] = datetime.now(timezone.utc).isoformat()
        results.append(outcome)

    return results
