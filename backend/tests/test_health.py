import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"


@pytest.mark.asyncio
async def test_health_503_when_gemini_required_without_key(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "require_gemini", True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/health")
    assert res.status_code == 503
    assert "GEMINI_API_KEY" in res.json()["detail"]
