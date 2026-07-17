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

The startup update script keeps deps fresh (`pnpm install` + editable backend install). Everything below is what that script does **not** do.

**Toolchain gotchas**
- Use `python3` (there is no `python` shim). Console scripts (`uvicorn`, `pytest`, `alembic`) install to `~/.local/bin` — run `export PATH="$HOME/.local/bin:$PATH"` or invoke via `python3 -m ...`.
- Frontend package manager is **pnpm** (matches CI + `pnpm-lock.yaml`), not npm, even though the README says `npm`. Node 22.

**Postgres (no Docker here)**
- Docker is not available; the compose stack (`redis`/`minio`) is not used. Redis is unused by the code and MinIO is stubbed (no `boto3`), so only Postgres matters.
- Postgres runs natively. Start it each session with `sudo pg_ctlcluster 16 main start`. Role/db `orchestra`/`orchestra` on `localhost:5432` (db `orchestra`) already exist in the data dir. If ever missing: `sudo -u postgres psql -c "CREATE ROLE orchestra LOGIN PASSWORD 'orchestra' SUPERUSER;" && sudo -u postgres createdb -O orchestra orchestra`.
- No pgvector extension needed (template embeddings are stored as JSON float lists).

**Running the app (dev mode)**
- Backend: from `backend/`, `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`. It reads `/workspace/.env` (points `DATABASE_URL` at localhost) and on boot creates tables (`AUTO_CREATE_ALL=true`) + seeds catalog/demo users (`AUTO_SEED=true`). Health: `curl localhost:8000/api/v1/health`.
- Frontend: from repo root, `pnpm dev`. `.env.local` sets `NEXT_PUBLIC_USE_MOCKS=false` + `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1` to hit the real API.
- Gemini/Clerk are optional: without `GEMINI_API_KEY` the AI gateway uses deterministic fixtures; with `AUTH_MODE=demo` (default) the backend uses seeded demo client/worker stubs — no login needed for API/E2E.

**Known pre-existing issue (not an env problem)**
- In demo mode (no `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`), any page rendering the shared header **500s** during SSR: `AuthNav` → `useOrchestraAuth()` calls Clerk's `useAuth()` *before* the `clerkEnabled` early-return, so it throws outside a `ClerkProvider`. Clerk-gated pages without the header (e.g. `/sign-in`) still render. Setting valid Clerk keys (mounts `ClerkProvider`) or fixing the hook order unblocks the header pages; the backend + API flow are unaffected.
