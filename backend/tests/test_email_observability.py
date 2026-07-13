"""Email no-op path + AI quality summary."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.email import EmailService


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


@pytest.mark.asyncio
async def test_email_noop_without_key(monkeypatch):
    monkeypatch.setattr("app.services.email.settings.resend_api_key", None)
    svc = EmailService()
    assert svc.enabled is False
    result = await svc.send_invite(to="worker@example.com", task_title="Logo")
    assert result["ok"] is True
    assert result["stub"] is True


@pytest.mark.asyncio
async def test_admin_ai_quality(api_client: AsyncClient):
    res = await api_client.get("/api/v1/admin/ai-quality")
    assert res.status_code == 200
    body = res.json()
    assert "count" in body
    assert "avg_confidence" in body
    assert "escalate_count" in body
