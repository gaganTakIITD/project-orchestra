import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def api_client():
    """HTTP client; skips if Postgres unavailable."""
    from app.db.base import Base
    from app.db.seed import seed_catalog, seed_demo_client
    from app.db.session import AsyncSessionLocal, engine

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSessionLocal() as session:
            await seed_catalog(session)
            await seed_demo_client(session)
    except Exception as e:
        pytest.skip(f"Database unavailable: {e}")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_auth_me_returns_demo_client(api_client: AsyncClient):
    res = await api_client.get("/api/v1/auth/me")
    assert res.status_code == 200
    body = res.json()
    assert body["email"] == "ananya@healthtrack.in"
    assert body["role"] == "client"


@pytest.mark.asyncio
async def test_create_intent_returns_spec_and_quote(api_client: AsyncClient):
    res = await api_client.post(
        "/api/v1/intents",
        json={
            "raw_text": "I need a brand and landing page for my healthcare startup HealthTrack.",
            "attachments": [],
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert "intent_id" in body
    assert "quote_id" in body

    spec_res = await api_client.get(f"/api/v1/intents/{body['intent_id']}")
    assert spec_res.status_code == 200
    spec = spec_res.json()
    assert spec["intent_id"] == body["intent_id"]
    assert len(spec["deliverables"]) >= 1

    quote_res = await api_client.get(f"/api/v1/quotes/{body['quote_id']}")
    assert quote_res.status_code == 200
    quote = quote_res.json()
    assert quote["status"] == "issued"
    assert quote["price"] == 14000.0


@pytest.mark.asyncio
async def test_accept_quote_creates_order(api_client: AsyncClient):
    create = await api_client.post(
        "/api/v1/intents",
        json={
            "raw_text": "Launch Studio package for my SaaS product with modern branding.",
            "attachments": [],
        },
    )
    quote_id = create.json()["quote_id"]

    accept = await api_client.post(f"/api/v1/quotes/{quote_id}/accept")
    assert accept.status_code == 200
    order_id = accept.json()["order_id"]

    order_res = await api_client.get(f"/api/v1/orders/{order_id}")
    assert order_res.status_code == 200
    order = order_res.json()
    assert order["status"] == "confirmed"
    assert order["quote_id"] == quote_id
