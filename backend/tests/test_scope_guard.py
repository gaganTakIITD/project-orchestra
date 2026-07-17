"""Scope Guard — fixture heuristics + discussion flag-only wiring."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.ai.fixtures.scope_guard import classify_fixture
from app.ai.scope_guard import classify, summarize_charter
from app.config import settings
from app.main import app
from app.orchestrator.states import TaskStatus


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


def test_fixture_also_add_flags_drift():
    result = classify_fixture("also add a blog", "Task: Logo design | Scope: SVG mark")
    assert result["scope_drift"] is True
    assert "add" in result["reason"].lower()


def test_fixture_instead_of_and_expansions():
    assert classify_fixture("use blue instead of green")["scope_drift"] is True
    assert classify_fixture("we need more budget for photos")["scope_drift"] is True
    assert classify_fixture("can we extend the deadline by a week")["scope_drift"] is True
    assert classify_fixture("Please keep the mark simple.")["scope_drift"] is False


def test_classify_uses_fixture_without_gemini(monkeypatch):
    monkeypatch.setattr(settings, "gemini_auth", "off")
    monkeypatch.setattr(settings, "require_gemini", False)
    monkeypatch.setattr(settings, "app_env", "development")

    result = classify("also add a blog", summarize_charter(task_title="Logo design"))
    assert result.scope_drift is True
    assert result.source == "fixture"
    assert result.reason


@pytest.mark.asyncio
async def test_post_also_add_blog_sets_scope_flagged(api_client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "gemini_auth", "off")
    monkeypatch.setattr(settings, "require_gemini", False)
    monkeypatch.setattr(settings, "app_env", "development")

    _order_id, task_id = await _order_with_ready_task(api_client)

    post = await api_client.post(
        f"/api/v1/tasks/{task_id}/discussion",
        json={"body": "also add a blog", "message_type": "clarification"},
    )
    assert post.status_code == 200, post.text
    messages = post.json()["messages"]
    flagged = [m for m in messages if m["body"] == "also add a blog"]
    assert len(flagged) == 1
    assert flagged[0]["scope_flagged"] is True
    assert flagged[0]["message_type"] == "scope_change_request"

    from app.db.session import AsyncSessionLocal
    from app.models.platform import AiDecisionLog

    async with AsyncSessionLocal() as session:
        logs = (
            await session.execute(
                select(AiDecisionLog).where(AiDecisionLog.agent_type == "scope_guard")
            )
        ).scalars().all()
        assert len(logs) >= 1
        assert logs[-1].source == "fixture"
        assert logs[-1].output_draft["scope_drift"] is True


@pytest.mark.asyncio
async def test_post_clarification_not_flagged(api_client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "gemini_auth", "off")
    monkeypatch.setattr(settings, "require_gemini", False)
    monkeypatch.setattr(settings, "app_env", "development")

    _order_id, task_id = await _order_with_ready_task(api_client)

    post = await api_client.post(
        f"/api/v1/tasks/{task_id}/discussion",
        json={"body": "Please keep the mark simple.", "message_type": "clarification"},
    )
    assert post.status_code == 200, post.text
    msgs = [m for m in post.json()["messages"] if m["body"].startswith("Please keep")]
    assert len(msgs) == 1
    assert msgs[0]["scope_flagged"] is False
    assert msgs[0]["message_type"] == "clarification"
