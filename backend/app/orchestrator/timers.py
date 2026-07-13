"""Durable Postgres timers — schedule / cancel / tick (Cloud Scheduler or lifespan)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import TimerRecord


class TimerKind(StrEnum):
    PRIORITY_WINDOW = "priority_window"
    QUOTE_VALIDITY = "quote_validity"
    CLIENT_ACCEPTANCE = "client_acceptance"


class TimerStatus(StrEnum):
    PENDING = "pending"
    FIRED = "fired"
    CANCELLED = "cancelled"


@dataclass
class PendingTimer:
    """Legacy in-memory shape kept for unit tests / callers that don't need DB."""

    kind: TimerKind
    aggregate_id: str
    fires_at: datetime
    payload: dict


class InMemoryTimerQueue:
    """Test/dev stub — prefer DurableTimerService for real paths."""

    def __init__(self) -> None:
        self._timers: list[PendingTimer] = []

    def schedule(
        self,
        kind: TimerKind,
        aggregate_id: str,
        delay: timedelta,
        payload: dict | None = None,
    ) -> PendingTimer:
        timer = PendingTimer(
            kind=kind,
            aggregate_id=aggregate_id,
            fires_at=datetime.now(UTC) + delay,
            payload=payload or {},
        )
        self._timers.append(timer)
        return timer

    def due(self, now: datetime | None = None) -> list[PendingTimer]:
        now = now or datetime.now(UTC)
        due = [t for t in self._timers if t.fires_at <= now]
        self._timers = [t for t in self._timers if t.fires_at > now]
        return due


class DurableTimerService:
    """Postgres-backed timers — survive process restart / multi-instance Cloud Run."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def schedule(
        self,
        *,
        kind: TimerKind | str,
        aggregate_id: uuid.UUID,
        delay: timedelta | None = None,
        fire_at: datetime | None = None,
        payload: dict[str, Any] | None = None,
        aggregate_type: str = "task",
        cancel_existing: bool = True,
    ) -> TimerRecord:
        if fire_at is None:
            if delay is None:
                raise ValueError("Provide delay or fire_at")
            fire_at = datetime.now(UTC) + delay
        elif fire_at.tzinfo is None:
            fire_at = fire_at.replace(tzinfo=UTC)

        kind_str = kind.value if isinstance(kind, TimerKind) else str(kind)

        if cancel_existing:
            await self.cancel(
                kind=kind_str,
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
            )

        row = TimerRecord(
            kind=kind_str,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            fire_at=fire_at,
            payload=payload or {},
            status=TimerStatus.PENDING,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def cancel(
        self,
        *,
        kind: TimerKind | str | None = None,
        aggregate_id: uuid.UUID,
        aggregate_type: str = "task",
    ) -> int:
        kind_str = kind.value if isinstance(kind, TimerKind) else kind
        stmt = (
            update(TimerRecord)
            .where(
                TimerRecord.aggregate_id == aggregate_id,
                TimerRecord.aggregate_type == aggregate_type,
                TimerRecord.status == TimerStatus.PENDING,
            )
            .values(status=TimerStatus.CANCELLED)
        )
        if kind_str is not None:
            stmt = stmt.where(TimerRecord.kind == kind_str)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return int(result.rowcount or 0)

    async def due(self, now: datetime | None = None, *, limit: int = 100) -> list[TimerRecord]:
        now = now or datetime.now(UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        rows = list(
            (
                await self.session.execute(
                    select(TimerRecord)
                    .where(
                        TimerRecord.status == TimerStatus.PENDING,
                        TimerRecord.fire_at <= now,
                    )
                    .order_by(TimerRecord.fire_at.asc())
                    .limit(limit)
                    .with_for_update(skip_locked=True)
                )
            ).scalars()
        )
        return rows

    async def mark_fired(self, timer: TimerRecord, *, now: datetime | None = None) -> TimerRecord:
        now = now or datetime.now(UTC)
        timer.status = TimerStatus.FIRED
        timer.fired_at = now
        await self.session.flush()
        return timer
