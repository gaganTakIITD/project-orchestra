import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.identity import DEMO_WORKER_ID


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
async def test_worker_profile(api_client: AsyncClient):
    res = await api_client.get("/api/v1/workers/profile")
    assert res.status_code == 200
    body = res.json()
    assert body["user_id"] == str(DEMO_WORKER_ID)
    assert body["full_name"] == "Rohan Verma"
    assert body["profile_completion_pct"] >= 70
    assert body["stats"]["seller_level"] == "trusted"
    assert len(body["skills"]) >= 1


@pytest.mark.asyncio
async def test_worker_me_tasks_after_order(api_client: AsyncClient):
    create = await api_client.post(
        "/api/v1/intents",
        json={"raw_text": "Launch Studio brand and landing for my SaaS.", "attachments": []},
    )
    assert create.status_code == 201
    accept = await api_client.post(f"/api/v1/quotes/{create.json()['quote_id']}/accept")
    assert accept.status_code == 200

    inbox = await api_client.get("/api/v1/workers/me/tasks")
    assert inbox.status_code == 200
    tasks = inbox.json()
    assert len(tasks) >= 1
    assert tasks[0]["status"] == "ready"
    assert "title" in tasks[0]
