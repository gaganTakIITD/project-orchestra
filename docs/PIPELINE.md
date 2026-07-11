# 🚀 Project Orchestra — Build Pipeline

> **Single source of truth for what to work on.** Every agent (Cursor, v0, human) reads this before starting and updates it after finishing. If it's not here, it's not planned; if you did it, mark it.
>
> **North star:** Production Outcome-as-a-Service — client **co-creates the OutcomeSpec in real time with Gemini** (chat + live spec panel), confirms quote, Spine executes plan/match/QA/delivery with live tracker updates. See `docs/SPEC_CO_CREATION.md`.

**Legend:** `[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked

**Owners:** `v0` = Vercel v0 on `main` · `cursor` = Cursor agents on `core` · `founder` = human decision

---

## 🎯 NOW (current sprint — do these first)

> **Active sub-plan:** [`docs/SUBPLAN_S2_STAGES.md`](SUBPLAN_S2_STAGES.md) — Stage-wise product live (A → C complete; **D deepen is LATER**)

### N0. Interactive Chat Surfaces — **primary product UX** ⟵ **NORTH STAR**

- Owner: `cursor` (chat API + Gemini + streaming) + `v0` (`ChatSurface` component)
- Docs: `docs/CHAT_SURFACES.md` · `docs/SPEC_CO_CREATION.md`
- [x] Contract: `ChatSession`, `ChatMessage`, `OutcomeSpecDraft` in `lib/types.ts`
- [x] Mock + API: `chatApi`, hooks (`useStartScopeSession`, `useSendChatMessage`, `useFinalizeChatSession`)
- [x] Backend: chat sessions, spec extractor, completeness gating, finalize → quote
- [x] UI: `ScopeChatSurface` + `JobDescriptionPanel` on `/start`
- [x] Gemini AI gateway — `app/ai/gateway.py` structured JSON extraction, **key-ready** (set `GEMINI_API_KEY`), deterministic fixture fallback, `ai_decision_log` audit
- [ ] **v0:** dedicated resumable page `/scope/[sessionId]` (move chat off `/start`; `/start` creates session → redirect) — **shipped on `main` (`c3ab130`), live on Vercel**
- [x] SSE streaming tokens — `POST /chat/sessions/{id}/messages/stream`, `ChatStreamEvent`, `sendMessageStream` hook + scope page consumer
- [ ] Stage 3: Preference Chat Surface — Matcher agent
- **Done when:** user scopes in chat, sees JSON fields populate live, tweaks in thread, confirms without a cold proposal page.

### N0b. DB production hardening — `cursor` ✅

- [x] Alembic migrations (`backend/alembic/`, baseline `0001_baseline`); Docker runs `alembic upgrade head` on boot
- [x] `create_all` gated behind `AUTO_CREATE_ALL` (dev/test only; prod uses migrations)
- [x] Connection pool: `pool_pre_ping`, sized pool, recycle (`app/db/session.py`)
- [x] Chat session ownership checks (403 on cross-client access)
- [x] `ai_decision_log` audit table (AI proposes; Spine decides)
- [ ] Replace `get_demo_client` stub with real JWT auth (`founder` decision on provider) — **Stage D**

### N1. Product path on real API — Stages A–C ✅

- Owner: `cursor`
- Sub-plan: [`docs/SUBPLAN_S2_STAGES.md`](SUBPLAN_S2_STAGES.md)
- [x] **Stage A:** `POST /tasks/{id}/accept-interest`, `ready-to-start`, `submit` + `submissions` + Spine events
- [x] **Stage B:** `GET/POST /tasks/{id}/discussion`, `GET /orders/{id}/delivery`, `POST .../accept-delivery`
- [x] **Stage C:** `NEXT_PUBLIC_USE_MOCKS=false` product path + `tests/test_product_smoke.py` (intent→submit)
- [x] Browser bind with `USE_MOCKS=false` — `.env.local` + Docker API rebuilt; live path intent→accept→submit verified 2026-07-12
- **Done when:** worker accept → submit and client delivery accept work against Postgres without mocks — **met (API + pytest + live curl)**

### N2. Backend B2 — Spine integration tests

- Owner: `cursor`
- [x] State machines + EventWriter + unit tests
- [x] Integration pytest with Postgres — task lifecycle + product smoke
- **Done when:** pytest drives worker lifecycle with events in DB — **met**

### N3. Stage 3 worker screens

- Owner: `v0` + `cursor` (hook wiring)
- [x] `/join` — talent landing + CTA → `/worker/onboarding`
- [x] `/worker/onboarding` — profile wizard + ≥70% gate (v0)
- [x] `/worker` — task inbox via `useWorkerProfile` + `useMyTasks` (wired to contract)
- [x] `/worker/tasks/[taskId]` — Charter + TaskPacket job card via hooks + accept / ready / submit
- [x] Backend: `GET /workers/profile`, `GET /workers/me/tasks`, charter/packet APIs + lifecycle routes
- **Done when:** worker journey clickable on real API (stubs until Stage D auth)

---

## 📋 NEXT (queued — start when NOW empties)

### X1. Stage D — deepen pass

- Owner: `cursor` + `founder`
- [x] Auth first slice: Clerk-ready JWT + demo fallback (`AUTH_MODE`, `get_current_*`) — set Clerk keys to go live
- [ ] Founder: Clerk app + secrets; flip `AUTH_MODE=clerk`
- [ ] Gemini required for Spec Compiler + Task Packet in prod
- [ ] Matcher from DB profiles (not fixture list)
- [ ] Onboarding persists to `worker_profiles`
- [ ] Deploy (Vercel + API host) + secrets

### X2. Backend B4 — AI gateway + 4 agents (fixtures → Gemini)

- Owner: `cursor`
- [x] AI gateway: schema validation, `ai_decision_log`, Spec Compiler (key-ready + fixture fallback)
- [x] **Task Packet Generator** — Charter + TaskPacket on plan build; `GET /tasks/{id}/charter` + `/packet`
- [ ] Architect (DAG builder, acyclic validation) — still fixture
- [ ] Matcher (filter + rank from DB profiles)
- [ ] QA Judge (deterministic checks + Gemini Vision) — stage auto-QA stub in submit path
- [ ] **Bind gate #3:** proposal card shows real AI-scoped spec

### X3. Bind gate #1 — catalog on real API (browser)

- Owner: `founder`
- [ ] Homepage SKU cards with `USE_MOCKS=false`

---

## 🔭 LATER (post-slice — do not start early)

- [ ] B5 vertical slice: pytest `intent → delivered` end-to-end (partially covered by `test_full_dag_delivery_and_accept`)
- [ ] Bind gate #4: flip `USE_MOCKS=false` globally in production
- [ ] WebSocket live tracker updates
- [ ] B6: CI (GitHub Actions), contract tests, run-slice script
- [ ] Admin console (verify workers, human queue, AI decision log)
- [ ] Mock ledger visuals (funds held / reserved / released states)
- [ ] Auth UI + session handling
- [ ] Deploy: Vercel (frontend) + Railway/Cloud Run (backend) for product URL

**Explicitly out of scope (don't build):** real payments, TDS math, disputes UI, PM control loop, RAG flywheel, notifications/email, mobile apps.

---

## ✅ SHIPPED

- [x] Planning docs (design notes, tech spec, master plan, diagrams)
- [x] Repo: Next.js 16 at root, v0-compatible, GitHub `gaganTakIITD/project-orchestra`
- [x] Branch model: `main` = v0 UI · `core` = contract + backend
- [x] Shared contract: `lib/types.ts`, `mock-data.ts`, `api.ts`, `hooks.ts`, `state-labels.ts`
- [x] Design tokens + `docs/V0_HANDOFF.md`
- [x] Stage 1 homepage refresh (v0 — Lumena/Bauhaus redesign, Framer Motion, a11y pass)
- [x] **Stage 2 client workflow (v0)** — `/start`, `/proposal/[quoteId]`, `/orders/[orderId]`, preferences; IntentForm + hooks wired; deployed on `main`
- [x] B2 Spine code: state machines, event_log, TaskSpine/OrderSpine, timer stub, pytest
- [x] B3 slice: auth stub, intent/quote/order API, fixture spec compiler, client hooks
- [x] B3 fulfillment: Architect fixture plan, milestones/candidates/preferences API
- [x] Agent framework: `AGENTS.md` playbook + `.cursor/rules/` (frontend contract, backend spine)
- [x] **S2 Stages A–C:** worker lifecycle, discussion, delivery accept, product smoke (`SUBPLAN_S2_STAGES.md`)

---

## 📐 How to use this pipeline (all agents)

1. **Pick from NOW** — top item your lane owns. Don't cherry-pick from LATER.
2. **Announce** — before starting: scope, files, done-when test.
3. **Ship** — end with something runnable (pytest / curl / browser).
4. **Update this file** — tick boxes, move finished blocks to SHIPPED, promote NEXT → NOW when a slot frees.
5. **Blocked?** Mark `[!]` with a one-line reason and move on — don't idle.
6. **Scope creep?** New ideas go to LATER, not into the current sprint.

**Escalate to founder when:** contract shapes change, money/legal logic appears, v0 and core lanes collide, or a stage checkpoint slips.
