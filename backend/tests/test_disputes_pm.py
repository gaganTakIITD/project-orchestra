"""Disputes + PM orchestrator tick."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.fulfillment import FulfillmentTask, OutcomeOrder
from app.models.identity import DEMO_CLIENT_ID
from app.models.platform import TimerRecord
from app.orchestrator.states import OrderStatus, TaskStatus
from app.orchestrator.timers import TimerKind


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
async def test_open_and_resolve_dispute(api_client: AsyncClient):
    create = await api_client.post(
        "/api/v1/intents",
        json={"raw_text": "Need a logo and brand kit for my cafe within two weeks please"},
    )
    accept = await api_client.post(f"/api/v1/quotes/{create.json()['quote_id']}/accept")
    order_id = accept.json()["order_id"]

    opened = await api_client.post(
        f"/api/v1/orders/{order_id}/disputes",
        json={"reason": "Deliverable missing"},
    )
    assert opened.status_code == 200
    dispute_id = opened.json()["id"]
    assert opened.json()["dispute_open"] is True

    listed = await api_client.get(f"/api/v1/orders/{order_id}/disputes")
    assert listed.status_code == 200
    assert len(listed.json()["disputes"]) == 1

    resolved = await api_client.post(
        f"/api/v1/admin/disputes/{dispute_id}/resolve",
        json={"resolution": "Partial rework agreed"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"


@pytest.mark.asyncio
async def test_orchestrator_tick(api_client: AsyncClient):
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        order = OutcomeOrder(
            id=uuid.uuid4(),
            client_id=DEMO_CLIENT_ID,
            status=OrderStatus.ASSEMBLING_TEAM,
            price=1000,
        )
        task = FulfillmentTask(
            id=uuid.uuid4(),
            order_id=order.id,
            title="Logo",
            status=TaskStatus.PRIORITY_ACTIVE,
            sequence_order=1,
            acceptance_criteria=[],
            payout_amount=200,
        )
        session.add(order)
        await session.flush()
        session.add(task)
        await session.flush()
        session.add(
            TimerRecord(
                kind=TimerKind.PRIORITY_WINDOW,
                aggregate_type="task",
                aggregate_id=task.id,
                fire_at=datetime.now(timezone.utc) - timedelta(minutes=1),
                status="pending",
                payload={},
            )
        )
        await session.commit()

    res = await api_client.post("/api/v1/internal/orchestrator/tick")
    assert res.status_code == 200
    body = res.json()
    assert "fired" in body
    assert "suggestions" in body
    assert isinstance(body["suggestions"], list)
