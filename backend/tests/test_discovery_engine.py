"""Discovery Engine knowledge service — config + parse helpers (no live GCP calls)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.discovery_engine import (
    DiscoveryEngineKnowledgeService,
    DiscoveryEngineNotConfiguredError,
    KnowledgeAnswer,
)


def test_not_configured_raises(monkeypatch):
    monkeypatch.setattr("app.services.discovery_engine.settings.project_id", None)
    monkeypatch.setattr("app.services.discovery_engine.settings.data_store_id", None)
    monkeypatch.setattr("app.services.discovery_engine.settings.engine_id", None)
    svc = DiscoveryEngineKnowledgeService()
    assert svc.enabled is False
    with pytest.raises(DiscoveryEngineNotConfiguredError):
        svc.query_knowledge_base("hello")


def test_serving_config_prefers_engine(monkeypatch):
    svc = DiscoveryEngineKnowledgeService(
        project_id="proj-1",
        location="global",
        data_store_id="ds-1",
        engine_id="eng-1",
    )
    assert "engines/eng-1" in svc._serving_config()
    assert "dataStores" not in svc._serving_config()


def test_serving_config_data_store(monkeypatch):
    svc = DiscoveryEngineKnowledgeService(
        project_id="proj-1",
        location="us",
        data_store_id="ds-abc",
        engine_id=None,
    )
    path = svc._serving_config()
    assert "dataStores/ds-abc" in path
    assert "locations/us" in path


def test_parse_answer_with_citations():
    svc = DiscoveryEngineKnowledgeService(
        project_id="p", location="global", data_store_id="d"
    )
    answer = SimpleNamespace(
        answer_text="Revisions are included twice.",
        citations=[],
        references=[
            SimpleNamespace(
                chunk_info=SimpleNamespace(
                    content="Two revision rounds are included.",
                    document_metadata=SimpleNamespace(title="Policy"),
                    document=None,
                ),
                document=SimpleNamespace(
                    id="doc-1",
                    title="Revision Policy",
                    derived_struct_data={"link": "https://example.com/policy"},
                ),
                content=None,
            )
        ],
    )
    response = SimpleNamespace(answer=answer, session="sessions/abc", search_results=[])
    result = svc._parse_answer_response(response)
    assert isinstance(result, KnowledgeAnswer)
    assert "Revisions" in result.answer
    assert result.citations
    assert result.citations[0].uri == "https://example.com/policy"


def test_empty_query_raises():
    svc = DiscoveryEngineKnowledgeService(
        project_id="p", location="global", data_store_id="d"
    )
    with pytest.raises(ValueError):
        svc.query_knowledge_base("   ")
