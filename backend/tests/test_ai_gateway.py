"""AI gateway — fixture fallback + prod gate (no silent fixture when required)."""

import pytest

from app.ai.gateway import (
    GeminiNotConfiguredError,
    compile_spec_turn,
    generate_task_packet_proposal,
)
from app.ai.spec_extractor import empty_draft
from app.config import settings


def test_gateway_uses_fixture_without_key(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "require_gemini", False)
    monkeypatch.setattr(settings, "app_env", "development")
    turn = compile_spec_turn(
        draft=empty_draft(),
        user_message="Need brand and landing page for my startup",
        history=[],
    )
    assert turn.source == "fixture"
    # Fixture leaves reply to the deterministic builder in ChatService.
    assert turn.reply is None
    assert turn.draft["version"] == 1
    assert turn.error is None


def test_gateway_fixture_extracts_deliverables(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "require_gemini", False)
    monkeypatch.setattr(settings, "app_env", "development")
    turn = compile_spec_turn(
        draft=empty_draft(),
        user_message=(
            "HealthTrack — brand identity and landing page, trustworthy healthcare tone. "
            "Tagline: Your health, tracked. References: apple.com"
        ),
        history=[],
    )
    assert turn.draft["deliverables"]
    assert turn.draft["mapped_task_types"]


def test_draft_from_gemini_merges_previous_and_defaults():
    from app.ai.gateway import GeminiSpec, _draft_from_gemini

    previous = empty_draft()
    previous["outcome_statement"] = "Launch-ready brand for HealthTrack chronic care."
    previous["deliverables"] = [{"name": "Logo", "format": "SVG + PNG", "required": True}]
    previous["out_of_scope"] = ["CMS", "SEO"]
    previous["version"] = 2

    # Gemini omits out_of_scope and leaves acceptance empty — merge + defaults.
    spec = GeminiSpec(
        outcome_statement="Launch-ready brand for HealthTrack chronic care.",
        deliverables=[{"name": "Logo", "format": "SVG + PNG", "required": True}],
        in_scope=["Brand identity"],
        assistant_reply="Looking good.",
        confidence=0.8,
    )
    out = _draft_from_gemini(spec, previous=previous)
    assert out["out_of_scope"] == ["CMS", "SEO"]  # preserved from previous
    assert out["acceptance_criteria"]  # package defaults
    assert out["version"] == 3


def test_gateway_degrades_when_gemini_call_fails(monkeypatch):
    # A key is set but the SDK is unavailable / the call fails → fixture fallback
    # with the error recorded, never a crash (non-prod only).
    monkeypatch.setattr(settings, "gemini_api_key", "invalid-test-key")
    monkeypatch.setattr(settings, "require_gemini", False)
    monkeypatch.setattr(settings, "app_env", "development")
    turn = compile_spec_turn(
        draft=empty_draft(),
        user_message="brand and landing page",
        history=[],
    )
    assert turn.source == "fixture"
    assert turn.error is not None
    assert turn.error.startswith("gemini_fallback:")


def test_gateway_fails_loud_when_gemini_required_without_key(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "require_gemini", True)
    monkeypatch.setattr(settings, "app_env", "development")
    with pytest.raises(GeminiNotConfiguredError):
        compile_spec_turn(
            draft=empty_draft(),
            user_message="Need a logo",
            history=[],
        )


def test_ensure_gemini_configured_in_production(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "require_gemini", False)
    monkeypatch.setattr(settings, "app_env", "production")
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        settings.ensure_gemini_configured()


def test_task_packet_proposal_fixture_path(monkeypatch):
    import uuid

    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "require_gemini", False)
    monkeypatch.setattr(settings, "app_env", "development")

    class _FakeTask:
        def __init__(self):
            self.id = uuid.uuid4()
            self.title = "Logo design"
            self.description = "Design the logo in SVG + PNG."
            self.task_type_slug = "logo_design"
            self.acceptance_criteria = [
                {
                    "criterion": "Logo delivered in SVG and PNG",
                    "check_type": "deterministic",
                }
            ]
            self.deadline = None

    task = _FakeTask()
    proposal = generate_task_packet_proposal(
        order_id=uuid.uuid4(),
        task=task,
        spec={
            "outcome_statement": "Launch-ready brand for HealthTrack.",
            "deliverables": [{"name": "Logo", "format": "SVG + PNG", "required": True}],
            "out_of_scope": [],
            "client_inputs_required": ["company_name"],
        },
        order_price_share=2000,
        order_deadline=None,
        revision_limit=2,
        dependency_titles=[],
    )
    assert proposal.source == "fixture"
    assert proposal.packet["checklist"]
    assert proposal.charter["task_id"] == task.id


def test_task_packet_fails_loud_when_gemini_required(monkeypatch):
    import uuid

    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "require_gemini", True)

    class _FakeTask:
        id = uuid.uuid4()
        title = "Logo"
        description = "x"
        task_type_slug = "logo_design"
        acceptance_criteria = []
        deadline = None

    with pytest.raises(GeminiNotConfiguredError):
        generate_task_packet_proposal(
            order_id=uuid.uuid4(),
            task=_FakeTask(),
            spec={"outcome_statement": "Brand", "deliverables": []},
            order_price_share=100,
            order_deadline=None,
            revision_limit=1,
        )
