"""Auth mode demo still resolves seeded users without Bearer.

Also scaffolds a Clerk JWT path with a mock JWKS signing key (Phase 4 prep —
founder still must set real Clerk keys + AUTH_MODE=clerk on Cloud Run).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app
from app.services import auth as auth_service


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
async def test_auth_me_demo_client(api_client: AsyncClient):
    res = await api_client.get("/api/v1/auth/me")
    assert res.status_code == 200
    assert res.json()["role"] == "client"


@pytest.mark.asyncio
async def test_auth_me_demo_worker_header(api_client: AsyncClient):
    res = await api_client.get(
        "/api/v1/auth/me",
        headers={"X-Orchestra-Role": "worker"},
    )
    assert res.status_code == 200
    assert res.json()["role"] == "worker"
    assert "Rohan" in res.json()["full_name"]


@pytest.mark.asyncio
async def test_clerk_jwt_with_mock_jwks(api_client: AsyncClient, monkeypatch):
    """Phase 4 prep: verify AUTH_MODE=clerk accepts a Bearer JWT via mock JWKS."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    issuer = "https://example.clerk.accounts.dev"
    monkeypatch.setattr(settings, "auth_mode", "clerk")
    monkeypatch.setattr(settings, "clerk_jwks_url", f"{issuer}/.well-known/jwks.json")
    monkeypatch.setattr(settings, "clerk_issuer", issuer)
    monkeypatch.setattr(settings, "clerk_audience", None)
    auth_service._jwks_clients.clear()

    fake_client = MagicMock()
    fake_signing_key = MagicMock()
    fake_signing_key.key = public_pem
    fake_client.get_signing_key_from_jwt.return_value = fake_signing_key
    monkeypatch.setattr(auth_service, "_jwks_client", lambda: fake_client)

    token = jwt.encode(
        {
            "sub": "user_clerk_test_sub_1",
            "email": "clerk.tester@example.com",
            "name": "Clerk Tester",
            "iss": issuer,
        },
        private_key,
        algorithm="RS256",
    )

    res = await api_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["email"] == "clerk.tester@example.com"
    assert body["full_name"] == "Clerk Tester"
    assert body["role"] == "client"


@pytest.mark.asyncio
async def test_choose_worker_role(api_client: AsyncClient):
    res = await api_client.patch("/api/v1/auth/role", json={"role": "worker"})
    assert res.status_code == 200
    assert res.json()["role"] == "worker"
    prof = await api_client.get(
        "/api/v1/workers/profile",
        headers={"X-Orchestra-Role": "worker"},
    )
    assert prof.status_code == 200


@pytest.mark.asyncio
async def test_clerk_mode_requires_bearer(api_client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "auth_mode", "clerk")
    monkeypatch.setattr(settings, "clerk_jwks_url", "https://example.clerk.accounts.dev/.well-known/jwks.json")
    res = await api_client.get("/api/v1/auth/me")
    assert res.status_code == 401
