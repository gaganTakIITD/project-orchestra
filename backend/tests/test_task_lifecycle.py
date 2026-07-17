"""Worker lifecycle + discussion + delivery integration tests."""

from unittest.mock import MagicMock

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.config import settings
from app.main import app
from app.models.identity import DEMO_WORKER_ID
from app.models.platform import EventLog
from app.orchestrator.states import ActorType, OrderStatus, TaskStatus
from app.services import auth as auth_service


def _setup_clerk_mode(monkeypatch):
    """Switch settings to Clerk mode with a mock JWKS signing key."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    issuer = "https://example.clerk.accounts.dev"
    monkeypatch.setattr(settings, "auth_mode", "clerk")
    monkeypatch.setattr(settings, "clerk_jwks_url", f"{issuer}/.well-known/jwks.json")
    monkeypatch.setattr(settings, "clerk_issuer", issuer)
    monkeypatch.setattr(settings, "clerk_audience", None)
    monkeypatch.setattr(settings, "admin_email_allowlist", "")
    auth_service._jwks_clients.clear()

    fake_client = MagicMock()
    fake_signing_key = MagicMock()
    fake_signing_key.key = public_pem
    fake_client.get_signing_key_from_jwt.return_value = fake_signing_key
    monkeypatch.setattr(auth_service, "_jwks_client", lambda: fake_client)
    return private_key, issuer


def _clerk_token(private_key, issuer: str, *, sub: str, email: str) -> str:
    return jwt.encode(
        {"sub": sub, "email": email, "name": email.split("@")[0], "iss": issuer},
        private_key,
        algorithm="RS256",
    )


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


async def _set_preferences(
    api_client: AsyncClient,
    order_id: str,
    task_id: str,
    *,
    ranked_worker_ids: list[str] | None = None,
    headers: dict | None = None,
) -> None:
    hdrs = headers or {}
    if ranked_worker_ids is None:
        cands = await api_client.get(
            f"/api/v1/orders/{order_id}/tasks/{task_id}/candidates",
            headers=hdrs,
        )
        assert cands.status_code == 200, cands.text
        ids = [c["worker_id"] for c in cands.json()]
        assert ids, "expected live candidates for preferences"
        need = max(1, min(3, len(ids)))
        ranked_worker_ids = ids[:need]
    pref = await api_client.post(
        f"/api/v1/orders/{order_id}/tasks/{task_id}/preferences",
        json={"ranked_worker_ids": ranked_worker_ids},
        headers=hdrs,
    )
    assert pref.status_code == 200, pref.text


async def _complete_task(api_client: AsyncClient, order_id: str, task_id: str) -> None:
    await _set_preferences(api_client, order_id, task_id)

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

    await _complete_task(api_client, order_id, task_id)

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
    assert accept.status_code == 409
    assert "invited" in accept.json()["detail"].lower()

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
async def test_worker_discussion_forbidden_until_accept(api_client: AsyncClient):
    """Invited worker cannot open discussion until Accept interest assigns them."""
    order_id, task_id = await _order_with_ready_task(api_client)
    await _set_preferences(api_client, order_id, task_id)

    worker_headers = {"X-Orchestra-Role": "worker"}
    denied = await api_client.get(
        f"/api/v1/tasks/{task_id}/discussion",
        headers=worker_headers,
    )
    assert denied.status_code == 403

    denied_post = await api_client.post(
        f"/api/v1/tasks/{task_id}/discussion",
        json={"body": "too early", "message_type": "clarification"},
        headers=worker_headers,
    )
    assert denied_post.status_code == 403

    acc = await api_client.post(
        f"/api/v1/tasks/{task_id}/accept-interest",
        headers=worker_headers,
    )
    assert acc.status_code == 200, acc.text

    ok = await api_client.get(
        f"/api/v1/tasks/{task_id}/discussion",
        headers=worker_headers,
    )
    assert ok.status_code == 200

    post = await api_client.post(
        f"/api/v1/tasks/{task_id}/discussion",
        json={"body": "Hello from assigned worker", "message_type": "clarification"},
        headers=worker_headers,
    )
    assert post.status_code == 200, post.text
    assert any(
        m["body"].startswith("Hello from assigned") for m in post.json()["messages"]
    )


@pytest.mark.asyncio
async def test_assigned_worker_discussion_attributed_as_worker_even_if_db_role_client(
    api_client: AsyncClient, monkeypatch
):
    """Hybrid account: assigned worker posts with DB role=client still attributed
    as worker (sender_id + DiscussionMessagePosted actor_type), not the client."""
    private_key, issuer = _setup_clerk_mode(monkeypatch)
    client_headers = {
        "Authorization": f"Bearer {_clerk_token(private_key, issuer, sub='user_disc_client', email='disc.client@example.com')}"
    }
    worker_headers = {
        "Authorization": f"Bearer {_clerk_token(private_key, issuer, sub='user_disc_worker', email='disc.worker@example.com')}"
    }

    client_me = await api_client.get("/api/v1/auth/me", headers=client_headers)
    assert client_me.status_code == 200
    client_id = client_me.json()["id"]

    create = await api_client.post(
        "/api/v1/intents",
        json={"raw_text": "Launch Studio brand and landing for my SaaS.", "attachments": []},
        headers=client_headers,
    )
    assert create.status_code == 201, create.text
    accept = await api_client.post(
        f"/api/v1/quotes/{create.json()['quote_id']}/accept",
        headers=client_headers,
    )
    assert accept.status_code == 200, accept.text
    order_id = accept.json()["order_id"]
    plan = (
        await api_client.get(
            f"/api/v1/orders/{order_id}/milestones",
            headers=client_headers,
        )
    ).json()
    task_id = next(t["id"] for t in plan["tasks"] if t["status"] == TaskStatus.READY)

    switch = await api_client.patch(
        "/api/v1/auth/role",
        json={"role": "worker"},
        headers=worker_headers,
    )
    assert switch.status_code == 200
    worker_id = switch.json()["id"]
    assert worker_id != client_id

    # Go live so Matcher includes this Clerk worker in candidates.
    live = await api_client.post(
        "/api/v1/workers/profile",
        headers=worker_headers,
        json={
            "full_name": "Disc Worker",
            "community_type": "design",
            "headline": "Logo systems for campus startups and pilots",
            "bio": "I design crisp brand marks and reusable identity kits for early products.",
            "availability_status": "available",
            "weekly_hours_available": 15,
            "max_concurrent_tasks": 2,
            "payout_min": 2000,
            "payout_max": 5000,
            "is_active": True,
            "figma_url": "https://figma.com/@discworker",
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
                },
                {
                    "task_type_id": "tt_brand",
                    "name": "Brand Identity",
                    "slug": "brand_identity",
                    "proficiency": "advanced",
                },
            ],
            "portfolio": [
                {
                    "id": "pf_disc",
                    "title": "Sample mark",
                    "description": "Campus brand system",
                    "tags": ["logo"],
                    "tools_used": ["Figma"],
                    "is_featured": True,
                }
            ],
        },
    )
    assert live.status_code == 200, live.text
    assert live.json()["is_active"] is True

    # Drop seeded talent so the live Clerk worker is in the candidate shortlist
    # (default matcher limit=10 otherwise buries a new profile under 10 seeds).
    from app.db.seed import purge_seed_workers
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        await purge_seed_workers(session)

    cands = await api_client.get(
        f"/api/v1/orders/{order_id}/tasks/{task_id}/candidates",
        headers=client_headers,
    )
    assert cands.status_code == 200, cands.text
    cand_ids = [c["worker_id"] for c in cands.json()]
    assert worker_id in cand_ids, cand_ids

    await _set_preferences(
        api_client,
        order_id,
        task_id,
        ranked_worker_ids=[worker_id],
        headers=client_headers,
    )

    acc = await api_client.post(
        f"/api/v1/tasks/{task_id}/accept-interest",
        headers=worker_headers,
    )
    assert acc.status_code == 200, acc.text
    assert acc.json()["status"] == "accepted"

    assigned = (
        await api_client.get(
            f"/api/v1/orders/{order_id}/milestones",
            headers=client_headers,
        )
    ).json()
    task_row = next(t for t in assigned["tasks"] if t["id"] == task_id)
    assert task_row["assigned_worker_id"] == worker_id

    # Active portal role flipped back to client — participation still governs chat.
    demote = await api_client.patch(
        "/api/v1/auth/role",
        json={"role": "client"},
        headers=worker_headers,
    )
    assert demote.status_code == 200
    assert demote.json()["role"] == "client"

    post = await api_client.post(
        f"/api/v1/tasks/{task_id}/discussion",
        json={"body": "Worker note while portal role is client.", "message_type": "clarification"},
        headers=worker_headers,
    )
    assert post.status_code == 200, post.text
    mine = [m for m in post.json()["messages"] if m["body"].startswith("Worker note")]
    assert len(mine) == 1
    assert mine[0]["sender_id"] == worker_id

    from app.db.session import AsyncSessionLocal
    import uuid as uuid_mod

    async with AsyncSessionLocal() as session:
        events = (
            await session.execute(
                select(EventLog).where(
                    EventLog.aggregate_type == "task",
                    EventLog.aggregate_id == uuid_mod.UUID(task_id),
                    EventLog.event_type == "DiscussionMessagePosted",
                )
            )
        ).scalars().all()
        assert events
        latest = max(events, key=lambda e: e.created_at)
        assert str(latest.actor_id) == worker_id
        assert latest.actor_type == ActorType.WORKER


@pytest.mark.asyncio
async def test_full_dag_delivery_and_accept(api_client: AsyncClient):
    order_id, _ = await _order_with_ready_task(api_client)

    for _ in range(5):
        plan = (await api_client.get(f"/api/v1/orders/{order_id}/milestones")).json()
        ready = [t for t in plan["tasks"] if t["status"] == TaskStatus.READY]
        assert ready, f"no ready task; {[t['status'] for t in plan['tasks']]}"
        await _complete_task(api_client, order_id, ready[0]["id"])

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

    await _set_preferences(api_client, order_id, task_id)
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
    order_id, task_id = await _order_with_ready_task(api_client)
    await _complete_task(api_client, order_id, task_id)

    qa = await api_client.get(f"/api/v1/tasks/{task_id}/qa")
    assert qa.status_code == 200, qa.text
    body = qa.json()
    assert body["task_id"] == task_id
    assert body["result"] == "pass"
    assert body["feedback"]
    assert body["reviewed_by"] == "ai"
    assert body["submission_id"]
    assert isinstance(body["evidence"], list)