"""Amendments — create from scope flag, approve/reject, list by order."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app
from app.models.fulfillment import AmendmentRecord, CharterRecord, FulfillmentTask, OutcomeOrder
from app.models.identity import DEMO_CLIENT_ID
from app.models.platform import EventLog
from app.orchestrator.states import OrderStatus, TaskStatus
from app.services.amendment import AmendmentService


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


@pytest.mark.asyncio
async def test_create_approve_amendment(db_session):
    order = OutcomeOrder(
        id=uuid.uuid4(),
        client_id=DEMO_CLIENT_ID,
        status=OrderStatus.DELIVERY_ACTIVE,
        price=10000,
    )
    task = FulfillmentTask(
        id=uuid.uuid4(),
        order_id=order.id,
        title="Logo",
        status=TaskStatus.IN_PROGRESS,
        sequence_order=1,
        acceptance_criteria=[],
        payout_amount=2000,
    )
    charter = CharterRecord(
        order_id=order.id,
        task_id=task.id,
        version=1,
        snapshot={"scope": "Logo only", "meta": {}},
    )
    db_session.add(order)
    await db_session.flush()
    db_session.add(task)
    await db_session.flush()
    db_session.add(charter)
    await db_session.flush()

    svc = AmendmentService(db_session)
    row = await svc.create_from_scope_flag(
        task=task,
        requested_by=DEMO_CLIENT_ID,
        delta_description="Also need brand guidelines PDF",
    )
    assert row.status == "requested"

    events = (
        await db_session.execute(
            select(EventLog).where(EventLog.event_type == "AmendmentRequested")
        )
    ).scalars().all()
    assert len(events) == 1

    row = await svc.approve(amendment=row, client_id=DEMO_CLIENT_ID)
    assert row.status == "applied"
    await db_session.refresh(charter)
    assert charter.version == 2
    assert "Amendment" in (charter.snapshot.get("scope") or "")

    applied = (
        await db_session.execute(
            select(EventLog).where(EventLog.event_type == "AmendmentApplied")
        )
    ).scalars().all()
    assert len(applied) == 1


@pytest.mark.asyncio
async def test_reject_amendment_api(api_client: AsyncClient):
    from app.db.session import AsyncSessionLocal
    from app.services.amendment import AmendmentService

    async with AsyncSessionLocal() as session:
        order = OutcomeOrder(
            id=uuid.uuid4(),
            client_id=DEMO_CLIENT_ID,
            status=OrderStatus.DELIVERY_ACTIVE,
            price=5000,
        )
        task = FulfillmentTask(
            id=uuid.uuid4(),
            order_id=order.id,
            title="UI",
            status=TaskStatus.IN_PROGRESS,
            sequence_order=1,
            acceptance_criteria=[],
            payout_amount=1000,
        )
        session.add(order)
        await session.flush()
        session.add(task)
        await session.flush()
        row = await AmendmentService(session).create_from_scope_flag(
            task=task,
            requested_by=DEMO_CLIENT_ID,
            delta_description="Extra screens",
        )
        await session.commit()
        amendment_id = str(row.id)
        order_id = str(order.id)

    listed = await api_client.get(f"/api/v1/orders/{order_id}/amendments")
    assert listed.status_code == 200
    assert any(a["id"] == amendment_id for a in listed.json()["amendments"])

    rejected = await api_client.post(f"/api/v1/amendments/{amendment_id}/reject")
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
