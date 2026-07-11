"""Product-path smoke: intent → quote → order → accept → start → submit (no mocks).

Run with Postgres up (docker compose) from backend/:

    python -m pytest tests/test_product_smoke.py -v
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.identity import DEMO_WORKER_ID
from app.orchestrator.states import OrderStatus, TaskStatus


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
async def test_product_path_scope_to_submit(api_client: AsyncClient):
    """Stage C: one scripted path proves the whole idea without mocks."""
    # 1) Intent → quote (fixture Spec Compiler; chat finalize is equivalent path)
    create = await api_client.post(
        "/api/v1/intents",
        json={
            "raw_text": "I need a Launch Studio brand and landing page for HealthTrack.",
            "attachments": [],
        },
    )
    assert create.status_code == 201
    quote_id = create.json()["quote_id"]

    # 2) Accept quote → order + plan
    accept_quote = await api_client.post(f"/api/v1/quotes/{quote_id}/accept")
    assert accept_quote.status_code == 200
    order_id = accept_quote.json()["order_id"]

    plan = (await api_client.get(f"/api/v1/orders/{order_id}/milestones")).json()
    assert len(plan["tasks"]) >= 1
    task = next(t for t in plan["tasks"] if t["status"] == TaskStatus.READY)
    task_id = task["id"]

    # 3) Client preferences (demo worker first)
    pref = await api_client.post(
        f"/api/v1/orders/{order_id}/tasks/{task_id}/preferences",
        json={
            "ranked_worker_ids": [
                str(DEMO_WORKER_ID),
                "usr_worker_meera",
                "usr_worker_kabir",
            ]
        },
    )
    assert pref.status_code == 200

    # 4) Worker accept → ready → submit
    # accept-interest returns soft "accepted" (Spine state is priority_active)
    assert (await api_client.post(f"/api/v1/tasks/{task_id}/accept-interest")).json()[
        "status"
    ] == "accepted"
    assert (await api_client.post(f"/api/v1/tasks/{task_id}/ready-to-start")).json()[
        "status"
    ] == TaskStatus.IN_PROGRESS
    submit = await api_client.post(
        f"/api/v1/tasks/{task_id}/submit",
        json={
            "notes": "Brand direction v1",
            "asset_urls": ["https://files.example/brand.pdf"],
        },
    )
    assert submit.status_code == 200
    assert submit.json()["status"] == TaskStatus.COMPLETED

    # 5) Order advanced; discussion available
    order = (await api_client.get(f"/api/v1/orders/{order_id}")).json()
    assert order["status"] == OrderStatus.DELIVERY_ACTIVE

    disc = await api_client.get(f"/api/v1/tasks/{task_id}/discussion")
    assert disc.status_code == 200
    assert disc.json()["task_id"] == task_id
