"""Payments sandbox — ledger entries written even when PAYMENTS_ENABLED=false."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app
from app.models.fulfillment import OutcomeOrder
from app.models.identity import DEMO_CLIENT_ID
from app.models.platform import LedgerEntryRecord
from app.orchestrator.states import OrderStatus
from app.services.ledger import LedgerService


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
    from app.db.seed import seed_demo_client
    from app.db.session import AsyncSessionLocal, engine

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSessionLocal() as session:
            await seed_demo_client(session)
    except Exception as e:
        pytest.skip(f"Database unavailable: {e}")

    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.mark.asyncio
async def test_ledger_entries_on_authorize_flag_off(db_session, monkeypatch):
    monkeypatch.setattr("app.config.settings.payments_enabled", False)
    order = OutcomeOrder(
        id=uuid.uuid4(),
        client_id=DEMO_CLIENT_ID,
        status=OrderStatus.CONFIRMED,
        price=14000,
        ledger_state="unfunded",
    )
    db_session.add(order)
    await db_session.flush()

    await LedgerService(db_session).authorize(order, actor_id=DEMO_CLIENT_ID)
    await db_session.commit()

    rows = (
        await db_session.execute(
            select(LedgerEntryRecord).where(LedgerEntryRecord.order_id == order.id)
        )
    ).scalars().all()
    assert len(rows) == 2
    assert sum(float(r.debit) for r in rows) == sum(float(r.credit) for r in rows)
    assert order.ledger_state == "funds_authorized"


@pytest.mark.asyncio
async def test_fund_endpoint(api_client: AsyncClient):
    create = await api_client.post(
        "/api/v1/intents",
        json={"raw_text": "Need a logo and brand kit for my cafe within two weeks please"},
    )
    assert create.status_code in (200, 201)
    accept = await api_client.post(f"/api/v1/quotes/{create.json()['quote_id']}/accept")
    assert accept.status_code in (200, 201)
    order_id = accept.json()["order_id"]

    fund = await api_client.post(f"/api/v1/orders/{order_id}/fund")
    assert fund.status_code == 200
    assert fund.json()["payments_enabled"] is False

    entries = await api_client.get(f"/api/v1/orders/{order_id}/ledger-entries")
    assert entries.status_code == 200
    assert len(entries.json()["entries"]) >= 2
