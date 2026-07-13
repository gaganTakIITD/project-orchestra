"""Knowledge-base (Vertex AI Agent Builder / Discovery Engine) response shapes."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class KnowledgeQueryIn(BaseModel):
    query: str = Field(min_length=1, max_length=4000)


class KnowledgeCitationOut(BaseModel):
    title: str
    uri: str | None = None
    snippet: str | None = None
    document_id: str | None = None


class KnowledgeAnswerOut(BaseModel):
    answer: str
    citations: list[KnowledgeCitationOut] = Field(default_factory=list)
    session_id: str | None = None
    # Optional debug payload — omit from public UIs if undesired
    raw: dict[str, Any] | None = None
