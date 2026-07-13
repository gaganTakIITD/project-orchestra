"""Track F — Pricing Reasoner chat finalize + scope draft undo."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.ai.pricing_reasoner import compile_pricing_turn, opening_pricing_message
from app.main import app


def test_opening_pricing_mentions_price():
    msg = opening_pricing_message(
        {
            "price": 14000,
            "risk_tier": "L1",
            "sku_name": "Launch Studio",
            "ai_rationale": "Standard band.",
        }
    )
    assert "14,000" in msg or "14000" in msg
    assert "L1" in msg


def test_compile_pricing_turn_drivers_and_confirm():
    quote = {
        "quote_id": "q1",
        "price": 14000,
        "risk_tier": "L1",
        "sku_name": "Launch Studio",
        "sku_base_price": 14000,
        "deliverable_count": 4,
        "mapped_task_types": ["logo_design", "landing_page_frontend"],
        "revision_limit": 2,
        "ai_rationale": "Standard Launch Studio scope.",
        "ai_confidence": 0.88,
        "deadline": "2026-08-01T00:00:00+00:00",
        "sku_typical_days": 14,
    }
    drivers = compile_pricing_turn(quote=quote, user_message="Why this price?", version=0)
    assert "Price drivers" in drivers.reply or "SKU" in drivers.reply
    assert drivers.ready_to_confirm is True

    risk = compile_pricing_turn(quote=quote, user_message="What about risk?", version=0)
    assert "L1" in risk.reply

    confirm = compile_pricing_turn(quote=quote, user_message="confirm looks good", version=0)
    assert confirm.ready_to_confirm is True
    assert confirm.version == 1


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
async def test_pricing_chat_turn_and_finalize_accepts_quote(api_client: AsyncClient):
    create = await api_client.post(
        "/api/v1/intents",
        json={"raw_text": "Launch Studio brand and landing for HealthTrack.", "attachments": []},
    )
    assert create.status_code == 201
    quote_id = create.json()["quote_id"]

    start = await api_client.post(
        "/api/v1/chat/sessions",
        json={"agent_type": "pricing", "ref_type": "quote", "ref_id": quote_id},
    )
    assert start.status_code == 201, start.text
    session = start.json()
    sid = session["id"]
    assert session["agent_type"] == "pricing"
    assert session["ref_id"] == quote_id
    assert session["ready_to_confirm"] is True
    assert session["messages"][0]["role"] == "assistant"

    why = await api_client.post(
        f"/api/v1/chat/sessions/{sid}/messages",
        json={"body": "Why this price?"},
    )
    assert why.status_code == 200
    assert why.json()["agent_type"] == "pricing"
    assert "SKU" in why.json()["messages"][-1]["body"] or "driver" in why.json()["messages"][-1]["body"].lower()

    fin = await api_client.post(f"/api/v1/chat/sessions/{sid}/finalize")
    assert fin.status_code == 200, fin.text
    body = fin.json()
    assert body["quote_id"] == quote_id
    assert body["order_id"]
    assert body.get("intent_id") is None

    order = (await api_client.get(f"/api/v1/orders/{body['order_id']}")).json()
    assert order["quote_id"] == quote_id
    assert order["status"] == "confirmed" or order["status"] == "assembling_team"

    fin2 = await api_client.post(f"/api/v1/chat/sessions/{sid}/finalize")
    assert fin2.status_code == 400


@pytest.mark.asyncio
async def test_scope_undo_restores_previous_draft(api_client: AsyncClient):
    start = await api_client.post("/api/v1/chat/sessions")
    assert start.status_code == 201
    sid = start.json()["id"]
    assert start.json()["can_undo"] is False

    first = await api_client.post(
        f"/api/v1/chat/sessions/{sid}/messages",
        json={
            "body": (
                "HealthTrack helps chronic condition tracking — need brand and landing page, "
                "trustworthy modern healthcare. Tagline: Your health, tracked."
            )
        },
    )
    assert first.status_code == 200
    after_first = first.json()
    assert after_first["can_undo"] is True
    v1 = after_first["spec_version"]
    draft_v1_statement = after_first["spec_draft"]["outcome_statement"]
    assert v1 >= 1

    second = await api_client.post(
        f"/api/v1/chat/sessions/{sid}/messages",
        json={"body": "Also add Hindi copy on the landing page."},
    )
    assert second.status_code == 200
    after_second = second.json()
    assert after_second["spec_version"] > v1
    msg_count = len(after_second["messages"])

    undo = await api_client.post(f"/api/v1/chat/sessions/{sid}/undo")
    assert undo.status_code == 200, undo.text
    restored = undo.json()
    assert restored["spec_version"] == v1
    assert restored["spec_draft"]["outcome_statement"] == draft_v1_statement
    assert len(restored["messages"]) < msg_count

    # Matcher sessions reject undo
    create = await api_client.post(
        "/api/v1/intents",
        json={"raw_text": "Launch Studio brand and landing for HealthTrack.", "attachments": []},
    )
    accept = await api_client.post(f"/api/v1/quotes/{create.json()['quote_id']}/accept")
    order_id = accept.json()["order_id"]
    plan = (await api_client.get(f"/api/v1/orders/{order_id}/milestones")).json()
    ready = next(t for t in plan["tasks"] if t["status"] == "ready")
    matcher = await api_client.post(
        "/api/v1/chat/sessions",
        json={
            "agent_type": "matcher",
            "ref_type": "task",
            "ref_id": ready["id"],
            "order_id": order_id,
        },
    )
    assert matcher.status_code == 201
    bad = await api_client.post(f"/api/v1/chat/sessions/{matcher.json()['id']}/undo")
    assert bad.status_code == 400
