"""Worker stats update on QA + media upload URL stub."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app
from app.models.identity import DEMO_WORKER_ID
from app.models.platform import WorkerStatsRecord
from app.services.worker_stats import WorkerStatsService


@pytest.fixture
async def api_client():
    from app.db.base import Base
    from app.db.seed import seed_catalog, seed_demo_client, seed_demo_worker
    from app.db.session import AsyncSessionLocal, engine

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSessionLocal() as session:
            await seed_catalog(session)
            await seed_demo_client(session)
            await seed_demo_worker(session)
    except Exception as e:
        pytest.skip(f"Database unavailable: {e}")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def db_session():
    from app.db.base import Base
    from app.db.seed import seed_demo_client, seed_demo_worker
    from app.db.session import AsyncSessionLocal, engine

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSessionLocal() as session:
            await seed_demo_client(session)
            await seed_demo_worker(session)
    except Exception as e:
        pytest.skip(f"Database unavailable: {e}")

    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.mark.asyncio
async def test_worker_stats_qa_pass_fail(db_session):
    svc = WorkerStatsService(db_session)
    await svc.record_qa(
        worker_id=DEMO_WORKER_ID,
        task_type_slug="logo_design",
        passed=True,
        confidence=0.9,
    )
    await svc.record_qa(
        worker_id=DEMO_WORKER_ID,
        task_type_slug="logo_design",
        passed=False,
        confidence=0.4,
    )
    await db_session.commit()

    row = await db_session.scalar(
        select(WorkerStatsRecord).where(
            WorkerStatsRecord.worker_id == DEMO_WORKER_ID,
            WorkerStatsRecord.task_type_slug == "logo_design",
        )
    )
    assert row is not None
    assert row.completed == 1
    assert row.reworked == 1
    assert row.avg_qa_confidence is not None


@pytest.mark.asyncio
async def test_media_upload_url_stub(api_client: AsyncClient):
    res = await api_client.post(
        "/api/v1/media/upload-url",
        json={"filename": "logo.svg", "content_type": "image/svg+xml"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "upload_url" in body
    assert "asset_url" in body
    assert "example.invalid" in body["upload_url"] or body["upload_url"].startswith("http")
