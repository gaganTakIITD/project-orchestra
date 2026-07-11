"""Durable timer stubs — full Redis worker wiring comes in B5."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum


class TimerKind(StrEnum):
    PRIORITY_WINDOW = "priority_window"
    QUOTE_VALIDITY = "quote_validity"
    CLIENT_ACCEPTANCE = "client_acceptance"


@dataclass
class PendingTimer:
    kind: TimerKind
    aggregate_id: str
    fires_at: datetime
    payload: dict


class InMemoryTimerQueue:
    """Test/dev stub until Redis ARQ worker lands."""

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
