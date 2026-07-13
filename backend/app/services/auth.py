"""Auth — demo stubs (default) or Clerk JWT (AUTH_MODE=clerk)."""

from __future__ import annotations

import uuid
from typing import Any

import jwt
from fastapi import Depends, Header, HTTPException, Request
from jwt import PyJWKClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.models.identity import DEMO_CLIENT_ID, DEMO_WORKER_ID, User, WorkerProfileRecord

_jwks_clients: dict[str, PyJWKClient] = {}


async def get_demo_client(session: AsyncSession) -> User:
    user = await session.get(User, DEMO_CLIENT_ID)
    if user is None:
        raise RuntimeError("Demo client not seeded — run with AUTO_SEED=true")
    return user


async def get_demo_worker(session: AsyncSession) -> User:
    user = await session.get(User, DEMO_WORKER_ID)
    if user is None:
        raise RuntimeError("Demo worker not seeded — run with AUTO_SEED=true")
    return user


async def get_demo_worker_profile(session: AsyncSession) -> WorkerProfileRecord:
    profile = await session.get(WorkerProfileRecord, DEMO_WORKER_ID)
    if profile is None:
        raise RuntimeError("Demo worker profile not seeded — run with AUTO_SEED=true")
    return profile


def _bearer_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    return None


def _jwks_client() -> PyJWKClient:
    url = settings.clerk_jwks_url
    if not url:
        raise HTTPException(status_code=503, detail="CLERK_JWKS_URL not configured")
    if url not in _jwks_clients:
        _jwks_clients[url] = PyJWKClient(url, cache_keys=True)
    return _jwks_clients[url]


def _verify_clerk_token(token: str) -> dict[str, Any]:
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        decode_kwargs: dict[str, Any] = {
            "algorithms": ["RS256"],
            "options": {"verify_aud": bool(settings.clerk_audience)},
        }
        if settings.clerk_issuer:
            decode_kwargs["issuer"] = settings.clerk_issuer
        if settings.clerk_audience:
            decode_kwargs["audience"] = settings.clerk_audience
        return jwt.decode(token, signing_key.key, **decode_kwargs)
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {e}") from e


def _claim_email(claims: dict[str, Any]) -> str | None:
    if isinstance(claims.get("email"), str):
        return claims["email"]
    emails = claims.get("email_addresses")
    if isinstance(emails, list) and emails:
        first = emails[0]
        if isinstance(first, dict) and first.get("email_address"):
            return str(first["email_address"])
    return None


async def _upsert_clerk_user(
    session: AsyncSession,
    *,
    claims: dict[str, Any],
) -> User:
    """Link a Clerk subject to a User row.

    Role model ("D + Hybrid"): admin is IdP-owned (Clerk claim / allowlist);
    everyone else defaults to ``client`` and self-serves the client<->worker
    switch via ``PATCH /auth/role``. We elevate to admin from claims but never
    auto-demote (claim removal is handled out-of-band).
    """
    external_id = str(claims.get("sub") or "")
    if not external_id:
        raise HTTPException(status_code=401, detail="Token missing sub")

    is_admin = _claims_are_admin(claims)
    email = _claim_email(claims) or f"{external_id}@users.clerk.orchestra.local"
    name = claims.get("name") or claims.get("full_name") or email.split("@")[0]

    user = await session.scalar(select(User).where(User.external_auth_id == external_id))
    if user is None:
        user = await session.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            id=uuid.uuid4(),
            email=email,
            full_name=str(name)[:255],
            role="admin" if is_admin else "client",
            external_auth_id=external_id,
            email_verified=True,
            is_active=True,
        )
        session.add(user)
    else:
        user.external_auth_id = external_id
        if name:
            user.full_name = str(name)[:255]
        if is_admin and user.role != "admin":
            user.role = "admin"
    await session.flush()
    return user


async def set_user_role(session: AsyncSession, user: User, role: str) -> User:
    """Switch portal role (client ↔ worker). Admin cannot be set via API."""
    if role not in ("client", "worker"):
        raise ValueError(f"Invalid role: {role}")
    if user.role == "admin":
        raise PermissionError("Admin role cannot be changed via API")

    user.role = role
    if role == "worker":
        profile = await session.get(WorkerProfileRecord, user.id)
        if profile is None:
            session.add(
                WorkerProfileRecord(
                    user_id=user.id,
                    headline="",
                    bio="",
                )
            )
    await session.flush()
    return user


async def resolve_user(
    session: AsyncSession,
    request: Request,
    *,
    prefer_role: str,
) -> User:
    """Resolve actor *identity* (no role gate).

    Demo mode returns the seeded stub for ``prefer_role``; Clerk mode verifies
    the JWT and upserts the linked user. Role enforcement is the caller's job
    via ``_require_active_role`` (``get_current_client`` / ``get_current_worker``).
    """
    if settings.auth_mode != "clerk":
        if prefer_role == "worker":
            return await get_demo_worker(session)
        return await get_demo_client(session)

    token = _bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authorization Bearer required")
    claims = _verify_clerk_token(token)
    return await _upsert_clerk_user(session, claims=claims)


def _require_active_role(user: User, required: str) -> User:
    """Enforce the active portal role. Admin is a super-role (allowed in any lane)."""
    if user.role == required or user.role == "admin":
        return user
    raise HTTPException(
        status_code=403,
        detail=(
            f"This action requires the {required} portal, but your active role "
            f"is '{user.role}'. Switch with PATCH /auth/role."
        ),
    )


async def get_current_client(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await resolve_user(db, request, prefer_role="client")
    return _require_active_role(user, "client")


async def get_current_worker(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await resolve_user(db, request, prefer_role="worker")
    return _require_active_role(user, "worker")


async def get_current_user_for_me(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_orchestra_role: str | None = Header(default=None, alias="X-Orchestra-Role"),
) -> User:
    prefer = "worker" if (x_orchestra_role or "").lower() == "worker" else "client"
    return await resolve_user(db, request, prefer_role=prefer)


def _claims_are_admin(claims: dict[str, Any]) -> bool:
    """True when Clerk public_metadata.role is admin or email is allowlisted."""
    meta = claims.get("public_metadata") or claims.get("metadata") or {}
    if isinstance(meta, dict) and str(meta.get("role", "")).lower() == "admin":
        return True
    email = _claim_email(claims)
    if email and email.lower() in settings.admin_email_allowlist_set:
        return True
    return False


async def get_current_admin(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Admin is IdP-owned. Clerk: require admin claim / allowlist. Demo: dev-only
    convenience — never allowed when APP_ENV=production (defense in depth)."""
    if settings.auth_mode != "clerk":
        if settings.is_production:
            raise HTTPException(
                status_code=403, detail="Admin requires Clerk auth in production"
            )
        return await get_demo_client(db)

    token = _bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authorization Bearer required")
    claims = _verify_clerk_token(token)
    if not _claims_are_admin(claims):
        raise HTTPException(status_code=403, detail="Admin access required")
    return await _upsert_clerk_user(db, claims=claims)
