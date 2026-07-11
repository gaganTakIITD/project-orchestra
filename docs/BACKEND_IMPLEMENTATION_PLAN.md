# Project Orchestra — Backend Implementation Plan

> **Purpose:** Detailed execution plan to build the **master architecture** (Spine + services + AI) and **bind it to the existing Next.js frontend** on `core`, without breaking v0's UI work on `main`.
>
> **Companion docs:** `Project_Orchestra_Technical_Spec.md` · `Project_Orchestra_Startup_Master_Plan.md` · `docs/V0_HANDOFF.md`
>
> **Last updated:** 2026-07-11 · **Branch:** `core` (backend + `lib/` contract)

---

## 0. Current state (honest baseline)

| Layer | Status |
|-------|--------|
| **Frontend UI** (v0 on `main`) | Stage 1 homepage + `/start` + `/join` shells |
| **Frontend contract** (`lib/`) | Types, mocks, hooks, mock-first API client — **done** |
| **Backend** | **Starting now** — was 0% |
| **Spine / AI / DB** | Not built yet |

**Binding rule:** The frontend never calls FastAPI directly. It calls `lib/api.ts` → hooks in `lib/hooks.ts`. When the backend endpoint exists and returns JSON matching `lib/types.ts`, set `NEXT_PUBLIC_USE_MOCKS=false` for that surface — **no component changes**.

---

## 1. Architecture recap (what we are building)

```text
┌─────────────────────────────────────────────────────────────┐
│  Next.js (v0 UI on main / contract on core)                 │
│  lib/hooks.ts  →  lib/api.ts  →  FastAPI /api/v1            │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│  API Gateway (FastAPI) — auth, RBAC, CORS, OpenAPI           │
├─────────────────────────────────────────────────────────────┤
│  Domain Services — intent, quote, order, task, profile, …    │
├─────────────────────────────────────────────────────────────┤
│  ORCHESTRATOR (Spine) — state machines, timers, event log    │
├─────────────────────────────────────────────────────────────┤
│  AI Gateway — Gemini nodes (fixtures first, then real)       │
└───────────────────────────────┬─────────────────────────────┘
                                │
              PostgreSQL (+ pgvector) · Redis · MinIO
```

**Golden rule:** AI proposes structured JSON; **Spine enforces** transitions and writes `event_log`. AI never mutates state directly.

---

## 2. Phased build (6 backend steps + frontend binding gates)

Each phase ends with a **checkpoint** you can demo. I will **confirm scope with you** before starting any phase that touches v0-owned files (`app/**`, `components/**`) or changes the frozen contract shape.

---

### Phase B1 — Foundation + first bind (NOW)

**Goal:** Runnable backend stack; **homepage catalog works against real API**.

| # | Task | Owner | Done when |
|---|------|-------|-----------|
| B1.1 | `docker-compose.yml` — Postgres (pgvector), Redis, MinIO, API | Cursor | `docker compose up` healthy |
| B1.2 | FastAPI app — `/health`, `/docs`, CORS for `localhost:3000` | Cursor | Browser + curl OK |
| B1.3 | SQLAlchemy 2.0 async models — identity, taxonomy, catalog tables | Cursor | Alembic migration applies |
| B1.4 | Seed script — SKUs, skills, tools, task_types (match `lib/mock-data.ts`) | Cursor | Seed idempotent |
| B1.5 | API routes — `GET /catalog/skus`, `/taxonomy/*` | Cursor | Response matches `lib/types.ts` |
| B1.6 | **Frontend bind gate #1** — `.env.example`, catalog on real API | Cursor | `useSkus()` works with `USE_MOCKS=false` |

**Not in B1:** Spine, AI, auth JWT, intent flow — deferred to B2–B5.

---

### Phase B2 — The Spine (highest engineering priority)

**Goal:** Deterministic order + task state machines with audit trail.

| # | Task | Done when |
|---|------|-----------|
| B2.1 | `event_log` table + transactional outbox pattern | Events persist in same txn as domain write |
| B2.2 | Order state machine — transitions per Spec §5.1 | Legal/illegal transition unit tests |
| B2.3 | Task state machine — transitions per Spec §5.2 | Same |
| B2.4 | Transition guards + `EventLog` writer | Every state change logged with actor |
| B2.5 | Redis-backed durable timer stubs (priority window) | Timer job fires in test |
| B2.6 | Orchestrator `handle_event()` dispatcher | Handler registry wired |

**Checkpoint:** Drive one task `blocked → ready → invited` in pytest without UI.

---

### Phase B3 — Core domain services

**Goal:** Business logic behind the client + worker journeys.

| Service | Key methods | Events emitted |
|---------|-------------|----------------|
| AuthService | register, login, JWT, stub `/auth/me` | UserRegistered |
| IntentService | create_intent, add_clarification | IntentCaptured |
| QuoteService | generate_quote (deterministic formula) | QuoteIssued |
| OrderService | accept_quote, freeze spec | OrderConfirmed |
| FulfillmentService | build_plan, unlock_ready_tasks | PlanApproved |
| TaskService | transition, assign | per transition |
| PreferenceService | set_preferences, accept_interest, promote_backup | PreferencesSet, InterestAccepted |
| WorkerProfileService | CRUD, completion % | ProfileUpdated |
| SubmissionService | submit deliverable | SubmissionReceived |

**Frontend bind gate #2:** `/start` → POST `/intents` → real intent_id; proposal page reads spec + quote.

---

### Phase B4 — AI gateway + 4 core agents (fixtures → Gemini)

| Agent | Trigger | Output | MVP mode |
|-------|---------|--------|----------|
| Spec Compiler | IntentCaptured | OutcomeSpec | Fixture JSON first |
| Risk Classifier | SpecCompiled | risk_tier | Fixture |
| Architect | OrderConfirmed | task DAG | Fixture (3–5 tasks) |
| Matcher | task ready | ranked shortlist | Fixture + DB profiles |
| QA Judge | SubmissionReceived | pass/fail + evidence | Fixture |

**Gateway:** schema validation, `ai_decision_log`, confidence gate → human queue stub.

**Frontend bind gate #3:** Intent → AI-scoped proposal card shows **real** spec fields from backend.

---

### Phase B5 — Vertical slice integration (S0 milestone)

**Goal:** Full path via API/tests — no browser required for proof.

```text
POST /intents → Spec → Quote → accept → Order → Plan (DAG)
→ preferences → interest → priority → mutual start → submit → QA pass
→ task completed → delivery bundle → order delivered
```

| # | Task | Done when |
|---|------|-----------|
| B5.1 | Wire all services through Spine handlers | Event chain F1 complete |
| B5.2 | WebSocket channels (`order:{id}`, `task:{id}`) — log-only OK | Events emitted |
| B5.3 | pytest integration test `test_vertical_slice.py` | CI green |
| B5.4 | Mock ledger states (authorize/reserve/release) | Balance invariant test |

**Frontend bind gate #4:** Set `NEXT_PUBLIC_USE_MOCKS=false` globally; Stage 2 client tracker on real data.

---

### Phase B6 — Harden + production readiness

- Contract tests vs OpenAPI
- Idempotency / event replay tests
- `scripts/run_vertical_slice.sh`
- GitHub Actions CI for backend
- Env docs, runbook in README

---

## 3. Frontend binding matrix

Maps each `lib/api.ts` function → backend endpoint → UI consumer → bind phase.

| API function | Endpoint | Used by (today) | Bind phase |
|--------------|----------|-----------------|------------|
| `catalogApi.listSkus` | `GET /catalog/skus` | `outcome-catalog.tsx` | **B1** |
| `catalogApi.listTaskTypes` | `GET /taxonomy/task-types` | future onboarding | B1 |
| `catalogApi.listSkills` | `GET /taxonomy/skills` | future onboarding | B1 |
| `catalogApi.listTools` | `GET /taxonomy/tools` | future onboarding | B1 |
| `clientApi.createIntent` | `POST /intents` | `/start` form | B3 |
| `clientApi.getSpec` | `GET /intents/{id}` | proposal page | B3/B4 |
| `clientApi.getQuote` | `GET /quotes/{id}` | proposal page | B3 |
| `clientApi.acceptQuote` | `POST /quotes/{id}/accept` | proposal CTA | B3 |
| `clientApi.getOrder` | `GET /orders/{id}` | tracker | B5 |
| `clientApi.getPlan` | `GET /orders/{id}/milestones` | tracker | B5 |
| `clientApi.getCandidates` | `GET /orders/.../candidates` | preferences | B4/B5 |
| `workerApi.getProfile` | `GET /workers/profile` | worker onboarding | B3 |
| `workerApi.getMyTasks` | `GET /workers/me/tasks` | worker inbox | B5 |
| `authApi.me` | `GET /auth/me` | header/session | B3 |

**How to bind (per gate):**

1. Backend endpoint returns JSON **matching `lib/types.ts`** (snake_case fields).
2. Add integration test for the endpoint.
3. Set in `.env.local`:
   ```bash
   NEXT_PUBLIC_USE_MOCKS=false
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
   ```
4. Verify the v0 screen still renders (loading → data).
5. Document in this file which gates are ✅.

---

## 4. Repo layout (backend)

```text
backend/
├── app/
│   ├── main.py              # FastAPI entry, CORS, routers
│   ├── config.py            # pydantic-settings
│   ├── api/v1/
│   │   ├── router.py
│   │   ├── health.py
│   │   ├── catalog.py       # B1
│   │   ├── taxonomy.py      # B1
│   │   └── …                # B3+
│   ├── models/              # SQLAlchemy ORM
│   ├── schemas/             # Pydantic request/response (mirror lib/types)
│   ├── services/
│   ├── orchestrator/        # B2 — Spine
│   ├── ai/                  # B4 — gateway + agents
│   └── db/
│       ├── session.py
│       └── seed.py
├── alembic/
├── tests/
├── pyproject.toml
└── Dockerfile
docker-compose.yml           # repo root
.env.example                 # repo root
```

---

## 5. Branch & merge strategy

| Branch | Who | Contains |
|--------|-----|----------|
| `main` | v0 | UI only |
| `core` | Cursor | backend + `lib/` + env docs |

- Backend PRs: `core` → merge to `core`, periodically `main` → `core` to pick up v0 UI.
- When a bind gate is ready, PR `core` → `main` with **only** `lib/`, `backend/`, `.env.example` — avoid overwriting v0 components.
- v0 continues using mocks until we explicitly flip env on deploy preview.

---

## 6. Confirmation protocol (every phase)

Before I start each phase, I will state:

1. **Phase ID** (e.g. B2 Spine)
2. **Files I will create/modify**
3. **What I will NOT touch** (v0 UI unless you approve)
4. **Done-when test**
5. **Frontend bind gate** (if any)

After each phase:

1. Demo command (curl / pytest / npm run dev)
2. Update **Progress tracker** below
3. Ask before starting next phase if it changes contract shapes

---

## 7. Progress tracker

| Phase | Status | Bind gate | Notes |
|-------|--------|-----------|-------|
| B1 Foundation + catalog API | ✅ Code complete | Gate #1 catalog | Docker required to run stack; pytest health ✅ |
| B2 Spine | ⬜ Not started | — | **Next** |
| B3 Core services | ⬜ Not started | Gate #2 intent/quote | |
| B4 AI gateway + agents | ⬜ Not started | Gate #3 spec/proposal | |
| B5 Vertical slice | ⬜ Not started | Gate #4 full client flow | |
| B6 Harden + CI | ⬜ Not started | Gate #5 production | |

---

## 8. Immediate next actions (B1 — this session)

1. ✅ Write this plan
2. ✅ Create `docker-compose.yml` + `backend/` FastAPI skeleton
3. ✅ Models + seed (SKUs match mock data)
4. ✅ `GET /api/v1/catalog/skus` + taxonomy routes
5. ✅ CORS + `.env.example` for frontend bind
6. ⬜ Run stack (needs Docker Desktop) + verify `useSkus()` against real API

**After B1 runtime verify:** Confirm with you, then start **B2 Spine** (state machines).

---

*AI proposes; the Spine enforces. Frontend reflects backend truth — never the other way around.*
