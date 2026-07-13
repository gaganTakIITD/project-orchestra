"""Admin read-only API tests — orders list, events timeline, AI decisions."""

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


async def _create_order(api_client: AsyncClient) -> str:
    create = await api_client.post(
        "/api/v1/intents",
        json={"raw_text": "Need a logo and brand kit for my cafe within two weeks please"},
    )
    assert create.status_code in (200, 201)
    accept = await api_client.post(f"/api/v1/quotes/{create.json()['quote_id']}/accept")
    assert accept.status_code in (200, 201)
    return accept.json()["order_id"]


@pytest.mark.asyncio
async def test_admin_list_orders_demo(api_client: AsyncClient):
    order_id = await _create_order(api_client)

    res = await api_client.get("/api/v1/admin/orders")
    assert res.status_code == 200
    body = res.json()
    assert "orders" in body
    ids = [o["id"] for o in body["orders"]]
    assert order_id in ids
    order = next(o for o in body["orders"] if o["id"] == order_id)
    assert order["status"] in (
        "confirmed",
        "assembling_team",
        "delivery_active",
    )


@pytest.mark.asyncio
async def test_admin_list_orders_status_filter(api_client: AsyncClient):
    order_id = await _create_order(api_client)
    order = (await api_client.get(f"/api/v1/orders/{order_id}")).json()
    status = order["status"]

    matched = await api_client.get(f"/api/v1/admin/orders?status={status}")
    assert matched.status_code == 200
    assert any(o["id"] == order_id for o in matched.json()["orders"])

    empty = await api_client.get("/api/v1/admin/orders?status=cancelled")
    assert empty.status_code == 200
    assert empty.json()["orders"] == []


@pytest.mark.asyncio
async def test_admin_order_events(api_client: AsyncClient):
    order_id = await _create_order(api_client)

    res = await api_client.get(f"/api/v1/admin/orders/{order_id}/events")
    assert res.status_code == 200
    body = res.json()
    assert body["order_id"] == order_id
    assert isinstance(body["events"], list)
    assert len(body["events"]) >= 1
    types = {e["event_type"] for e in body["events"]}
    # Accept quote writes at least one order/task event
    assert any("order" in e["aggregate_type"] or "task" in e["aggregate_type"] for e in body["events"])
    assert types  # non-empty


@pytest.mark.asyncio
async def test_admin_order_events_404(api_client: AsyncClient):
    missing = "00000000-0000-4000-8000-000000009999"
    res = await api_client.get(f"/api/v1/admin/orders/{missing}/events")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_admin_ai_decisions(api_client: AsyncClient):
    await _create_order(api_client)

    res = await api_client.get("/api/v1/admin/ai-decisions?limit=20")
    assert res.status_code == 200
    body = res.json()
    assert "decisions" in body
    assert isinstance(body["decisions"], list)
    # Architect (and possibly matcher) log on plan build
    if body["decisions"]:
        row = body["decisions"][0]
        assert "agent_type" in row
        assert "source" in row
        assert "created_at" in row


@pytest.mark.asyncio
async def test_admin_clerk_requires_admin_role(api_client: AsyncClient, monkeypatch):
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

    # Non-admin token → 403
    client_token = jwt.encode(
        {
            "sub": "user_not_admin",
            "email": "client@example.com",
            "iss": issuer,
            "public_metadata": {"role": "client"},
        },
        private_key,
        algorithm="RS256",
    )
    denied = await api_client.get(
        "/api/v1/admin/orders",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert denied.status_code == 403

    # Admin role → 200
    admin_token = jwt.encode(
        {
            "sub": "user_is_admin",
            "email": "admin@example.com",
            "iss": issuer,
            "public_metadata": {"role": "admin"},
        },
        private_key,
        algorithm="RS256",
    )
    allowed = await api_client.get(
        "/api/v1/admin/orders",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert allowed.status_code == 200

    # Allowlist email → 200
    monkeypatch.setattr(settings, "admin_email_allowlist", "founder@orchestra.local")
    allowlist_token = jwt.encode(
        {
            "sub": "user_founder",
            "email": "founder@orchestra.local",
            "iss": issuer,
            "public_metadata": {"role": "client"},
        },
        private_key,
        algorithm="RS256",
    )
    allowlisted = await api_client.get(
        "/api/v1/admin/orders",
        headers={"Authorization": f"Bearer {allowlist_token}"},
    )
    assert allowlisted.status_code == 200
