"""QA Judge — deterministic checks + gateway fixture path."""

from types import SimpleNamespace

import pytest

from app.ai.gateway import GeminiNotConfiguredError, generate_qa_proposal
from app.ai.qa_judge import (
    build_fixture_review,
    deterministic_failed,
    run_deterministic_checks,
)
from app.config import settings


def test_files_include_format_pass():
    evidence = run_deterministic_checks(
        acceptance_criteria=[
            {
                "criterion": "Logo delivered in SVG and PNG",
                "check_type": "deterministic",
                "rule": "files_include_format(['svg','png'])",
            }
        ],
        notes="Logo pack",
        asset_urls=[
            "https://files.example/logo.svg",
            "https://files.example/logo.png",
        ],
    )
    assert evidence[0]["passed"] is True
    assert not deterministic_failed(evidence)


def test_files_include_format_fail():
    evidence = run_deterministic_checks(
        acceptance_criteria=[
            {
                "criterion": "Logo delivered in SVG and PNG",
                "check_type": "deterministic",
                "rule": "files_include_format(['svg','png'])",
            },
            {
                "criterion": "Matches brand",
                "check_type": "ai_judged",
                "rubric": "Consistent with mood board",
            },
        ],
        notes="Only PDF",
        asset_urls=["https://files.example/out.pdf"],
    )
    assert evidence[0]["passed"] is False
    assert evidence[1]["passed"] is None
    assert deterministic_failed(evidence)

    review = build_fixture_review(
        evidence=evidence,
        notes="Only PDF",
        asset_urls=["https://files.example/out.pdf"],
    )
    assert review["result"] == "fail"
    assert any(not e["passed"] for e in review["evidence"])


def test_fixture_soft_passes_human_required(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "require_gemini", False)
    monkeypatch.setattr(settings, "app_env", "development")

    task = SimpleNamespace(
        title="Brand direction",
        description="Mood board",
        task_type_slug="brand_identity",
        acceptance_criteria=[
            {
                "criterion": "Mood board + palette + type approved",
                "check_type": "human_required",
            }
        ],
    )
    proposal = generate_qa_proposal(
        task=task,
        notes="Brand direction v1",
        asset_urls=["https://files.example/mood.pdf"],
    )
    assert proposal.source == "fixture"
    assert proposal.result == "pass"
    assert proposal.score >= 0.8
    assert proposal.evidence


def test_gateway_qa_fails_on_missing_formats(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "require_gemini", False)
    monkeypatch.setattr(settings, "app_env", "development")

    task = SimpleNamespace(
        title="Logo design",
        description="SVG + PNG",
        task_type_slug="logo_design",
        acceptance_criteria=[
            {
                "criterion": "Logo delivered in SVG and PNG",
                "check_type": "deterministic",
                "rule": "files_include_format(['svg','png'])",
            }
        ],
    )
    proposal = generate_qa_proposal(
        task=task,
        notes="Wrong formats",
        asset_urls=["https://files.example/out.pdf"],
    )
    assert proposal.result == "fail"
    assert proposal.source == "fixture"


def test_gateway_qa_requires_gemini_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "require_gemini", True)
    monkeypatch.setattr(settings, "app_env", "development")

    task = SimpleNamespace(
        title="Brand",
        description="",
        task_type_slug="brand_identity",
        acceptance_criteria=[
            {"criterion": "Looks good", "check_type": "ai_judged", "rubric": "On brief"}
        ],
    )
    with pytest.raises(GeminiNotConfiguredError):
        generate_qa_proposal(task=task, notes="x", asset_urls=["https://files.example/a.pdf"])


def test_url_reachable_requires_http_asset():
    evidence = run_deterministic_checks(
        acceptance_criteria=[
            {
                "criterion": "URL reachable (200)",
                "check_type": "deterministic",
                "rule": "url_reachable",
            }
        ],
        notes="",
        asset_urls=["notes://local"],
    )
    assert evidence[0]["passed"] is False
