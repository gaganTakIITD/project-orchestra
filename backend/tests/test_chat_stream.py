import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.ai.stream_chunks import stream_text_chunks
from app.main import app


def test_stream_text_chunks_splits_words():
    chunks = stream_text_chunks("Hello world from Orchestra")
    assert len(chunks) >= 2
    assert "".join(chunks) == "Hello world from Orchestra"


@pytest.fixture
async def api_client():
    from app.db.base import Base
    from app.db.seed import seed_catalog, seed_demo_client
    from app.db.session import AsyncSessionLocal, engine

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
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
async def test_message_stream_sse_events(api_client: AsyncClient):
    start = await api_client.post("/api/v1/chat/sessions")
    assert start.status_code == 201
    sid = start.json()["id"]

    events: list[dict] = []
    async with api_client.stream(
        "POST",
        f"/api/v1/chat/sessions/{sid}/messages/stream",
        json={
            "body": (
                "HealthTrack — brand + landing, healthcare tone. "
                "Tagline: Your health, tracked. References: apple.com"
            )
        },
    ) as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")
        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))

    types = [e["type"] for e in events]
    assert "draft_patch" in types
    assert "token" in types
    assert types[-1] == "turn_complete"
    session = events[-1]["session"]
    assert session["ready_for_quote"] is True
    assert session["completeness_pct"] >= 85
