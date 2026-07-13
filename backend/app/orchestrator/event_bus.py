"""In-process asyncio pub/sub for live Spine events (single-instance fan-out)."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from typing import Any


class EventBus:
    """Channel fan-out: subscribe(channel) → async iterator; publish(channel, message)."""

    def __init__(self) -> None:
        self._subs: dict[str, list[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)
        self._lock = asyncio.Lock()

    def add_subscriber(self, channel: str) -> asyncio.Queue[dict[str, Any]]:
        """Eager queue registration (safe to cancel waits without touching an async gen)."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._subs[channel].append(queue)
        return queue

    def remove_subscriber(self, channel: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        subs = self._subs.get(channel)
        if subs and queue in subs:
            subs.remove(queue)
            if not subs:
                self._subs.pop(channel, None)

    def subscribe(self, channel: str) -> AsyncIterator[dict[str, Any]]:
        """Register immediately so publishers cannot race past an open WS."""
        queue = self.add_subscriber(channel)

        async def _agen() -> AsyncIterator[dict[str, Any]]:
            try:
                while True:
                    yield await queue.get()
            finally:
                async with self._lock:
                    self.remove_subscriber(channel, queue)

        return _agen()

    async def publish(self, channel: str, message: dict[str, Any]) -> None:
        async with self._lock:
            queues = list(self._subs.get(channel, ()))
        for queue in queues:
            await queue.put(message)


_bus = EventBus()


def get_event_bus() -> EventBus:
    return _bus
