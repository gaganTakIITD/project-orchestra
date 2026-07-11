# 🚀 Project Orchestra — Build Pipeline



> **Single source of truth for what to work on.** Every agent (Cursor, v0, human) reads this before starting and updates it after finishing. If it's not here, it's not planned; if you did it, mark it.

>

> **North star:** Production Outcome-as-a-Service — client **co-creates the OutcomeSpec in real time with Gemini** (chat + live spec panel), confirms quote, Spine executes plan/match/QA/delivery with live tracker updates. See `docs/SPEC_CO_CREATION.md`.



**Legend:** `[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked

**Owners:** `v0` = Vercel v0 on `main` · `cursor` = Cursor agents on `core` · `founder` = human decision



---



## 🎯 NOW (current sprint — do these first)

> **Active sub-plan:** [`docs/SUBPLAN_S1.md`](SUBPLAN_S1.md) — Scope Room + Real API Bind (S1-A → S1-B → S1-C, then demo)



### N0. Interactive Chat Surfaces — **primary product UX** ⟵ **NORTH STAR**

- Owner: `cursor` (chat API + Gemini + streaming) + `v0` (`ChatSurface` component)

- Docs: `docs/CHAT_SURFACES.md` · `docs/SPEC_CO_CREATION.md`

- [x] Contract: `ChatSession`, `ChatMessage`, `OutcomeSpecDraft` in `lib/types.ts`

- [x] Mock + API: `chatApi`, hooks (`useStartScopeSession`, `useSendChatMessage`, `useFinalizeChatSession`)

- [x] Backend: chat sessions, spec extractor, completeness gating, finalize → quote

- [x] UI: `ScopeChatSurface` + `JobDescriptionPanel` on `/start`

- [x] Gemini AI gateway — `app/ai/gateway.py` structured JSON extraction, **key-ready** (set `GEMINI_API_KEY`), deterministic fixture fallback, `ai_decision_log` audit

- [ ] **v0:** dedicated resumable page `/scope/[sessionId]` (move chat off `/start`; `/start` creates session → redirect) — **shipped on `main` (`c3ab130`), live on Vercel**

- [ ] SSE streaming tokens (backend endpoint + `ChatSurface` consumer)

- [ ] Stage 3: Preference Chat Surface — Matcher agent

- **Done when:** user scopes in chat, sees JSON fields populate live, tweaks in thread, confirms without a cold proposal page.



### N0b. DB production hardening — `cursor` ✅

- [x] Alembic migrations (`backend/alembic/`, baseline `0001_baseline`); Docker runs `alembic upgrade head` on boot

- [x] `create_all` gated behind `AUTO_CREATE_ALL` (dev/test only; prod uses migrations)

- [x] Connection pool: `pool_pre_ping`, sized pool, recycle (`app/db/session.py`)

- [x] Chat session ownership checks (403 on cross-client access)

- [x] `ai_decision_log` audit table (AI proposes; Spine decides)

- [ ] Replace `get_demo_client` stub with real JWT auth (`founder` decision on provider)



### N1. Bind gate #2 — full client journey on real API (scaffolding — superseded by N0 UX)

- Owner: `cursor` + `founder`

- [x] Merge v0 Stage 2 from `main` → `core` (4 screens + IntentForm)

- [x] Fix spec bind: `GET /specs/{spec_id}` for v0 proposal page (`useSpec(quote.spec_id)`)

- [x] `docker compose up -d --build` → API healthy

- [ ] `.env.local` with `NEXT_PUBLIC_USE_MOCKS=false` → browser smoke (API path verified; local/Vercel frontend bind pending)

- **Done when:** full Stage 2 journey works against Postgres without mock data.



### N2. Backend B2 — Spine integration tests

- Owner: `cursor`

- [x] State machines + EventWriter + unit tests

- [ ] Integration pytest with Postgres (Docker)

- **Done when:** pytest drives `blocked → ready → invited` with events in DB.



### N3. Stage 3 worker screens

- Owner: `v0` ← **NEXT v0 REQUEST** (see `docs/V0_HANDOFF.md` Stage 3)

- [ ] `/worker/onboarding` — profile wizard + completion meter (≥70% gate)

- [ ] `/worker` — task inbox (worker labels, priority countdown)

- [ ] `/worker/tasks/[taskId]` — charter, packet, submit, QA feedback

- **Done when:** worker journey clickable on mock data.



---



## 📋 NEXT (queued — start when NOW empties)



### X1. Backend B3 — core services (continued)

- Owner: `cursor`

- [ ] WorkerProfileService + `GET /workers/profile`, `GET /workers/me/tasks`

- [ ] Real JWT auth (replace demo client stub)

- [ ] `GET /orders/{id}/delivery`, discussion threads



### X2. Backend B4 — AI gateway + 4 agents (fixtures → Gemini)

- Owner: `cursor`

- [ ] AI gateway: schema validation, `ai_decision_log`, confidence gate

- [ ] Spec Compiler (fixture → Gemini structured output)

- [ ] Architect (DAG builder, acyclic validation)

- [ ] Matcher (filter + rank from DB profiles)

- [ ] QA Judge (deterministic checks + Gemini Vision)

- [ ] **Bind gate #3:** proposal card shows real AI-scoped spec



### X3. Bind gate #1 — catalog on real API (browser)

- Owner: `founder`

- [ ] Homepage SKU cards with `USE_MOCKS=false`



---



## 🔭 LATER (post-slice — do not start early)



- [ ] B5 vertical slice: pytest `intent → delivered` end-to-end (**S0 milestone**)

- [ ] Bind gate #4: flip `USE_MOCKS=false` globally in production

- [ ] WebSocket live tracker updates

- [ ] B6: CI (GitHub Actions), contract tests, run-slice script

- [ ] Admin console (verify workers, human queue, AI decision log)

- [ ] Mock ledger visuals (funds held / reserved / released states)

- [ ] Auth UI + session handling

- [ ] Deploy: Vercel (frontend) + Railway/Cloud Run (backend) for demo URL

- [ ] Demo script rehearsal + seed data for the 5-min story



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



---



## 📐 How to use this pipeline (all agents)



1. **Pick from NOW** — top item your lane owns. Don't cherry-pick from LATER.

2. **Announce** — before starting: scope, files, done-when test.

3. **Ship** — end with something runnable (pytest / curl / browser).

4. **Update this file** — tick boxes, move finished blocks to SHIPPED, promote NEXT → NOW when a slot frees.

5. **Blocked?** Mark `[!]` with a one-line reason and move on — don't idle.

6. **Scope creep?** New ideas go to LATER, not into the current sprint.



**Escalate to founder when:** contract shapes change, money/legal logic appears, v0 and core lanes collide, or a demo checkpoint slips.

