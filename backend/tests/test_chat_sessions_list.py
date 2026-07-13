"""GET /api/v1/chat/sessions — the client's active scope drafts ('Resume scope').

Run with Postgres up (docker compose) from backend/:

    python -m pytest tests/test_chat_sessions_list.py -v
"""

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
async def test_scope_sessions_list_empty_then_active(api_client: AsyncClient):
    # No drafts yet.
    empty = await api_client.get("/api/v1/chat/sessions")
    assert empty.status_code == 200
    assert empty.json() == []

    # Starting a scope chat creates an active draft.
    start = await api_client.post("/api/v1/chat/sessions")
    assert start.status_code == 201
    sid = start.json()["id"]

    listed = await api_client.get("/api/v1/chat/sessions")
    assert listed.status_code == 200
    rows = listed.json()
    assert len(rows) == 1
    assert rows[0]["id"] == sid
    assert rows[0]["agent_type"] == "spec_compiler"
    assert rows[0]["status"] == "active"
    assert "title" in rows[0]


@pytest.mark.asyncio
async def test_scope_sessions_list_excludes_finalized(api_client: AsyncClient):
    """Once a draft is finalized (status=completed) it drops off the resume list."""
    start = await api_client.post("/api/v1/chat/sessions")
    sid = start.json()["id"]

    await api_client.post(
        f"/api/v1/chat/sessions/{sid}/messages",
        json={
            "body": (
                "HealthTrack — chronic condition tracking startup. Brand + landing page, "
                "trustworthy healthcare tone. Tagline: Your health, tracked. "
                "References: apple.com"
            )
        },
    )
    fin = await api_client.post(f"/api/v1/chat/sessions/{sid}/finalize")
    assert fin.status_code == 200

    listed = (await api_client.get("/api/v1/chat/sessions")).json()
    assert all(row["id"] != sid for row in listed)
