"""RAG project templates — ingest on OutcomeClosed; keyword retrieve for Spec Compiler."""

from __future__ import annotations

import re
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commerce import OutcomeSpecRecord
from app.models.fulfillment import OutcomeOrder
from app.models.platform import ProjectTemplateRecord
from app.orchestrator.events import EventWriter
from app.orchestrator.states import ActorType


_TOKEN = re.compile(r"[a-z0-9]{3,}")


def _tokens(text: str) -> set[str]:
    return set(_TOKEN.findall((text or "").lower()))


def keyword_overlap_score(query: str, summary: str, spec: dict | None = None) -> float:
    q = _tokens(query)
    if not q:
        return 0.0
    blob = summary or ""
    if isinstance(spec, dict):
        blob += " " + str(spec.get("outcome_statement") or "")
        blob += " " + " ".join(str(x) for x in (spec.get("in_scope") or []))
        blob += " " + " ".join(str(x) for x in (spec.get("mapped_task_types") or []))
    t = _tokens(blob)
    if not t:
        return 0.0
    return len(q & t) / len(q)


class RagService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.events = EventWriter(session)

    async def ingest_from_order(self, order: OutcomeOrder) -> ProjectTemplateRecord | None:
        if order.spec_id is None:
            return None
        spec = await self.session.get(OutcomeSpecRecord, order.spec_id)
        if spec is None:
            return None

        spec_json: dict[str, Any] = {
            "outcome_statement": spec.outcome_statement,
            "deliverables": spec.deliverables,
            "acceptance_criteria": spec.acceptance_criteria,
            "in_scope": spec.in_scope,
            "out_of_scope": spec.out_of_scope,
            "mapped_task_types": spec.mapped_task_types,
            "workflow_summary": getattr(spec, "workflow_summary", None),
            "risk_tier": getattr(spec, "risk_tier", None),
        }
        plan_summary = (
            getattr(spec, "workflow_summary", None)
            or spec.outcome_statement
            or "Closed outcome"
        )
        row = ProjectTemplateRecord(
            sku_id=order.sku_id or spec.sku_id,
            order_id=order.id,
            name=(spec.outcome_statement or "Outcome")[:255],
            plan_summary=plan_summary,
            spec_json=spec_json,
            success_count=1,
            embedding=None,
        )
        self.session.add(row)
        await self.session.flush()

        await self.events.emit(
            aggregate_type="order",
            aggregate_id=order.id,
            event_type="ProjectTemplateIngested",
            actor_type=ActorType.SYSTEM,
            payload={"template_id": str(row.id)},
        )
        await self.session.flush()
        return row

    async def retrieve(
        self,
        *,
        query: str,
        limit: int = 3,
        sku_id: uuid.UUID | None = None,
    ) -> list[dict[str, Any]]:
        stmt = select(ProjectTemplateRecord).order_by(ProjectTemplateRecord.created_at.desc())
        if sku_id is not None:
            stmt = stmt.where(ProjectTemplateRecord.sku_id == sku_id)
        rows = list((await self.session.execute(stmt.limit(50))).scalars().all())
        if not rows:
            return []

        scored: list[tuple[float, ProjectTemplateRecord]] = []
        for row in rows:
            score = keyword_overlap_score(query, row.plan_summary or "", row.spec_json)
            if score > 0:
                scored.append((score, row))
        scored.sort(key=lambda x: -x[0])
        out: list[dict[str, Any]] = []
        for score, row in scored[:limit]:
            out.append(
                {
                    "id": str(row.id),
                    "name": row.name,
                    "plan_summary": row.plan_summary,
                    "score": round(score, 4),
                    "spec_json": row.spec_json,
                }
            )
        return out
