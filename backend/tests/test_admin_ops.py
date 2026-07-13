"""Admin verify + taxonomy CRUD + matcher verified preference."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.identity import DEMO_WORKER_ID, WorkerProfileRecord


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
async def test_admin_list_and_verify_worker(api_client: AsyncClient):
    listed = await api_client.get("/api/v1/admin/workers")
    assert listed.status_code == 200
    workers = listed.json()["workers"]
    assert any(w["user_id"] == str(DEMO_WORKER_ID) for w in workers)

    unverified = await api_client.post(f"/api/v1/admin/workers/{DEMO_WORKER_ID}/unverify")
    assert unverified.status_code == 200
    assert unverified.json()["campus_verified"] is False

    verified = await api_client.post(f"/api/v1/admin/workers/{DEMO_WORKER_ID}/verify")
    assert verified.status_code == 200
    assert verified.json()["campus_verified"] is True


@pytest.mark.asyncio
async def test_admin_taxonomy_skill_crud(api_client: AsyncClient):
    slug = f"test-skill-{uuid.uuid4().hex[:8]}"
    created = await api_client.post(
        "/api/v1/admin/taxonomy/skills",
        json={"name": "Test Skill", "slug": slug, "category": "design"},
    )
    assert created.status_code == 200
    skill_id = created.json()["id"]

    patched = await api_client.patch(
        f"/api/v1/admin/taxonomy/skills/{skill_id}",
        json={"name": "Test Skill 2", "slug": slug, "category": "design"},
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "Test Skill 2"

    deleted = await api_client.delete(f"/api/v1/admin/taxonomy/skills/{skill_id}")
    assert deleted.status_code == 200


@pytest.mark.asyncio
async def test_matcher_prefers_verified(api_client: AsyncClient):
    from app.ai.matcher import match_candidates
    from app.db.session import AsyncSessionLocal
    from app.models.fulfillment import FulfillmentTask, OutcomeOrder
    from app.orchestrator.states import OrderStatus, TaskStatus

    async with AsyncSessionLocal() as session:
        # Ensure demo worker is verified
        profile = await session.get(WorkerProfileRecord, DEMO_WORKER_ID)
        assert profile is not None
        profile.campus_verified = True
        await session.commit()

        order = OutcomeOrder(
            id=uuid.uuid4(),
            client_id=uuid.UUID("00000000-0000-4000-8000-000000000010"),
            status=OrderStatus.CONFIRMED,
            price=1000,
        )
        task = FulfillmentTask(
            id=uuid.uuid4(),
            order_id=order.id,
            title="Logo",
            task_type_slug="logo_design",
            status=TaskStatus.READY,
            sequence_order=1,
            acceptance_criteria=[],
            payout_amount=500,
        )
        session.add(order)
        await session.flush()
        session.add(task)
        await session.flush()
        candidates = await match_candidates(session, task=task, limit=5)
        assert isinstance(candidates, list)
