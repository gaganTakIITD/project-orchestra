import pytest
from httpx import ASGITransport, AsyncClient

from app.ai.spec_extractor import assess_completeness, empty_draft, extract_from_message
from app.main import app


def test_vague_startup_not_ready():
    draft = empty_draft()
    draft = extract_from_message(draft, "create my startup", "create my startup")
    pct, missing, ready = assess_completeness(draft, "create my startup")
    assert ready is False


def test_healthcare_intent_increases_completeness():
    msg = (
        "HealthTrack helps chronic condition tracking — need brand and landing page, "
        "trustworthy modern healthcare. Tagline: Your health, tracked. References: apple.com, stripe.com"
    )
    draft = empty_draft()
    draft = extract_from_message(draft, msg, msg)
    pct, missing, ready = assess_completeness(draft, msg)
    assert pct >= 85
    assert ready is True
    assert draft["deliverables"]
    assert draft["workflow_summary"]


def test_package_defaults_unlock_ready_when_out_of_scope_empty():
    """Gemini often fills deliverables but leaves out_of_scope empty — defaults must unlock quote."""
    from app.ai.spec_extractor import apply_package_defaults

    draft = empty_draft()
    draft["outcome_statement"] = (
        "Launch-ready brand identity and responsive landing page for HealthTrack."
    )
    draft["deliverables"] = [{"name": "Logo", "format": "SVG + PNG", "required": True}]
    draft["acceptance_criteria"] = []
    draft["in_scope"] = []
    draft["out_of_scope"] = []
    draft["client_inputs_required"] = ["company_name", "landing_page_copy"]
    draft["workflow_summary"] = ""

    filled = apply_package_defaults(draft)
    assert filled["out_of_scope"]
    assert filled["workflow_summary"]
    pct, missing, ready = assess_completeness(
        filled,
        "HealthTrack brand and landing page for our startup",
    )
    assert missing == []
    assert ready is True
    assert pct >= 85


def test_client_inputs_satisfied_without_tagline_keyword():
    draft = empty_draft()
    draft["outcome_statement"] = "Brand and landing page for Acme, a fintech startup."
    draft["deliverables"] = [{"name": "Logo", "format": "SVG", "required": True}]
    draft["acceptance_criteria"] = [{"criterion": "Looks good", "check_type": "ai_judged"}]
    draft["in_scope"] = ["Brand"]
    draft["out_of_scope"] = ["CMS"]
    draft["client_inputs_required"] = ["company_name", "landing_page_copy"]
    draft["workflow_summary"] = "Brand → Logo → Landing"
    pct, missing, ready = assess_completeness(draft, "brand and landing for our fintech startup")
    assert "client_inputs" not in missing
    assert ready is True


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
async def test_scope_chat_flow_to_finalize(api_client: AsyncClient):
    start = await api_client.post("/api/v1/chat/sessions")
    assert start.status_code == 201
    session = start.json()
    sid = session["id"]
    assert session["completeness_pct"] == 0

    vague = await api_client.post(
        f"/api/v1/chat/sessions/{sid}/messages",
        json={"body": "create my startup"},
    )
    assert vague.status_code == 200
    assert vague.json()["ready_for_quote"] is False

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
    body = detailed.json()
    assert body["completeness_pct"] >= 85
    assert body["ready_for_quote"] is True
    assert len(body["spec_draft"]["deliverables"]) >= 1
    draft = body["spec_draft"]

    fin = await api_client.post(f"/api/v1/chat/sessions/{sid}/finalize")
    assert fin.status_code == 200
    fin_body = fin.json()
    assert "intent_id" in fin_body
    assert "quote_id" in fin_body

    quote = await api_client.get(f"/api/v1/quotes/{fin_body['quote_id']}")
    assert quote.status_code == 200
    spec_resp = await api_client.get(f"/api/v1/specs/{quote.json()['spec_id']}")
    assert spec_resp.status_code == 200
    spec = spec_resp.json()
    assert spec["outcome_statement"] == draft["outcome_statement"]
    assert spec["deliverables"] == draft["deliverables"]
    assert spec["in_scope"] == draft["in_scope"]
    assert spec["out_of_scope"] == draft["out_of_scope"]
    assert spec["client_inputs_required"] == draft["client_inputs_required"]
    assert spec["mapped_task_types"] == draft["mapped_task_types"]
    assert spec["workflow_summary"] == (draft.get("workflow_summary") or "")

    fin2 = await api_client.post(f"/api/v1/chat/sessions/{sid}/finalize")
    assert fin2.status_code == 400
