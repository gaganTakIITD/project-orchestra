"""RAG project_templates insert + keyword retrieve."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.models.commerce import Intent, OutcomeSpecRecord
from app.models.fulfillment import OutcomeOrder
from app.models.identity import DEMO_CLIENT_ID
from app.models.platform import ProjectTemplateRecord
from app.orchestrator.states import OrderStatus
from app.services.rag import RagService, keyword_overlap_score


@pytest.fixture
async def db_session():
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

    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.mark.asyncio
async def test_rag_insert_and_retrieve(db_session):
    intent = Intent(
        client_id=DEMO_CLIENT_ID,
        raw_text="brand logo landing page cafe",
        attachments=[],
        status="compiled",
    )
    db_session.add(intent)
    await db_session.flush()

    spec = OutcomeSpecRecord(
        intent_id=intent.id,
        outcome_statement="Launch-ready brand identity and responsive landing page for a cafe.",
        deliverables=[{"name": "Logo"}],
        acceptance_criteria=[],
        in_scope=["logo", "landing page"],
        out_of_scope=[],
        assumptions=[],
        client_inputs_required=[],
        mapped_task_types=["logo_design", "landing_page_frontend"],
        workflow_summary="Brand → Logo → Landing page for cafe",
    )
    db_session.add(spec)
    await db_session.flush()

    order = OutcomeOrder(
        id=uuid.uuid4(),
        client_id=DEMO_CLIENT_ID,
        spec_id=spec.id,
        status=OrderStatus.CLOSED,
        price=10000,
    )
    db_session.add(order)
    await db_session.flush()

    svc = RagService(db_session)
    row = await svc.ingest_from_order(order)
    assert row is not None
    await db_session.commit()

    stored = (
        await db_session.execute(select(ProjectTemplateRecord))
    ).scalars().all()
    assert len(stored) == 1

    hits = await svc.retrieve(query="cafe logo landing brand", limit=3)
    assert len(hits) >= 1
    assert hits[0]["score"] > 0
    assert keyword_overlap_score("cafe logo", "cafe logo landing") > 0
