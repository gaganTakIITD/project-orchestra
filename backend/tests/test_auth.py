"""Auth mode demo still resolves seeded users without Bearer.

Clerk JWT path uses a mock JWKS signing key (AUTH_MODE=clerk is live in prod;
these tests exercise RBAC + admin elevation without hitting real Clerk).
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


def _setup_clerk_mode(monkeypatch):
    """Switch settings to Clerk mode with a mock JWKS signing key. Returns
    (private_key, issuer) for minting test tokens."""
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
    monkeypatch.setattr(settings, "admin_email_allowlist", "")
    auth_service._jwks_clients.clear()

    fake_client = MagicMock()
    fake_signing_key = MagicMock()
    fake_signing_key.key = public_pem
    fake_client.get_signing_key_from_jwt.return_value = fake_signing_key
    monkeypatch.setattr(auth_service, "_jwks_client", lambda: fake_client)
    return private_key, issuer


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


@pytest.mark.asyncio
async def test_worker_route_requires_worker_role_clerk(api_client: AsyncClient, monkeypatch):
    """RBAC: a fresh Clerk account defaults to client → worker APIs return 403."""
    private_key, issuer = _setup_clerk_mode(monkeypatch)
    token = jwt.encode(
        {"sub": "user_plain_client", "email": "buyer@example.com", "iss": issuer},
        private_key,
        algorithm="RS256",
    )
    denied = await api_client.get(
        "/api/v1/workers/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_auth_me_reflects_admin_role_clerk(api_client: AsyncClient, monkeypatch):
    """/auth/me is the single source of truth: an admin claim surfaces role=admin."""
    private_key, issuer = _setup_clerk_mode(monkeypatch)
    token = jwt.encode(
        {
            "sub": "user_admin_me",
            "email": "boss@example.com",
            "iss": issuer,
            "public_metadata": {"role": "admin"},
        },
        private_key,
        algorithm="RS256",
    )
    res = await api_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_worker_role_cannot_hit_client_route_clerk(
    api_client: AsyncClient, monkeypatch
):
    """RBAC: active role=worker → client routes (e.g. POST /intents) return 403."""
    private_key, issuer = _setup_clerk_mode(monkeypatch)
    token = jwt.encode(
        {
            "sub": "user_worker_blocks_client",
            "email": "seller@example.com",
            "iss": issuer,
        },
        private_key,
        algorithm="RS256",
    )
    headers = {"Authorization": f"Bearer {token}"}

    me = await api_client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["role"] == "client"

    switched = await api_client.patch(
        "/api/v1/auth/role",
        json={"role": "worker"},
        headers=headers,
    )
    assert switched.status_code == 200
    assert switched.json()["role"] == "worker"

    denied = await api_client.post(
        "/api/v1/intents",
        json={"raw_text": "Need a logo for my cafe within two weeks please"},
        headers=headers,
    )
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_admin_claim_persists_across_auth_me_calls(
    api_client: AsyncClient, monkeypatch
):
    """Admin elevation from Clerk claims is committed; survives a follow-up /auth/me
    even when the second token no longer carries the admin claim (no auto-demote)."""
    private_key, issuer = _setup_clerk_mode(monkeypatch)
    sub = "user_admin_persist"
    admin_token = jwt.encode(
        {
            "sub": sub,
            "email": "persist.admin@example.com",
            "iss": issuer,
            "public_metadata": {"role": "admin"},
        },
        private_key,
        algorithm="RS256",
    )
    first = await api_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert first.status_code == 200
    assert first.json()["role"] == "admin"
    user_id = first.json()["id"]

    plain_token = jwt.encode(
        {
            "sub": sub,
            "email": "persist.admin@example.com",
            "iss": issuer,
            "public_metadata": {"role": "client"},
        },
        private_key,
        algorithm="RS256",
    )
    second = await api_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {plain_token}"},
    )
    assert second.status_code == 200
    assert second.json()["id"] == user_id
    assert second.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_patch_auth_role_rejected_for_admin(
    api_client: AsyncClient, monkeypatch
):
    """Admin is IdP-owned — PATCH /auth/role must not demote or reassign it."""
    private_key, issuer = _setup_clerk_mode(monkeypatch)
    token = jwt.encode(
        {
            "sub": "user_admin_no_patch",
            "email": "locked.admin@example.com",
            "iss": issuer,
            "public_metadata": {"role": "admin"},
        },
        private_key,
        algorithm="RS256",
    )
    headers = {"Authorization": f"Bearer {token}"}

    me = await api_client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["role"] == "admin"

    rejected = await api_client.patch(
        "/api/v1/auth/role",
        json={"role": "worker"},
        headers=headers,
    )
    assert rejected.status_code == 403
