"""Knowledge base — Vertex AI Agent Builder (Discovery Engine) grounded Q&A."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.models.identity import User
from app.schemas.knowledge import KnowledgeAnswerOut, KnowledgeCitationOut, KnowledgeQueryIn
from app.services.auth import get_current_client
from app.services.discovery_engine import (
    DiscoveryEngineKnowledgeService,
    DiscoveryEngineNotConfiguredError,
    KnowledgeAnswer,
    query_knowledge_base,
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def _to_out(result: KnowledgeAnswer) -> KnowledgeAnswerOut:
    return KnowledgeAnswerOut(
        answer=result.answer,
        citations=[
            KnowledgeCitationOut(
                title=c.title,
                uri=c.uri,
                snippet=c.snippet,
                document_id=c.document_id,
            )
            for c in result.citations
        ],
        session_id=result.session_id,
        raw=None,
    )


@router.post("/query", response_model=KnowledgeAnswerOut)
async def query_knowledge(
    body: KnowledgeQueryIn,
    _client: User = Depends(get_current_client),
) -> KnowledgeAnswerOut:
    """Grounded RAG against the configured Discovery Engine data store / search app.

    Uses ``google-cloud-discoveryengine`` only (Agent Builder credits — not Gemini SDK).
    """
    try:
        result = await asyncio.to_thread(query_knowledge_base, body.query)
    except DiscoveryEngineNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001 — surface provider errors cleanly
        raise HTTPException(
            status_code=502,
            detail=f"Discovery Engine query failed: {e}",
        ) from e
    return _to_out(result)


class KnowledgeStatusOut(BaseModel):
    enabled: bool
    project_id: str | None = None
    location: str | None = None
    data_store_id: str | None = None
    engine_id: str | None = None
    serving_config_preview: str | None = None


@router.get("/status", response_model=KnowledgeStatusOut)
async def knowledge_status(
    _client: User = Depends(get_current_client),
) -> KnowledgeStatusOut:
    """Whether Discovery Engine RAG is configured (does not call Google)."""
    svc = DiscoveryEngineKnowledgeService()
    preview: str | None = None
    if svc.enabled:
        try:
            preview = svc._serving_config()
        except DiscoveryEngineNotConfiguredError:
            preview = None
    return KnowledgeStatusOut(
        enabled=svc.enabled,
        project_id=svc.project_id,
        location=svc.location,
        data_store_id=svc.data_store_id,
        engine_id=svc.engine_id,
        serving_config_preview=preview,
    )
