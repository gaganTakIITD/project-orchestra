"""Preference Chat (Stage 3) — Matcher agent turn + finalize → PreferenceSet."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.ai.matcher_chat import compile_matcher_turn, opening_matcher_message
from app.main import app
from app.models.identity import DEMO_WORKER_ID, DEMO_WORKER_KABIR_ID, DEMO_WORKER_MEERA_ID


def test_opening_mentions_shortlist():
    candidates = [
        {
            "worker_id": "a",
            "full_name": "Rohan Verma",
            "score": 0.92,
            "rationale": "Strong logo_design fit",
        },
        {
            "worker_id": "b",
            "full_name": "Meera Nair",
            "score": 0.86,
            "rationale": "Advanced logo_design",
        },
        {
            "worker_id": "c",
            "full_name": "Kabir Anand",
            "score": 0.79,
            "rationale": "Good style fit",
        },
    ]
    msg = opening_matcher_message(candidates, task_title="Logo design")
    assert "3 strong matches" in msg
    assert "Rohan" in msg


def test_compile_matcher_turn_explain_and_reorder():
    candidates = [
        {
            "worker_id": "a",
            "full_name": "Rohan Verma",
            "score": 0.92,
            "rationale": "Expert fit",
            "tasks_completed": 27,
            "on_time_pct": 96,
            "seller_level": "trusted",
            "availability": "available",
        },
        {
            "worker_id": "b",
            "full_name": "Meera Nair",
            "score": 0.86,
            "rationale": "Advanced fit",
            "tasks_completed": 14,
            "on_time_pct": 94,
            "seller_level": "rising",
            "availability": "available",
        },
        {
            "worker_id": "c",
            "full_name": "Kabir Anand",
            "score": 0.79,
            "rationale": "Good fit",
            "tasks_completed": 9,
            "on_time_pct": 90,
            "seller_level": "rising",
            "availability": "busy",
        },
    ]
    why = compile_matcher_turn(candidates=candidates, user_message="Why is Rohan #1?", version=0)
    assert "Rohan" in why.reply
    assert why.candidates[0]["worker_id"] == "a"

    moved = compile_matcher_turn(
        candidates=candidates, user_message="Move Meera to #1", version=0
    )
    assert moved.candidates[0]["worker_id"] == "b"
    assert moved.version == 1
    assert moved.ready_to_confirm is True

    confirm = compile_matcher_turn(
        candidates=moved.candidates, user_message="confirm these three", version=1
    )
    assert confirm.ready_to_confirm is True
    assert "confirm" in confirm.reply.lower() or "PreferenceSet" in confirm.reply


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


async def _ready_task(api_client: AsyncClient) -> tuple[str, str]:
    create = await api_client.post(
        "/api/v1/intents",
        json={"raw_text": "Launch Studio brand and landing for HealthTrack.", "attachments": []},
    )
    assert create.status_code == 201
    accept = await api_client.post(f"/api/v1/quotes/{create.json()['quote_id']}/accept")
    order_id = accept.json()["order_id"]
    plan = (await api_client.get(f"/api/v1/orders/{order_id}/milestones")).json()
    ready = next(t for t in plan["tasks"] if t["status"] == "ready")
    return order_id, ready["id"]


@pytest.mark.asyncio
async def test_preference_chat_turn_and_finalize(api_client: AsyncClient):
    order_id, task_id = await _ready_task(api_client)

    start = await api_client.post(
        "/api/v1/chat/sessions",
        json={
            "agent_type": "matcher",
            "ref_type": "task",
            "ref_id": task_id,
            "order_id": order_id,
        },
    )
    assert start.status_code == 201, start.text
    session = start.json()
    sid = session["id"]
    assert session["agent_type"] == "matcher"
    assert session["ref_id"] == task_id
    assert session["order_id"] == order_id
    assert len(session["candidates"]) >= 3
    assert session["ready_to_confirm"] is True
    assert session["messages"][0]["role"] == "assistant"

    why = await api_client.post(
        f"/api/v1/chat/sessions/{sid}/messages",
        json={"body": "Why is #1 ranked first?"},
    )
    assert why.status_code == 200
    assert why.json()["agent_type"] == "matcher"
    assert len(why.json()["messages"]) >= 3

    move = await api_client.post(
        f"/api/v1/chat/sessions/{sid}/messages",
        json={"body": "Move Meera to #1"},
    )
    assert move.status_code == 200
    ranked = move.json()["candidates"]
    assert ranked[0]["worker_id"] == str(DEMO_WORKER_MEERA_ID)

    fin = await api_client.post(
        f"/api/v1/chat/sessions/{sid}/finalize",
        json={
            "ranked_worker_ids": [
                str(DEMO_WORKER_MEERA_ID),
                str(DEMO_WORKER_ID),
                str(DEMO_WORKER_KABIR_ID),
            ]
        },
    )
    assert fin.status_code == 200, fin.text
    body = fin.json()
    assert body["preference_set_id"]
    assert body["order_id"] == order_id
    assert body["task_id"] == task_id
    assert body.get("intent_id") is None

    plan = (await api_client.get(f"/api/v1/orders/{order_id}/milestones")).json()
    logo = next(t for t in plan["tasks"] if t["id"] == task_id)
    assert logo["status"] == "invited"

    order = (await api_client.get(f"/api/v1/orders/{order_id}")).json()
    assert order["status"] == "assembling_team"

    fin2 = await api_client.post(f"/api/v1/chat/sessions/{sid}/finalize")
    assert fin2.status_code == 400


@pytest.mark.asyncio
async def test_scope_session_still_works_without_body(api_client: AsyncClient):
    """Regression: POST /chat/sessions with no body starts Scope chat."""
    start = await api_client.post("/api/v1/chat/sessions")
    assert start.status_code == 201
    assert start.json()["agent_type"] == "spec_compiler"
    assert start.json()["candidates"] is None or start.json()["candidates"] == []
