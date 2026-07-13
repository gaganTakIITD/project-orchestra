"""GET /api/v1/orders — the client's outcomes list (powers the /orders dashboard).

Run with Postgres up (docker compose) from backend/:

    python -m pytest tests/test_orders_list.py -v
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.identity import DEMO_CLIENT_ID


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
async def test_orders_list_empty_then_populated(api_client: AsyncClient):
    # Fresh client has no outcomes yet.
    empty = await api_client.get("/api/v1/orders")
    assert empty.status_code == 200
    assert empty.json() == []

    # Create an order: intent -> quote -> accept.
    create = await api_client.post(
        "/api/v1/intents",
        json={
            "raw_text": "I need a Launch Studio brand and landing page for HealthTrack.",
            "attachments": [],
        },
    )
    assert create.status_code == 201
    quote_id = create.json()["quote_id"]

    accept = await api_client.post(f"/api/v1/quotes/{quote_id}/accept")
    assert accept.status_code == 200
    order_id = accept.json()["order_id"]

    # The list now returns that order, scoped to the current client.
    listed = await api_client.get("/api/v1/orders")
    assert listed.status_code == 200
    orders = listed.json()
    assert len(orders) == 1
    row = orders[0]
    assert row["id"] == order_id
    assert row["client_id"] == str(DEMO_CLIENT_ID)
    for field in ("status", "price", "deadline", "progress_pct", "created_at"):
        assert field in row


@pytest.mark.asyncio
async def test_orders_list_newest_first(api_client: AsyncClient):
    order_ids = []
    for _ in range(2):
        create = await api_client.post(
            "/api/v1/intents",
            json={
                "raw_text": "Launch Studio brand and landing page for a campus startup.",
                "attachments": [],
            },
        )
        assert create.status_code == 201
        accept = await api_client.post(
            f"/api/v1/quotes/{create.json()['quote_id']}/accept"
        )
        assert accept.status_code == 200
        order_ids.append(accept.json()["order_id"])

    listed = (await api_client.get("/api/v1/orders")).json()
    assert len(listed) == 2
    # Newest first: the most recently created order leads the list.
    assert listed[0]["id"] == order_ids[-1]
