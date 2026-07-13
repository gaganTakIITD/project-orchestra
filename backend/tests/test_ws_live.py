"""Live Spine WebSocket — EventBus fan-out after emit / discussion post."""

from __future__ import annotations

import asyncio
import json
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.fulfillment import FulfillmentTask, OutcomeOrder
from app.orchestrator.event_bus import get_event_bus
from app.orchestrator.spine import TaskSpine
from app.orchestrator.states import OrderStatus, TaskStatus


class _AsgiWsClient:
    """Minimal async WebSocket client against an ASGI app (same event loop)."""

    def __init__(self, asgi_app, path: str):
        self.app = asgi_app
        self.path = path
        self._to_app: asyncio.Queue = asyncio.Queue()
        self._from_app: asyncio.Queue = asyncio.Queue()
        self._task: asyncio.Task | None = None
        self.accepted = False

    async def __aenter__(self):
        async def receive():
            return await self._to_app.get()

        async def send(message):
            await self._from_app.put(message)

        scope = {
            "type": "websocket",
            "asgi": {"spec_version": "2.3", "version": "2.0"},
            "http_version": "1.1",
            "scheme": "ws",
            "server": ("test", 80),
            "client": ("test", 50000),
            "root_path": "",
            "path": self.path,
            "raw_path": self.path.encode(),
            "query_string": b"",
            "headers": [],
            "subprotocols": [],
            "state": {},
            "extensions": None,
        }

        self._task = asyncio.create_task(self.app(scope, receive, send))
        await self._to_app.put({"type": "websocket.connect"})

        while True:
            msg = await asyncio.wait_for(self._from_app.get(), timeout=5.0)
            if msg["type"] == "websocket.accept":
                self.accepted = True
                break
            if msg["type"] == "websocket.close":
                raise AssertionError(f"WebSocket rejected: {msg}")

        return self

    async def receive_json(self, timeout: float = 5.0) -> dict:
        while True:
            msg = await asyncio.wait_for(self._from_app.get(), timeout=timeout)
            if msg["type"] == "websocket.send":
                if "text" in msg and msg["text"] is not None:
                    return json.loads(msg["text"])
                if "bytes" in msg and msg["bytes"] is not None:
                    return json.loads(msg["bytes"])
            if msg["type"] == "websocket.close":
                raise AssertionError(f"WebSocket closed before message: {msg}")

    async def __aexit__(self, *exc):
        await self._to_app.put({"type": "websocket.disconnect", "code": 1000})
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=2.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self._task.cancel()


@pytest.fixture
async def api_client():
    from app.db.base import Base
    from app.db.seed import seed_catalog, seed_demo_client, seed_demo_worker
    from app.db.session import AsyncSessionLocal, engine

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSessionLocal() as session:
            await seed_catalog(session)
            await seed_demo_client(session)
            await seed_demo_worker(session)
    except Exception as e:
        pytest.skip(f"Database unavailable: {e}")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_event_bus_receives_spine_transition():
    """TaskSpine.emit fans out to task + parent order channels."""
    from app.db.base import Base
    from app.db.session import AsyncSessionLocal, engine

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        pytest.skip(f"Database unavailable: {e}")

    async with AsyncSessionLocal() as session:
        order = OutcomeOrder(
            id=uuid.uuid4(),
            client_id=uuid.uuid4(),
            status=OrderStatus.CONFIRMED,
            price=14000,
        )
        task = FulfillmentTask(
            id=uuid.uuid4(),
            order_id=order.id,
            title="Logo design",
            status=TaskStatus.BLOCKED,
            sequence_order=1,
            acceptance_criteria=[],
            payout_amount=2000,
        )
        session.add(order)
        await session.flush()
        session.add(task)
        await session.flush()

        bus = get_event_bus()
        got: asyncio.Queue = asyncio.Queue()

        async def collect(channel: str):
            async for msg in bus.subscribe(channel):
                await got.put((channel, msg))
                break

        t_task = asyncio.create_task(collect(f"task:{task.id}"))
        t_order = asyncio.create_task(collect(f"order:{order.id}"))
        await asyncio.sleep(0)

        spine = TaskSpine(session)
        await spine.transition(task, "dependencies_met")
        await session.commit()

        first = await asyncio.wait_for(got.get(), timeout=2.0)
        second = await asyncio.wait_for(got.get(), timeout=2.0)
        channels = {first[0], second[0]}
        assert channels == {f"task:{task.id}", f"order:{order.id}"}
        for _, msg in (first, second):
            assert msg["event_type"] == "TaskReady"
            assert msg["payload"]["order_id"] == str(order.id)
            assert msg["order_id"] == str(order.id)

        await asyncio.wait_for(asyncio.gather(t_task, t_order), timeout=2.0)


@pytest.mark.asyncio
async def test_ws_receives_event_after_discussion_post(api_client: AsyncClient):
    """WS /ws/orders/{id} receives DiscussionMessagePosted after POST discussion."""
    create = await api_client.post(
        "/api/v1/intents",
        json={
            "raw_text": "I need a Launch Studio brand and landing page for HealthTrack.",
            "attachments": [],
        },
    )
    assert create.status_code == 201, create.text
    quote_id = create.json()["quote_id"]

    accept = await api_client.post(f"/api/v1/quotes/{quote_id}/accept")
    assert accept.status_code == 200, accept.text
    order_id = accept.json()["order_id"]

    plan = (await api_client.get(f"/api/v1/orders/{order_id}/milestones")).json()
    assert plan["tasks"], "expected at least one task"
    task_id = plan["tasks"][0]["id"]

    async with _AsgiWsClient(app, f"/api/v1/ws/orders/{order_id}") as ws:
        assert ws.accepted
        post = await api_client.post(
            f"/api/v1/tasks/{task_id}/discussion",
            json={"body": "Quick question on brand colors"},
        )
        assert post.status_code == 200, post.text
        msg = await ws.receive_json()
        assert msg["event_type"] == "DiscussionMessagePosted"
        assert msg["aggregate_type"] == "task"
        assert msg["aggregate_id"] == task_id
        assert msg.get("order_id") == order_id or msg["payload"].get("order_id") == order_id
