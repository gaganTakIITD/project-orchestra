<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

---

# Project Orchestra — Agent Playbook

You are working in a **startup building toward production**, not a one-off demo. Ship vertical slices that match the north star; defer polish that doesn't serve it.

## What this product is (30 seconds)

**Outcome-as-a-Service.** The client describes an outcome in natural language; Gemini **extracts** a strict `OutcomeSpec` (that **is** the job description — one object, human + machine views). Once confirmed, the Spine plans tasks, matches talent, and delivers. See `docs/CHAT_SURFACES.md`.

Read before designing anything:
- `docs/PIPELINE.md` — **what to work on next (single source of truth)**
- `docs/CHAT_SURFACES.md` — **interactive chat + strict JSON artifacts at every stage (Cursor-like UX)**
- `docs/SPEC_CO_CREATION.md` — Stage 1 scope chat detail

## Who owns what (do not cross lanes)

| Lane | Owner | Branch | Paths |
|------|-------|--------|-------|
| Core UI (screens, components) | **Vercel v0** | `main` | `app/**`, `components/**` |
| Contract + backend + infra | **Cursor agents** | `core` | `lib/**`, `backend/**`, `docker-compose.yml`, config |

- Never rewrite v0's components wholesale; wire them to the contract instead.
- Merge direction: `main → core` to pick up UI; PR `core → main` for contract/backend only.

## Non-negotiable rules (from the founder's spec)

1. **Contract-first.** Data shapes live in `lib/types.ts` (frontend) and mirror `backend/app/schemas/` (snake_case JSON). Change shapes in both or not at all.
2. **UI never fetches directly.** Screens use hooks in `lib/hooks.ts` → `lib/api.ts`. Mock↔real swap is `NEXT_PUBLIC_USE_MOCKS` only.
3. **AI never mutates state.** Gemini nodes return structured JSON; the Spine validates and executes transitions.
4. **Every state change writes `event_log`** with actor + reason.
5. **Frozen things stay frozen.** `OutcomeSpec` after confirm, `Charter` after mutual start — changes only via `Amendment`.
6. **No real money.** Ledger states only (mock) until payments integration.

## Startup working style

- **Vertical slice > breadth.** One path working end-to-end beats five half-built features.
- **Confirm before big moves.** State scope, files touched, and done-when test before starting a phase; report honestly after (including failures).
- **Update `docs/PIPELINE.md`** when you finish, start, or discover work. Stale pipelines kill startups.
- **Demo-able checkpoints.** Every work session should end in something runnable (curl, pytest, or browser).
- Don't gold-plate: no premature abstractions, no speculative config, no features outside the current pipeline stage.

## Quick commands

```bash
npm run dev                        # frontend on :3000 (mocks by default)
docker compose up -d --build       # backend stack (needs Docker Desktop)
curl localhost:8000/api/v1/health  # backend alive?
cd backend && python -m pytest     # backend tests
npx tsc --noEmit                   # frontend type check
```

## Cursor Cloud specific instructions

The startup update script only refreshes dependencies (`pnpm install` for the frontend, and a Python venv at `backend/.venv` with `pip install -e "./backend[dev]"`). Datastore, services, and env files are NOT started/created by it — do the following manually each session.

**Postgres (required, native — not Docker here).** This VM runs PostgreSQL 16 + `pgvector` natively (the repo's `docker-compose.yml` is not used in Cloud). The cluster does not auto-start; start it once per session:
```bash
sudo pg_ctlcluster 16 main start
```
DB `orchestra` / role `orchestra` (password `orchestra`) and the `vector` extension already exist and match the default `DATABASE_URL`. If the DB is ever missing, recreate with: `sudo -u postgres psql -c "CREATE ROLE orchestra LOGIN PASSWORD 'orchestra';" ; sudo -u postgres createdb -O orchestra orchestra ; sudo -u postgres psql -d orchestra -c "CREATE EXTENSION IF NOT EXISTS vector;"`.

**Backend (FastAPI/uvicorn).** Use the venv interpreter directly (no `activate` needed). The backend needs no `.env` — `app/config.py` defaults already point at the local DB, `AUTH_MODE=demo`, `AUTO_SEED=true`, `AUTO_CREATE_ALL=true` (tables + demo client/worker are created on boot). Gemini is optional (deterministic fixtures when `GEMINI_AUTH=off`). Production uses Vertex on `raystartup` (`GEMINI_AUTH=vertex`) — never AI Studio API keys; see `docs/GCP_BILLING_SPLIT.md`.
```bash
cd backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Tests + contract check (run from `backend/`, Postgres must be up): `.venv/bin/python -m pytest` and `.venv/bin/python ../scripts/check_openapi_contract.py`.

**Frontend (Next.js 16, Turbopack).** To run the UI against the real API (not mocks), create `.env.local` at the repo root before `pnpm dev`:
```
NEXT_PUBLIC_USE_MOCKS=false
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```
Without `.env.local` the app still runs but serves mock data. The CI/typecheck gate is `pnpm run typecheck` (passes); `pnpm run lint` runs but has pre-existing errors/warnings and is NOT a CI gate — do not treat those as regressions.

**Known gotcha — demo mode + Clerk.** The app is designed to run without Clerk (demo mode, no `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`), but `lib/use-orchestra-auth.ts` calls Clerk's `useAuth()` *before* its `if (!clerkEnabled)` guard. With the pinned `@clerk/nextjs` 7.5.17 that throws outside a `<ClerkProvider>`, so every page 500s in demo mode. All other Clerk usages are correctly demo-guarded. To run the full UI locally, either set a real `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, or move the `if (!clerkEnabled) return {...}` guard above the `useAuth()` call in `lib/use-orchestra-auth.ts` (one line; `lib/` is Cursor's lane).
