# 🚀 Project Orchestra — Build Pipeline

> **Single source of truth for what to work on.** Every agent (Cursor, v0, human) reads this before starting and updates it after finishing. If it's not here, it's not planned; if you did it, mark it.
>
> **North star:** the 5-minute hackathon demo — client types intent → AI scopes + prices → confirms → AI builds task plan → worker accepts + submits → Gemini QA passes → client sees milestone complete live.

**Legend:** `[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked
**Owners:** `v0` = Vercel v0 on `main` · `cursor` = Cursor agents on `core` · `founder` = human decision

---

## 🎯 NOW (current sprint — do these first)

### N1. Verify backend B1 runtime + bind gate #1 (catalog)
- Owner: `cursor` + `founder`
- [!] Start Docker Desktop (founder — **still blocked**)
- [ ] `docker compose up -d --build` → all 4 services healthy
- [ ] `curl localhost:8000/api/v1/catalog/skus` returns 3 seeded SKUs
- [ ] `.env.local` with `NEXT_PUBLIC_USE_MOCKS=false` → homepage catalog renders from Postgres
- [ ] Commit + push B1 to `core`
- **Done when:** homepage SKU cards load from the real API in the browser.

### N2. Backend B2 — The Spine (state machines)
- Owner: `cursor`
- [x] `event_log` model + EventWriter (same-transaction)
- [x] Order + Task transition maps per Tech Spec §5
- [x] TaskSpine + OrderSpine services
- [x] pytest: legal/illegal transitions (pure graph tests ✅)
- [x] In-memory timer stub (Redis worker in B5)
- [ ] Integration pytest with Postgres (needs Docker)
- **Done when:** pytest drives `blocked → ready → invited` with events in DB.

### N3. Stage 2 client screens (UI shells on mocks)
- Owner: `v0`
- [ ] `/proposal/[quoteId]` — spec + quote card (per `docs/V0_HANDOFF.md` spec)
- [ ] `/orders/[orderId]` — milestone tracker (client labels only)
- [ ] `/orders/[orderId]/preferences/[taskId]` — pick ≥3 workers
- [ ] Wire `/start` form to `clientApi.createIntent` → route to proposal
- **Done when:** full client journey clickable on mock data.

---

## 📋 NEXT (queued — start when NOW empties)

### X1. Backend B3 — core services + bind gate #2
- Owner: `cursor`
- [ ] Auth (register/login/JWT) + `/auth/me`
- [ ] IntentService → `POST /intents` (emits `IntentCaptured`)
- [ ] QuoteService (deterministic price formula from SKU band)
- [ ] OrderService (accept quote → freeze spec → `OrderConfirmed`)
- [ ] WorkerProfileService + completion %
- [ ] **Bind gate #2:** `/start` → real intent → real proposal page

### X2. Backend B4 — AI gateway + 4 agents (fixtures → Gemini)
- Owner: `cursor`
- [ ] AI gateway: schema validation, `ai_decision_log`, confidence gate
- [ ] Spec Compiler (fixture → Gemini structured output)
- [ ] Architect (DAG builder, acyclic validation)
- [ ] Matcher (filter + rank from DB profiles)
- [ ] QA Judge (deterministic checks + Gemini Vision)
- [ ] **Bind gate #3:** proposal card shows real AI-scoped spec

### X3. Stage 3 worker screens
- Owner: `v0`
- [ ] `/worker/onboarding` — profile wizard + completion meter (≥70% gate)
- [ ] `/worker` — task inbox (worker labels, priority countdown)
- [ ] `/worker/tasks/[taskId]` — charter, packet, submit, QA feedback

---

## 🔭 LATER (post-slice — do not start early)

- [ ] B5 vertical slice: pytest `intent → delivered` end-to-end (**S0 milestone**)
- [ ] Bind gate #4: flip `USE_MOCKS=false` globally
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
- [x] B2 Spine code: state machines, event_log, TaskSpine/OrderSpine, timer stub, pytest (5 pass)
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
