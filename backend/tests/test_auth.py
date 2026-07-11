"""Auth mode demo still resolves seeded users without Bearer."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


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
async def test_auth_me_demo_client(api_client: AsyncClient):
    res = await api_client.get("/api/v1/auth/me")
    assert res.status_code == 200
    assert res.json()["role"] == "client"


@pytest.mark.asyncio
async def test_auth_me_demo_worker_header(api_client: AsyncClient):
    res = await api_client.get(
        "/api/v1/auth/me",
        headers={"X-Orchestra-Role": "worker"},
    )
    assert res.status_code == 200
    assert res.json()["role"] == "worker"
    assert "Rohan" in res.json()["full_name"]
