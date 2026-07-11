"""AI gateway — fixture fallback + graceful degradation (no key required)."""

from app.ai.gateway import compile_spec_turn
from app.ai.spec_extractor import empty_draft
from app.config import settings


def test_gateway_uses_fixture_without_key(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", None)
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


def test_gateway_degrades_when_gemini_call_fails(monkeypatch):
    # A key is set but the SDK is unavailable / the call fails → fixture fallback
    # with the error recorded, never a crash.
    monkeypatch.setattr(settings, "gemini_api_key", "invalid-test-key")
    turn = compile_spec_turn(
        draft=empty_draft(),
        user_message="brand and landing page",
        history=[],
    )
    assert turn.source == "fixture"
    assert turn.error is not None
    assert turn.error.startswith("gemini_fallback:")
