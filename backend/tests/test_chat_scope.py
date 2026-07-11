import pytest
from httpx import ASGITransport, AsyncClient

from app.ai.spec_extractor import assess_completeness, empty_draft, extract_from_message
from app.main import app


def test_vague_startup_not_ready():
    draft = empty_draft()
    draft = extract_from_message(draft, "create my startup", "create my startup")
    pct, missing, ready = assess_completeness(draft, "create my startup")
    assert ready is False


def test_healthcare_intent_increases_completeness():
    msg = (
        "HealthTrack helps chronic condition tracking — need brand and landing page, "
        "trustworthy modern healthcare. Tagline: Your health, tracked. References: apple.com, stripe.com"
    )
    draft = empty_draft()
    draft = extract_from_message(draft, msg, msg)
    pct, missing, ready = assess_completeness(draft, msg)
    assert pct >= 85
    assert ready is True
    assert draft["deliverables"]
    assert draft["workflow_summary"]


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
async def test_scope_chat_flow_to_finalize(api_client: AsyncClient):
    start = await api_client.post("/api/v1/chat/sessions")
    assert start.status_code == 201
    session = start.json()
    sid = session["id"]
    assert session["completeness_pct"] == 0

    vague = await api_client.post(
        f"/api/v1/chat/sessions/{sid}/messages",
        json={"body": "create my startup"},
    )
    assert vague.status_code == 200
    assert vague.json()["ready_for_quote"] is False

    detailed = await api_client.post(
        f"/api/v1/chat/sessions/{sid}/messages",
        json={
            "body": (
                "HealthTrack — chronic condition tracking startup. Brand + landing page, "
                "trustworthy healthcare tone. Tagline: Your health, tracked. "
                "References: apple.com"
            )
        },
    )
    assert detailed.status_code == 200
    body = detailed.json()
    assert body["completeness_pct"] >= 85
    assert body["ready_for_quote"] is True
    assert len(body["spec_draft"]["deliverables"]) >= 1

    fin = await api_client.post(f"/api/v1/chat/sessions/{sid}/finalize")
    assert fin.status_code == 200
    assert "intent_id" in fin.json()
    assert "quote_id" in fin.json()

    fin2 = await api_client.post(f"/api/v1/chat/sessions/{sid}/finalize")
    assert fin2.status_code == 400
