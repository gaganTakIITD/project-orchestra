"""DB-backed Matcher tests — ranked shortlist from worker_profiles."""

import pytest
import uuid
from httpx import ASGITransport, AsyncClient

from app.ai.matcher import match_candidates
from app.main import app
from app.models.identity import (
    DEMO_WORKER_ID,
    DEMO_WORKER_KABIR_ID,
    DEMO_WORKER_MEERA_ID,
    SEED_FAKE_WORKER_IDS,
    SEED_ORIGINAL_WORKER_IDS,
    SEED_WORKER_POOL_IDS,
    User,
    WorkerProfileRecord,
)
from sqlalchemy import select


@pytest.fixture
async def db_session():
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
            yield session
    except Exception as e:
        pytest.skip(f"Database unavailable: {e}")


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
async def test_seed_keeps_ten_profiles_five_original_five_fake(db_session):
    assert len(SEED_WORKER_POOL_IDS) == 10
    assert len(SEED_ORIGINAL_WORKER_IDS) == 5
    assert len(SEED_FAKE_WORKER_IDS) == 5

    result = await db_session.execute(
        select(WorkerProfileRecord).where(
            WorkerProfileRecord.user_id.in_(SEED_WORKER_POOL_IDS)
        )
    )
    profiles = list(result.scalars().all())
    assert len(profiles) == 10
    by_id = {p.user_id: p for p in profiles}
    for wid in SEED_ORIGINAL_WORKER_IDS:
        assert by_id[wid].campus_verified is True
        assert by_id[wid].is_active is True
    for wid in SEED_FAKE_WORKER_IDS:
        assert by_id[wid].campus_verified is False
        assert by_id[wid].is_active is True


@pytest.mark.asyncio
async def test_match_candidates_ranks_seeded_workers(db_session):
    candidates = await match_candidates(db_session, task_type_slug="logo_design")
    assert len(candidates) >= 3
    ids = {c["worker_id"] for c in candidates}
    assert str(DEMO_WORKER_ID) in ids
    assert str(DEMO_WORKER_MEERA_ID) in ids
    assert str(DEMO_WORKER_KABIR_ID) in ids
    # Highest score first — Rohan (expert + trusted) should lead
    assert candidates[0]["worker_id"] == str(DEMO_WORKER_ID)
    assert candidates[0]["score"] >= candidates[1]["score"]
    assert all("rationale" in c and "headline" in c for c in candidates)


@pytest.mark.asyncio
async def test_match_candidates_empty_pool(db_session):
    # Deactivate the full matcher pool (design + tech seed workers)
    result = await db_session.execute(select(WorkerProfileRecord))
    for profile in result.scalars().all():
        profile.is_active = False
    await db_session.flush()

    candidates = await match_candidates(db_session, task_type_slug="logo_design")
    assert candidates == []


@pytest.mark.asyncio
async def test_match_candidates_filters_unrelated_task_type(db_session):
    # Add a tech-only worker who should not match logo_design
    tech_id = uuid.UUID("00000000-0000-4000-8000-000000000099")
    db_session.add(
        User(
            id=tech_id,
            email="tech-only@iitd.ac.in",
            full_name="Dev Only",
            role="worker",
            is_active=True,
            email_verified=True,
        )
    )
    db_session.add(
        WorkerProfileRecord(
            user_id=tech_id,
            community_type="tech",
            headline="Backend engineer",
            bio="APIs and databases only.",
            availability_status="available",
            is_active=True,
            profile_completion_pct=90,
            skills=[{"skill_id": "skill_python", "name": "Python", "proficiency": "expert"}],
            tools=[{"tool_id": "tool_docker", "name": "Docker", "proficiency": "advanced"}],
            task_types=[
                {
                    "task_type_id": "tt_api",
                    "name": "API Integration",
                    "slug": "api_integration",
                    "proficiency": "expert",
                }
            ],
            portfolio=[{"id": "pf_t", "worker_id": str(tech_id), "title": "API", "tags": [], "tools_used": [], "is_featured": False}],
            stats={"worker_id": str(tech_id), "tasks_completed": 20, "on_time_pct": 99, "seller_level": "trusted"},
        )
    )
    await db_session.flush()

    candidates = await match_candidates(db_session, task_type_slug="logo_design")
    ids = {c["worker_id"] for c in candidates}
    assert str(tech_id) not in ids
    assert str(DEMO_WORKER_ID) in ids


@pytest.mark.asyncio
async def test_candidates_api_returns_db_workers(api_client: AsyncClient):
    create = await api_client.post(
        "/api/v1/intents",
        json={"raw_text": "Launch Studio brand and landing for HealthTrack.", "attachments": []},
    )
    assert create.status_code == 201
    accept = await api_client.post(f"/api/v1/quotes/{create.json()['quote_id']}/accept")
    order_id = accept.json()["order_id"]
    plan = (await api_client.get(f"/api/v1/orders/{order_id}/milestones")).json()
    logo = next(t for t in plan["tasks"] if t["task_type_slug"] == "logo_design")

    res = await api_client.get(f"/api/v1/orders/{order_id}/tasks/{logo['id']}/candidates")
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 3
    assert body[0]["worker_id"] == str(DEMO_WORKER_ID)
    # Must be real UUIDs from DB — not fixture string IDs like usr_worker_meera
    assert all(len(c["worker_id"]) == 36 for c in body)
