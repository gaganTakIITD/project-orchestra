import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.identity import DEMO_WORKER_ID
from app.schemas.worker import PROFILE_LIVE_THRESHOLD, compute_profile_completion_pct


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
async def test_upsert_worker_profile_create_and_get(api_client: AsyncClient):
    payload = {
        "full_name": "Rohan Verma",
        "community_type": "design",
        "headline": "Logo systems for campus startups",
        "bio": "I design crisp brand marks and reusable identity kits.",
        "availability_status": "available",
        "weekly_hours_available": 15,
        "max_concurrent_tasks": 2,
        "payout_min": 2000,
        "payout_max": 5000,
        "figma_url": "https://figma.com/@rohan",
        "skills": [
            {
                "skill_id": "skill_logo",
                "name": "Logo Design",
                "proficiency": "expert",
                "years_experience": 3,
            },
            {
                "skill_id": "skill_brand",
                "name": "Brand Identity",
                "proficiency": "advanced",
            },
            {"skill_id": "skill_figma", "name": "Figma", "proficiency": "advanced"},
        ],
        "tools": [
            {"tool_id": "tool_figma", "name": "Figma", "proficiency": "expert"},
            {"tool_id": "tool_ai", "name": "Illustrator", "proficiency": "advanced"},
        ],
        "task_types": [
            {
                "task_type_id": "tt_logo",
                "name": "Logo Design",
                "slug": "logo_design",
                "proficiency": "expert",
            }
        ],
        "portfolio": [
            {
                "id": "pf_new",
                "worker_id": "",
                "title": "Campus club rebrand",
                "description": "Full identity for a student club",
                "project_url": "https://behance.net/example",
                "tags": ["branding"],
                "tools_used": ["Figma"],
                "is_featured": True,
            }
        ],
        "is_active": True,
    }

    patch = await api_client.patch("/api/v1/workers/profile", json=payload)
    assert patch.status_code == 200
    saved = patch.json()
    assert saved["user_id"] == str(DEMO_WORKER_ID)
    assert saved["headline"] == payload["headline"]
    assert saved["profile_completion_pct"] >= PROFILE_LIVE_THRESHOLD
    assert saved["is_active"] is True
    assert len(saved["skills"]) == 3
    assert saved["portfolio"][0]["worker_id"] == str(DEMO_WORKER_ID)

    got = await api_client.get("/api/v1/workers/profile")
    assert got.status_code == 200
    assert got.json()["headline"] == payload["headline"]
    assert got.json()["bio"] == payload["bio"]


@pytest.mark.asyncio
async def test_upsert_profile_live_gate_below_threshold(api_client: AsyncClient):
    """Incomplete profiles stay offline even if is_active is requested."""
    patch = await api_client.patch(
        "/api/v1/workers/profile",
        json={
            "full_name": "Rohan Verma",
            "community_type": "design",
            "headline": "Hi",
            "bio": "",
            "availability_status": "available",
            "skills": [],
            "tools": [],
            "task_types": [],
            "portfolio": [],
            "is_active": True,
        },
    )
    assert patch.status_code == 200
    body = patch.json()
    assert body["profile_completion_pct"] < PROFILE_LIVE_THRESHOLD
    assert body["is_active"] is False


def test_compute_profile_completion_pct_rules():
    full = compute_profile_completion_pct(
        headline="Designer",
        bio="I make logos",
        skills=[{"name": "a"}, {"name": "b"}, {"name": "c"}],
        tools=[{"name": "t1"}, {"name": "t2"}],
        task_types=[{"slug": "logo_design"}],
        portfolio=[{"id": "1"}],
        availability_status="available",
        payout_min=1000,
        payout_max=5000,
        github_url=None,
        figma_url="https://figma.com/x",
        behance_url=None,
        linkedin_url=None,
    )
    assert full == 100

    thin = compute_profile_completion_pct(
        headline="x",
        bio="",
        skills=[],
        tools=[],
        task_types=[],
        portfolio=[],
        availability_status="available",
        payout_min=None,
        payout_max=None,
        github_url=None,
        figma_url=None,
        behance_url=None,
        linkedin_url=None,
    )
    assert thin < PROFILE_LIVE_THRESHOLD


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
