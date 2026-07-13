"""Event-driven ledger: Held → Reserved → Released (mock money only).

Run with Postgres up (docker compose) from backend/:

    python -m pytest tests/test_ledger.py -v
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app
from app.models.identity import DEMO_WORKER_ID
from app.models.platform import EventLog
from app.orchestrator.states import OrderStatus, TaskStatus
from app.services.ledger import (
    FUNDS_AUTHORIZED,
    MILESTONE_RESERVED,
    PAYOUT_RELEASED,
)

_PASSING_ASSETS = [
    "https://files.example/logo.svg",
    "https://files.example/logo.png",
    "https://files.example/out.pdf",
    "https://preview.example/live",
]

_DEMO_RANKED = [
    str(DEMO_WORKER_ID),
    "usr_worker_meera",
    "usr_worker_kabir",
]


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


async def _create_order(api_client: AsyncClient) -> str:
    create = await api_client.post(
        "/api/v1/intents",
        json={
            "raw_text": "Launch Studio brand and landing for ledger path test.",
            "attachments": [],
        },
    )
    assert create.status_code == 201
    accept = await api_client.post(f"/api/v1/quotes/{create.json()['quote_id']}/accept")
    assert accept.status_code == 200
    return accept.json()["order_id"]


async def _complete_task(api_client: AsyncClient, order_id: str, task_id: str) -> None:
    pref = await api_client.post(
        f"/api/v1/orders/{order_id}/tasks/{task_id}/preferences",
        json={"ranked_worker_ids": list(_DEMO_RANKED)},
    )
    assert pref.status_code == 200, pref.text
    assert (await api_client.post(f"/api/v1/tasks/{task_id}/accept-interest")).json()[
        "status"
    ] == "accepted"
    assert (await api_client.post(f"/api/v1/tasks/{task_id}/ready-to-start")).json()[
        "status"
    ] == TaskStatus.IN_PROGRESS
    submit = await api_client.post(
        f"/api/v1/tasks/{task_id}/submit",
        json={
            "notes": "Work product attached. lighthouse: 85",
            "asset_urls": list(_PASSING_ASSETS),
        },
    )
    assert submit.status_code == 200, submit.text
    assert submit.json()["status"] == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_ledger_held_on_order_confirm(api_client: AsyncClient):
    order_id = await _create_order(api_client)
    order = (await api_client.get(f"/api/v1/orders/{order_id}")).json()
    assert order["status"] == OrderStatus.CONFIRMED
    assert order["ledger_state"] == FUNDS_AUTHORIZED

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        events = (
            await session.execute(
                select(EventLog).where(
                    EventLog.aggregate_type == "order",
                    EventLog.aggregate_id == uuid.UUID(order_id),
                    EventLog.event_type == "FundsAuthorized",
                )
            )
        ).scalars().all()
        assert len(events) == 1


@pytest.mark.asyncio
async def test_ledger_stays_held_through_assembling_team(api_client: AsyncClient):
    """Preferences / assembling_team must NOT reserve — only mutual start does."""
    order_id = await _create_order(api_client)
    plan = (await api_client.get(f"/api/v1/orders/{order_id}/milestones")).json()
    ready = next(t for t in plan["tasks"] if t["status"] == TaskStatus.READY)

    pref = await api_client.post(
        f"/api/v1/orders/{order_id}/tasks/{ready['id']}/preferences",
        json={"ranked_worker_ids": list(_DEMO_RANKED)},
    )
    assert pref.status_code == 200, pref.text

    order = (await api_client.get(f"/api/v1/orders/{order_id}")).json()
    assert order["status"] == OrderStatus.ASSEMBLING_TEAM
    assert order["ledger_state"] == FUNDS_AUTHORIZED


@pytest.mark.asyncio
async def test_ledger_reserved_on_mutual_start(api_client: AsyncClient):
    order_id = await _create_order(api_client)
    plan = (await api_client.get(f"/api/v1/orders/{order_id}/milestones")).json()
    ready = next(t for t in plan["tasks"] if t["status"] == TaskStatus.READY)
    task_id = ready["id"]

    pref = await api_client.post(
        f"/api/v1/orders/{order_id}/tasks/{task_id}/preferences",
        json={"ranked_worker_ids": list(_DEMO_RANKED)},
    )
    assert pref.status_code == 200, pref.text
    assert (await api_client.post(f"/api/v1/tasks/{task_id}/accept-interest")).json()[
        "status"
    ] == "accepted"
    assert (await api_client.post(f"/api/v1/tasks/{task_id}/ready-to-start")).json()[
        "status"
    ] == TaskStatus.IN_PROGRESS

    order = (await api_client.get(f"/api/v1/orders/{order_id}")).json()
    assert order["status"] == OrderStatus.DELIVERY_ACTIVE
    assert order["ledger_state"] == MILESTONE_RESERVED

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        events = (
            await session.execute(
                select(EventLog).where(
                    EventLog.aggregate_type == "order",
                    EventLog.aggregate_id == uuid.UUID(order_id),
                    EventLog.event_type == "MilestoneReserved",
                )
            )
        ).scalars().all()
        assert len(events) == 1


@pytest.mark.asyncio
async def test_ledger_released_on_delivery_accept(api_client: AsyncClient):
    order_id = await _create_order(api_client)

    for _ in range(5):
        plan = (await api_client.get(f"/api/v1/orders/{order_id}/milestones")).json()
        ready = [t for t in plan["tasks"] if t["status"] == TaskStatus.READY]
        assert ready, f"no ready task; {[t['status'] for t in plan['tasks']]}"
        await _complete_task(api_client, order_id, ready[0]["id"])

    mid = (await api_client.get(f"/api/v1/orders/{order_id}")).json()
    assert mid["status"] == OrderStatus.DELIVERED
    assert mid["ledger_state"] == MILESTONE_RESERVED

    closed = await api_client.post(f"/api/v1/orders/{order_id}/accept-delivery")
    assert closed.status_code == 200, closed.text
    assert closed.json()["status"] == OrderStatus.CLOSED

    order = (await api_client.get(f"/api/v1/orders/{order_id}")).json()
    assert order["ledger_state"] == PAYOUT_RELEASED

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        events = (
            await session.execute(
                select(EventLog).where(
                    EventLog.aggregate_type == "order",
                    EventLog.aggregate_id == uuid.UUID(order_id),
                    EventLog.event_type == "PayoutReleased",
                )
            )
        ).scalars().all()
        assert len(events) == 1
