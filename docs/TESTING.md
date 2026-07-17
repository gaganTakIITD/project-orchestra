# Project Orchestra — Testing & Reliability

> **Goal:** Move from campus prototype to **industry-standard** Outcome-as-a-Service — every critical path is automated, CI gates merges, and prod smoke is repeatable.
>
> **Parent:** `docs/PIPELINE.md` · **Run locally:** see [Quick commands](#quick-commands)

---

## Pyramid (what we run and when)

| Layer | Tool | Scope | When |
|-------|------|-------|------|
| **Unit** | Vitest (`lib/`) | Pure contract helpers — labels, journey maps, API mock flag | Every PR |
| **Unit** | pytest (no DB) | Transition graphs, AI fixtures, timer queue | Every PR |
| **Integration** | pytest + Postgres | Spine, services, HTTP via ASGI | Every PR (CI service) |
| **Vertical slice** | `test_product_smoke.py` + `scripts/run-slice.py` | Chat → quote → order → worker → delivery → closed | Every PR |
| **Contract** | `scripts/check_openapi_contract.py`, `scripts/check_status_enum_parity.py` | OpenAPI paths + TS/Python enum parity | Every PR |
| **Build** | `next build`, `tsc --noEmit` | Frontend compiles for production | Every PR |
| **E2E (browser)** | Playwright | Clerk sign-in, scope chat, tracker (planned) | Pre-prod gate |
| **Prod smoke** | `docs/DEPLOY_API.md` checklist | Two Clerk accounts on Vercel + Cloud Run | Before campus / payments |

---

## Current coverage (baseline 2026-07-17)

### Backend — strong

- **~124 pytest tests** across 31 files
- Postgres-backed integration for Spine, lifecycle, auth (mock JWKS), timers, ledger, amendments, disputes, notifications, WebSocket fan-out
- **Vertical slice:** `test_chat_path_finalize_to_delivery_accept` — full happy path without mocks
- **Gaps addressed in this chapter:** order Spine transition matrix, priority-window timeout via HTTP tick, enum parity script, coverage reporting

### Frontend — was zero; now starting

- Vitest on `lib/state-labels.ts`, `lib/journey.ts` (contract invariants)
- **Still needed:** `lib/api.ts` / `lib/hooks.ts` with MSW; Playwright happy path

### CI — hardened

- Backend: pytest + OpenAPI path check + **enum parity** + **coverage report** (informational threshold)
- Frontend: `tsc`, **vitest**, **`next build`**
- **Still needed:** ESLint gate (pre-existing warnings in v0 components), Playwright job, Alembic migration test, optional Gemini eval (secret-gated)

---

## Critical paths — must stay green

These are non-negotiable for production confidence:

1. **Order + task Spine** — every legal transition works; illegal transitions raise `IllegalTransitionError`
2. **Vertical slice** — `test_product_smoke.py` (intent + chat paths)
3. **Priority window** — accept-interest schedules timer; tick promotes backup worker
4. **Auth RBAC** — client/worker/admin route guards (demo + mock Clerk JWKS)
5. **Ledger** — Held → Reserved → Released; debits == credits per order
6. **Contract parity** — `lib/types.ts` status enums match `backend/app/orchestrator/states.py`
7. **Client label safety** — `rework` never exposed to clients (`state-labels.ts`)

---

## Test files map

### Backend (`backend/tests/`)

| File | Focus |
|------|--------|
| `test_product_smoke.py` | End-to-end product path (P0 gate) |
| `test_reliability.py` | Order Spine matrix, priority timeout HTTP path |
| `test_spine.py` | Task Spine + transition graph |
| `test_timers.py` | Durable timers, tick endpoint |
| `test_auth.py` | Demo + Clerk JWT, RBAC |
| `test_ledger.py` / `test_payments_ledger.py` | Mock funds lifecycle |
| `test_task_lifecycle.py` | Worker accept → submit → QA |
| `test_amendments.py` / `test_disputes_pm.py` | Post-delivery ops |

### Frontend (`lib/__tests__/`)

| File | Focus |
|------|--------|
| `state-labels.test.ts` | Dual-view labels; rework hidden from client |
| `journey.test.ts` | Stage mapping for order/task statuses |

### Scripts (`scripts/`)

| Script | Purpose |
|--------|---------|
| `check_openapi_contract.py` | Required REST paths in OpenAPI |
| `check_status_enum_parity.py` | TS ↔ Python status enum sync |
| `run-slice.py` | Dev onboarding vertical slice (mirrors smoke test) |

---

## Phased roadmap → industry standard

### Phase R0 — Foundation (this PR)

- [x] `docs/TESTING.md` (this file)
- [x] Order Spine transition tests
- [x] Priority timeout reliability test
- [x] Enum parity CI check
- [x] Vitest + lib unit tests
- [x] CI: lint, build, vitest, coverage

### Phase R1 — Contract & Spine depth

- [ ] Centralize pytest fixtures in `conftest.py` (single `api_client` / `db_session`)
- [ ] Order transition integration tests (DB + `event_log`)
- [ ] Amendment approve via API in vertical slice
- [ ] Ledger global invariant: Σ debits == Σ credits per order across all events
- [ ] `lib/types.ts` ↔ Pydantic schema field parity (beyond enums)

### Phase R2 — Frontend confidence

- [ ] MSW-backed tests for `lib/api.ts` real vs mock branches
- [ ] React Testing Library for `JourneyStepper`, `WorkspaceHeader` notification badge
- [ ] Playwright: Clerk test user → scope → quote → confirm → tracker

### Phase R3 — Production gates

- [ ] Alembic `upgrade head` / `downgrade -1` in CI (no `AUTO_CREATE_ALL` only)
- [ ] Event handler idempotency tests (double-delivery safe)
- [ ] Payments sandbox with `PAYMENTS_ENABLED=true` in CI (test keys)
- [ ] Staging deploy smoke (GitHub Action → Vercel preview + API health)
- [ ] Optional: Gemini golden-set eval (gated on `GEMINI_API_KEY` secret)

### Phase R4 — Operability

- [ ] Sentry error budget + synthetic uptime check
- [ ] Load test: concurrent scope sessions + WS fan-out
- [ ] Disaster recovery drill: DB restore + event replay

---

## Quick commands

```bash
# Full local gate (needs Docker Postgres)
docker compose up -d postgres
cd backend && pip install -e ".[dev]" && python -m pytest -v --tb=short
python ../scripts/check_openapi_contract.py
python ../scripts/check_status_enum_parity.py

# Frontend
pnpm install
pnpm run typecheck
pnpm run lint
pnpm run test
pnpm run build

# Vertical slice (API must be up OR uses in-process ASGI)
pnpm run run-slice

# Coverage (backend)
cd backend && python -m pytest --cov=app --cov-report=term-missing --cov-fail-under=55
```

---

## Definition of done — "reliable, not prototype"

| Criterion | Status |
|-----------|--------|
| CI green on every PR to `main` | R0 |
| Vertical slice pytest green | ✅ |
| No illegal Spine transition without test | R0 (orders) / partial (tasks ✅) |
| Frontend contract lib tested | R0 started |
| Browser E2E on happy path | R2 |
| Founder prod dual-account smoke | Founder (see `DEPLOY_API.md`) |
| Payments production disabled until harden green | Policy ✅ |

**Escalate to founder when:** enabling production payments, changing frozen contract shapes, or skipping a CI gate for a release.
