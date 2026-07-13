"""Vertex AI Agent Builder (Discovery Engine) knowledge base.

Bills against Agent Builder / Search product credits — **not** Gemini API Studio
or Vertex AI prediction SDKs. Do not import ``google.generativeai`` /
``google.cloud.aiplatform`` here.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class KnowledgeCitation:
    """One grounded source chunk returned by Discovery Engine."""

    title: str
    uri: str | None = None
    snippet: str | None = None
    document_id: str | None = None


@dataclass(frozen=True)
class KnowledgeAnswer:
    """Grounded answer + citations from ``answer_query`` (or search fallback)."""

    answer: str
    citations: list[KnowledgeCitation] = field(default_factory=list)
    session_id: str | None = None
    raw: dict[str, Any] | None = None


class DiscoveryEngineNotConfiguredError(RuntimeError):
    """Raised when PROJECT_ID / DATA_STORE_ID (or ENGINE_ID) are missing."""


class DiscoveryEngineKnowledgeService:
    """Thin wrapper around ``google.cloud.discoveryengine`` conversational search."""

    def __init__(
        self,
        *,
        project_id: str | None = None,
        location: str | None = None,
        data_store_id: str | None = None,
        engine_id: str | None = None,
    ) -> None:
        self.project_id = project_id if project_id is not None else settings.project_id
        self.location = (location if location is not None else settings.location) or "global"
        self.data_store_id = (
            data_store_id if data_store_id is not None else settings.data_store_id
        )
        self.engine_id = engine_id if engine_id is not None else settings.engine_id
        self._client: Any | None = None

    @property
    def enabled(self) -> bool:
        return bool(self.project_id and (self.engine_id or self.data_store_id))

    def _require_config(self) -> None:
        if not self.project_id:
            raise DiscoveryEngineNotConfiguredError(
                "PROJECT_ID is required for Discovery Engine RAG"
            )
        if not self.engine_id and not self.data_store_id:
            raise DiscoveryEngineNotConfiguredError(
                "DATA_STORE_ID or ENGINE_ID is required for Discovery Engine RAG"
            )

    def _serving_config(self) -> str:
        """Full servingConfig resource name.

        Prefer ``ENGINE_ID`` (Search app) for ``answer_query``. Fall back to the
        data-store serving config when only ``DATA_STORE_ID`` is set.
        """
        self._require_config()
        base = (
            f"projects/{self.project_id}/locations/{self.location}"
            f"/collections/default_collection"
        )
        if self.engine_id:
            return f"{base}/engines/{self.engine_id}/servingConfigs/default_serving_config"
        return (
            f"{base}/dataStores/{self.data_store_id}/servingConfigs/default_serving_config"
        )

    def _client_options(self) -> Any | None:
        from google.api_core.client_options import ClientOptions

        if self.location and self.location != "global":
            return ClientOptions(
                api_endpoint=f"{self.location}-discoveryengine.googleapis.com"
            )
        return None

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        from google.cloud import discoveryengine_v1 as discoveryengine

        self._client = discoveryengine.ConversationalSearchServiceClient(
            client_options=self._client_options()
        )
        return self._client

    def query_knowledge_base(self, user_query: str) -> KnowledgeAnswer:
        """Forward ``user_query`` to the Data Store / Search app; return grounded answer."""
        text = (user_query or "").strip()
        if not text:
            raise ValueError("user_query must be non-empty")

        self._require_config()

        from google.cloud import discoveryengine_v1 as discoveryengine

        client = self._get_client()
        serving_config = self._serving_config()

        answer_generation_spec = discoveryengine.AnswerQueryRequest.AnswerGenerationSpec(
            include_citations=True,
            ignore_adversarial_query=True,
            ignore_non_answer_seeking_query=False,
        )

        request = discoveryengine.AnswerQueryRequest(
            serving_config=serving_config,
            query=discoveryengine.Query(text=text),
            answer_generation_spec=answer_generation_spec,
        )

        logger.info(
            "Discovery Engine answer_query project=%s location=%s serving=%s",
            self.project_id,
            self.location,
            serving_config,
        )
        response = client.answer_query(request)
        return self._parse_answer_response(response)

    def _parse_answer_response(self, response: Any) -> KnowledgeAnswer:
        answer_obj = getattr(response, "answer", None)
        answer_text = ""
        citations: list[KnowledgeCitation] = []

        if answer_obj is not None:
            answer_text = (getattr(answer_obj, "answer_text", None) or "").strip()
            citations = self._extract_citations(answer_obj, response)

        if not answer_text:
            # Some serving configs return only search snippets; surface top snippets.
            answer_text = self._fallback_snippet_answer(response)

        session = getattr(response, "session", None)
        session_id = str(session) if session else None

        return KnowledgeAnswer(
            answer=answer_text,
            citations=citations,
            session_id=session_id,
            raw=_safe_message_dict(response),
        )

    def _extract_citations(
        self, answer_obj: Any, response: Any
    ) -> list[KnowledgeCitation]:
        citations: list[KnowledgeCitation] = []
        # Map citation indices → grounded docs when present on the answer.
        for cite in getattr(answer_obj, "citations", None) or []:
            for src in getattr(cite, "sources", None) or []:
                ref = getattr(src, "reference_id", None) or getattr(src, "id", None)
                title = str(ref) if ref else "source"
                uri = None
                snippet = None
                doc_id = str(ref) if ref else None
                citations.append(
                    KnowledgeCitation(
                        title=title,
                        uri=uri,
                        snippet=snippet,
                        document_id=doc_id,
                    )
                )

        # Prefer richer references when the API returns them.
        for ref in getattr(answer_obj, "references", None) or []:
            chunk = getattr(ref, "chunk_info", None)
            doc = getattr(ref, "document", None)
            if doc is None and chunk is not None:
                doc = getattr(chunk, "document", None)
            title = "Document"
            if doc is not None and getattr(doc, "title", None):
                title = str(doc.title)
            else:
                meta = getattr(chunk, "document_metadata", None) if chunk else None
                if meta is not None and getattr(meta, "title", None):
                    title = str(meta.title)
            uri = None
            derived = getattr(doc, "derived_struct_data", None) if doc is not None else None
            if isinstance(derived, dict):
                link = derived.get("link") or derived.get("uri")
                if link:
                    uri = str(link)
            content = None
            if chunk is not None:
                content = getattr(chunk, "content", None)
            if not content:
                content = getattr(ref, "content", None)
            citations.append(
                KnowledgeCitation(
                    title=title,
                    uri=uri,
                    snippet=str(content)[:500] if content else None,
                    document_id=str(getattr(doc, "id", None) or "") or None,
                )
            )

        # Deduplicate by (title, uri, snippet)
        seen: set[tuple[str | None, str | None, str | None]] = set()
        unique: list[KnowledgeCitation] = []
        for c in citations:
            key = (c.title, c.uri, c.snippet)
            if key in seen:
                continue
            seen.add(key)
            unique.append(c)
        return unique

    def _fallback_snippet_answer(self, response: Any) -> str:
        parts: list[str] = []
        for result in getattr(response, "search_results", None) or []:
            doc = getattr(result, "document", None)
            if doc is None:
                continue
            data = getattr(doc, "derived_struct_data", None) or {}
            if isinstance(data, dict):
                snip = data.get("snippets") or data.get("extractive_answers")
                if isinstance(snip, list) and snip:
                    first = snip[0]
                    if isinstance(first, dict):
                        parts.append(str(first.get("snippet") or first.get("content") or ""))
                    else:
                        parts.append(str(first))
                elif data.get("title"):
                    parts.append(str(data["title"]))
        return "\n\n".join(p for p in parts if p).strip()


def query_knowledge_base(user_query: str) -> KnowledgeAnswer:
    """Module-level helper — forwards to the configured Discovery Engine data store."""
    return DiscoveryEngineKnowledgeService().query_knowledge_base(user_query)


def _safe_message_dict(message: Any) -> dict[str, Any] | None:
    try:
        from google.protobuf.json_format import MessageToDict

        if hasattr(message, "_pb"):
            return MessageToDict(message._pb, preserving_proto_field_name=True)
    except Exception:  # noqa: BLE001 — raw payload is best-effort for debugging
        logger.debug("Could not serialize Discovery Engine response", exc_info=True)
    return None
