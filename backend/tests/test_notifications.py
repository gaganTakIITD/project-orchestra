"""Notifications — list/mark-read + event projection from Spine transitions."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app
from app.models.fulfillment import FulfillmentTask, OutcomeOrder
from app.models.identity import DEMO_CLIENT_ID, DEMO_WORKER_ID
from app.models.platform import Notification
from app.orchestrator.spine import OrderSpine, TaskSpine
from app.orchestrator.states import OrderStatus, TaskStatus


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


@pytest.fixture
async def db_session():
    from app.db.base import Base
    from app.db.seed import seed_demo_client, seed_demo_worker
    from app.db.session import AsyncSessionLocal, engine

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSessionLocal() as session:
            await seed_demo_client(session)
            await seed_demo_worker(session)
    except Exception as e:
        pytest.skip(f"Database unavailable: {e}")

    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()

    await engine.dispose()


@pytest.mark.asyncio
async def test_list_notifications_empty(api_client: AsyncClient):
    res = await api_client.get("/api/v1/notifications")
    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.asyncio
async def test_preferences_set_creates_invite_for_worker(db_session):
    order = OutcomeOrder(
        id=uuid.uuid4(),
        client_id=DEMO_CLIENT_ID,
        status=OrderStatus.CONFIRMED,
        price=14000,
    )
    task = FulfillmentTask(
        id=uuid.uuid4(),
        order_id=order.id,
        title="Logo design",
        status=TaskStatus.READY,
        sequence_order=1,
        acceptance_criteria=[],
        payout_amount=2000,
    )
    db_session.add(order)
    await db_session.flush()
    db_session.add(task)
    await db_session.flush()

    spine = TaskSpine(db_session)
    await spine.transition(
        task,
        "preferences_set",
        actor_type="client",
        payload={"ranked_worker_ids": [str(DEMO_WORKER_ID)]},
    )
    await db_session.commit()

    rows = (
        await db_session.execute(
            select(Notification).where(Notification.user_id == DEMO_WORKER_ID)
        )
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].type == "invite"
    assert rows[0].ref_type == "task"
    assert rows[0].ref_id == task.id
    assert rows[0].source_event_id is not None


@pytest.mark.asyncio
async def test_interest_and_priority_notify_worker_and_client(db_session):
    order = OutcomeOrder(
        id=uuid.uuid4(),
        client_id=DEMO_CLIENT_ID,
        status=OrderStatus.ASSEMBLING_TEAM,
        price=14000,
    )
    task = FulfillmentTask(
        id=uuid.uuid4(),
        order_id=order.id,
        title="Landing page",
        status=TaskStatus.INVITED,
        sequence_order=1,
        acceptance_criteria=[],
        payout_amount=3000,
    )
    db_session.add(order)
    await db_session.flush()
    db_session.add(task)
    await db_session.flush()

    spine = TaskSpine(db_session)
    await spine.transition(
        task,
        "interest_accepted",
        actor_id=DEMO_WORKER_ID,
        actor_type="worker",
        payload={"worker_id": str(DEMO_WORKER_ID)},
    )
    await spine.transition(
        task,
        "priority_granted",
        actor_type="system",
        payload={"worker_id": str(DEMO_WORKER_ID)},
    )
    await db_session.commit()

    worker_types = {
        r.type
        for r in (
            await db_session.execute(
                select(Notification).where(Notification.user_id == DEMO_WORKER_ID)
            )
        ).scalars().all()
    }
    client_types = {
        r.type
        for r in (
            await db_session.execute(
                select(Notification).where(Notification.user_id == DEMO_CLIENT_ID)
            )
        ).scalars().all()
    }
    assert "interest_accepted" in worker_types
    assert "priority_granted" in worker_types
    assert "interest_accepted" in client_types
    assert "priority_granted" in client_types


@pytest.mark.asyncio
async def test_qa_and_delivery_notifications(db_session):
    order = OutcomeOrder(
        id=uuid.uuid4(),
        client_id=DEMO_CLIENT_ID,
        status=OrderStatus.DELIVERY_ACTIVE,
        price=14000,
    )
    task = FulfillmentTask(
        id=uuid.uuid4(),
        order_id=order.id,
        title="API backend",
        status=TaskStatus.SUBMITTED,
        sequence_order=1,
        acceptance_criteria=[],
        payout_amount=4000,
        assigned_worker_id=DEMO_WORKER_ID,
    )
    db_session.add(order)
    await db_session.flush()
    db_session.add(task)
    await db_session.flush()

    task_spine = TaskSpine(db_session)
    await task_spine.transition(task, "qa_pass", actor_type="system")

    order.status = OrderStatus.UNDER_QUALITY_CHECK
    await db_session.flush()
    order_spine = OrderSpine(db_session)
    await order_spine.transition(order, "bundle_ready", actor_type="system")
    await order_spine.transition(order, "client_accept", actor_type="client")
    await db_session.commit()

    worker_rows = (
        await db_session.execute(
            select(Notification).where(Notification.user_id == DEMO_WORKER_ID)
        )
    ).scalars().all()
    assert any(r.type == "qa_pass" for r in worker_rows)

    client_rows = (
        await db_session.execute(
            select(Notification).where(Notification.user_id == DEMO_CLIENT_ID)
        )
    ).scalars().all()
    types = {r.type for r in client_rows}
    assert "delivery_ready" in types
    assert "delivery_accepted" in types


@pytest.mark.asyncio
async def test_list_and_mark_read_via_api(api_client: AsyncClient):
    # Create order → prefer demo worker → invite notification lands for worker.
    create = await api_client.post(
        "/api/v1/intents",
        json={"raw_text": "I need a logo and brand kit for my health startup"},
    )
    assert create.status_code in (200, 201)
    accept = await api_client.post(f"/api/v1/quotes/{create.json()['quote_id']}/accept")
    assert accept.status_code == 200
    order_id = accept.json()["order_id"]
    plan = (await api_client.get(f"/api/v1/orders/{order_id}/milestones")).json()
    ready = [t for t in plan["tasks"] if t["status"] == "ready"]
    assert ready
    task_id = ready[0]["id"]

    candidates = (
        await api_client.get(f"/api/v1/orders/{order_id}/tasks/{task_id}/candidates")
    ).json()
    ranked = [c["worker_id"] for c in candidates[:3]]
    # Ensure demo worker is preferred so X-Orchestra-Role: worker sees the invite.
    ranked = [str(DEMO_WORKER_ID)] + [w for w in ranked if w != str(DEMO_WORKER_ID)]
    while len(ranked) < 3:
        ranked.append(f"00000000-0000-4000-8000-00000000002{len(ranked)}")
    pref = await api_client.post(
        f"/api/v1/orders/{order_id}/tasks/{task_id}/preferences",
        json={"ranked_worker_ids": ranked[:3]},
    )
    assert pref.status_code == 200

    worker_headers = {"X-Orchestra-Role": "worker"}
    listed = await api_client.get("/api/v1/notifications", headers=worker_headers)
    assert listed.status_code == 200
    body = listed.json()
    invites = [n for n in body if n["type"] == "invite" and n["ref_id"] == task_id]
    assert invites
    assert invites[0]["read"] is False
    assert invites[0]["user_id"] == str(DEMO_WORKER_ID)

    ntf_id = invites[0]["id"]
    marked = await api_client.post(
        f"/api/v1/notifications/{ntf_id}/read",
        headers=worker_headers,
    )
    assert marked.status_code == 200
    assert marked.json()["read"] is True

    listed2 = await api_client.get("/api/v1/notifications", headers=worker_headers)
    found = next(n for n in listed2.json() if n["id"] == ntf_id)
    assert found["read"] is True

    # Client must not mark worker's notification.
    denied = await api_client.post(f"/api/v1/notifications/{ntf_id}/read")
    assert denied.status_code == 404
