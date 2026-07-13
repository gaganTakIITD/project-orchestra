"""Product-path smoke: intent/chat → quote → order → accept → start → submit (no mocks).

Run with Postgres up (docker compose) from backend/:

    python -m pytest tests/test_product_smoke.py -v
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.identity import DEMO_WORKER_ID
from app.orchestrator.states import OrderStatus, TaskStatus

# Assets that satisfy Architect deterministic rules across the Launch Studio DAG.
_PASSING_ASSETS = [
    "https://files.example/logo.svg",
    "https://files.example/logo.png",
    "https://files.example/out.pdf",
    "https://preview.example/live",
]


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


_DEMO_RANKED = [
    str(DEMO_WORKER_ID),
    "usr_worker_meera",
    "usr_worker_kabir",
]


async def _set_preferences(api_client: AsyncClient, order_id: str, task_id: str) -> None:
    pref = await api_client.post(
        f"/api/v1/orders/{order_id}/tasks/{task_id}/preferences",
        json={"ranked_worker_ids": list(_DEMO_RANKED)},
    )
    assert pref.status_code == 200, pref.text


async def _complete_ready_task(
    api_client: AsyncClient, order_id: str, task_id: str
) -> None:
    await _set_preferences(api_client, order_id, task_id)
    assert (await api_client.post(f"/api/v1/tasks/{task_id}/accept-interest")).json()[
        "status"
    ] == "accepted"
    assert (await api_client.post(f"/api/v1/tasks/{task_id}/ready-to-start")).json()[
        "status"
    ] == TaskStatus.IN_PROGRESS
    submit = await api_client.post(
        f"/api/v1/tasks/{task_id}/submit",
        json={
            "notes": "Work product attached. lighthouse: 85",
            "asset_urls": list(_PASSING_ASSETS),
        },
    )
    assert submit.status_code == 200, submit.text
    assert submit.json()["status"] == TaskStatus.COMPLETED


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

    # 3) Client preferences → worker accept → ready → submit
    await _complete_ready_task(api_client, order_id, task_id)

    # 4) Order advanced; discussion available
    order = (await api_client.get(f"/api/v1/orders/{order_id}")).json()
    assert order["status"] == OrderStatus.DELIVERY_ACTIVE

    disc = await api_client.get(f"/api/v1/tasks/{task_id}/discussion")
    assert disc.status_code == 200
    assert disc.json()["task_id"] == task_id


@pytest.mark.asyncio
async def test_chat_path_finalize_to_delivery_accept(api_client: AsyncClient):
    """Chat finalize → quote accept → prefs → worker submit → delivery accept."""
    start = await api_client.post("/api/v1/chat/sessions")
    assert start.status_code == 201
    sid = start.json()["id"]

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
    assert detailed.json()["ready_for_quote"] is True

    fin = await api_client.post(f"/api/v1/chat/sessions/{sid}/finalize")
    assert fin.status_code == 200
    quote_id = fin.json()["quote_id"]

    accept_quote = await api_client.post(f"/api/v1/quotes/{quote_id}/accept")
    assert accept_quote.status_code == 200
    order_id = accept_quote.json()["order_id"]

    # Walk the full DAG — preferences required on every ready task before accept.
    for _ in range(8):
        plan = (await api_client.get(f"/api/v1/orders/{order_id}/milestones")).json()
        ready = [t for t in plan["tasks"] if t["status"] == TaskStatus.READY]
        if not ready:
            break
        await _complete_ready_task(api_client, order_id, ready[0]["id"])
    else:
        pytest.fail("DAG did not finish within task budget")

    order = (await api_client.get(f"/api/v1/orders/{order_id}")).json()
    assert order["status"] == OrderStatus.DELIVERED

    delivery = await api_client.get(f"/api/v1/orders/{order_id}/delivery")
    assert delivery.status_code == 200
    assert len(delivery.json()["assets"]) >= 1

    closed = await api_client.post(f"/api/v1/orders/{order_id}/accept-delivery")
    assert closed.status_code == 200
    assert closed.json()["status"] == OrderStatus.CLOSED
