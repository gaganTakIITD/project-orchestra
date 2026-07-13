"""Worker lifecycle + discussion + delivery integration tests."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app
from app.models.identity import DEMO_WORKER_ID
from app.models.platform import EventLog
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


async def _order_with_ready_task(api_client: AsyncClient) -> tuple[str, str]:
    create = await api_client.post(
        "/api/v1/intents",
        json={"raw_text": "Launch Studio brand and landing for my SaaS.", "attachments": []},
    )
    assert create.status_code == 201
    accept = await api_client.post(f"/api/v1/quotes/{create.json()['quote_id']}/accept")
    assert accept.status_code == 200
    order_id = accept.json()["order_id"]
    plan = (await api_client.get(f"/api/v1/orders/{order_id}/milestones")).json()
    ready = next(t for t in plan["tasks"] if t["status"] == TaskStatus.READY)
    return order_id, ready["id"]


async def _complete_task(api_client: AsyncClient, task_id: str) -> None:
    acc = await api_client.post(f"/api/v1/tasks/{task_id}/accept-interest")
    assert acc.status_code == 200, acc.text
    # Contract alias — Spine state is priority_active
    assert acc.json()["status"] == "accepted"

    ready = await api_client.post(f"/api/v1/tasks/{task_id}/ready-to-start")
    assert ready.status_code == 200, ready.text
    assert ready.json()["status"] == TaskStatus.IN_PROGRESS

    submit = await api_client.post(
        f"/api/v1/tasks/{task_id}/submit",
        json={
            "notes": "Work product attached. lighthouse: 85",
            "asset_urls": [
                "https://files.example/logo.svg",
                "https://files.example/logo.png",
                "https://files.example/out.pdf",
                "https://preview.example/live",
            ],
        },
    )
    assert submit.status_code == 200, submit.text
    assert submit.json()["status"] == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_accept_interest_ready_to_start_submit(api_client: AsyncClient):
    order_id, task_id = await _order_with_ready_task(api_client)

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

    await _complete_task(api_client, task_id)

    plan = (await api_client.get(f"/api/v1/orders/{order_id}/milestones")).json()
    task = next(t for t in plan["tasks"] if t["id"] == task_id)
    assert task["status"] == TaskStatus.COMPLETED
    assert task["assigned_worker_id"] == str(DEMO_WORKER_ID)

    logo = next(t for t in plan["tasks"] if t["title"] == "Logo design")
    assert logo["status"] == TaskStatus.READY

    order = (await api_client.get(f"/api/v1/orders/{order_id}")).json()
    assert order["status"] == OrderStatus.DELIVERY_ACTIVE

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        events = (
            await session.execute(
                select(EventLog).where(
                    EventLog.aggregate_type == "task",
                    EventLog.aggregate_id == __import__("uuid").UUID(task_id),
                )
            )
        ).scalars().all()
        types = {e.event_type for e in events}
        assert "InterestAccepted" in types
        assert "SubmissionReceived" in types
        assert "QualityPassed" in types

        from app.models.platform import AiDecisionLog

        qa_logs = (
            await session.execute(
                select(AiDecisionLog).where(AiDecisionLog.agent_type == "qa_judge")
            )
        ).scalars().all()
        assert len(qa_logs) >= 1
        assert qa_logs[-1].source == "fixture"
        assert qa_logs[-1].output_draft["result"] == "pass"


@pytest.mark.asyncio
async def test_accept_from_ready_without_preferences(api_client: AsyncClient):
    _order_id, task_id = await _order_with_ready_task(api_client)

    accept = await api_client.post(f"/api/v1/tasks/{task_id}/accept-interest")
    assert accept.status_code == 200
    assert accept.json()["status"] == "accepted"

    ready = await api_client.post(f"/api/v1/tasks/{task_id}/ready-to-start")
    assert ready.status_code == 200
    assert ready.json()["status"] == TaskStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_discussion_thread(api_client: AsyncClient):
    _order_id, task_id = await _order_with_ready_task(api_client)

    disc = await api_client.get(f"/api/v1/tasks/{task_id}/discussion")
    assert disc.status_code == 200
    body = disc.json()
    assert body["task_id"] == task_id
    assert len(body["messages"]) >= 1

    post = await api_client.post(
        f"/api/v1/tasks/{task_id}/discussion",
        json={"body": "Please keep the mark simple.", "message_type": "clarification"},
    )
    assert post.status_code == 200
    assert any(m["body"].startswith("Please keep") for m in post.json()["messages"])


@pytest.mark.asyncio
async def test_full_dag_delivery_and_accept(api_client: AsyncClient):
    order_id, _ = await _order_with_ready_task(api_client)

    for _ in range(5):
        plan = (await api_client.get(f"/api/v1/orders/{order_id}/milestones")).json()
        ready = [t for t in plan["tasks"] if t["status"] == TaskStatus.READY]
        assert ready, f"no ready task; {[t['status'] for t in plan['tasks']]}"
        await _complete_task(api_client, ready[0]["id"])

    order = (await api_client.get(f"/api/v1/orders/{order_id}")).json()
    assert order["status"] == OrderStatus.DELIVERED

    delivery = await api_client.get(f"/api/v1/orders/{order_id}/delivery")
    assert delivery.status_code == 200, delivery.text
    assert delivery.json()["order_id"] == order_id
    assert len(delivery.json()["assets"]) >= 1

    closed = await api_client.post(f"/api/v1/orders/{order_id}/accept-delivery")
    assert closed.status_code == 200, closed.text
    assert closed.json()["status"] == OrderStatus.CLOSED


@pytest.mark.asyncio
async def test_submit_qa_fail_moves_to_rework(api_client: AsyncClient, monkeypatch):
    """Spine executes qa_fail when QA Judge proposes fail — no unlock."""
    from app.ai.gateway import QAProposal

    order_id, task_id = await _order_with_ready_task(api_client)

    def _fail_qa(**_kwargs):
        return QAProposal(
            result="fail",
            score=0.2,
            confidence=0.95,
            feedback="Fixture forced fail",
            evidence=[
                {
                    "criterion": "Forced",
                    "check_type": "deterministic",
                    "passed": False,
                    "detail": "test",
                }
            ],
            action="approve",
            source="fixture",
        )

    monkeypatch.setattr(
        "app.services.task_lifecycle.generate_qa_proposal",
        _fail_qa,
    )

    acc = await api_client.post(f"/api/v1/tasks/{task_id}/accept-interest")
    assert acc.status_code == 200
    ready = await api_client.post(f"/api/v1/tasks/{task_id}/ready-to-start")
    assert ready.status_code == 200
    submit = await api_client.post(
        f"/api/v1/tasks/{task_id}/submit",
        json={"notes": "bad", "asset_urls": ["https://files.example/out.pdf"]},
    )
    assert submit.status_code == 200
    assert submit.json()["status"] == TaskStatus.REWORK

    qa = await api_client.get(f"/api/v1/tasks/{task_id}/qa")
    assert qa.status_code == 200, qa.text
    body = qa.json()
    assert body["task_id"] == task_id
    assert body["result"] == "fail"
    assert body["feedback"] == "Fixture forced fail"
    assert body["score"] == 0.2
    assert isinstance(body["evidence"], list)
    assert len(body["evidence"]) >= 1
    assert body["evidence"][0]["passed"] is False
    assert body["reviewed_by"] == "ai"
    assert body["submission_id"]

    plan = (await api_client.get(f"/api/v1/orders/{order_id}/milestones")).json()
    logo = next(t for t in plan["tasks"] if t["title"] == "Logo design")
    assert logo["status"] == TaskStatus.BLOCKED


@pytest.mark.asyncio
async def test_submit_qa_pass_exposes_review(api_client: AsyncClient):
    """Pass path: GET /tasks/{id}/qa returns the latest review."""
    _order_id, task_id = await _order_with_ready_task(api_client)
    await _complete_task(api_client, task_id)

    qa = await api_client.get(f"/api/v1/tasks/{task_id}/qa")
    assert qa.status_code == 200, qa.text
    body = qa.json()
    assert body["task_id"] == task_id
    assert body["result"] == "pass"
    assert body["feedback"]
    assert body["reviewed_by"] == "ai"
    assert body["submission_id"]
    assert isinstance(body["evidence"], list)
