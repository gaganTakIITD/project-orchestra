# 🚀 Project Orchestra — Build Pipeline

> **Single source of truth for what to work on.** Every agent (Cursor, v0, human) reads this before starting and updates it after finishing. If it's not here, it's not planned; if you did it, mark it.
>
> **North star:** Production Outcome-as-a-Service — client **co-creates the OutcomeSpec in real time with Gemini** (chat + live spec panel), confirms quote, Spine executes plan/match/QA/delivery with live tracker updates. See `docs/SPEC_CO_CREATION.md`.
>
> **Current goal (set 2026-07-13): "Role-true Orchestra."** One Clerk login → three **correctly separated** portals (client / worker / admin) → one clean `intent → delivered` loop each role can run truthfully on the live API.

**Legend:** `[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked

**Owners:** `v0` = Vercel v0 on `main` · `cursor` = Cursor agents on `core` · `founder` = human decision

---

## 🎯 THE GOAL (this sprint) — Role-true Orchestra

The client `intent → delivered` loop already works on the live API. The gap is the **client / worker / admin split**: today it's one identity with a soft label, not three enforced lanes. This sprint makes the split **true**.

**Role model — decided 2026-07-13 ("D + Hybrid"):**

- **Client ↔ worker:** one Clerk account, **switchable active role**, DB-owned and self-serve via `PATCH /auth/role` + the portal hub (`/account`). Fits campus students who both buy and sell.
- **Admin:** **Clerk-claim owned** (`public_metadata.role=admin` or email allowlist) — **never** self-serve via `/auth/role`, gated even in demo mode.
- **`/auth/me` is the single source of truth** for the *effective* role (including admin), so the portal cards and the API stop disagreeing.
- **Real RBAC:** `get_current_client` / `get_current_worker` enforce the active role (403 on mismatch) instead of only resolving identity.

**Done when:** a client account scopes + confirms an order; a **separate** worker account accepts + submits; the client accepts delivery; an admin sees the full `event_log` trail — and each account is **blocked** from the other two's actions. Docs match code.

---

## 🔴 P0 — Make the three lanes true ⟵ **NOW**

- Owner: `cursor`
- [ ] **RBAC enforcement** in `get_current_client` / `get_current_worker` — clerk mode returns 403 on role mismatch; new Clerk users default to `client` (worker requires explicit switch)
- [ ] **`/auth/me` effective role** — reflect + persist admin from Clerk claims so portal cards and API agree
- [ ] **Admin lane wired** — portal card shows for effective admin; `get_current_admin` stays claim/allowlist-gated; demo-mode admin is explicit dev-only (not silently open in prod)
- [ ] **Fix worker discussion identity** — `POST /tasks/{id}/discussion` resolves client-or-worker so worker messages are attributed to the worker (not the client)
- [ ] **Worker-portal entry sets role** — `setRole('worker')` on portal-hub / onboarding entry so deep links don't 403
- [ ] **Reconcile docs** — this file + `SUBPLAN_S2_STAGES.md` + `DEPLOY_API.md`: Clerk auth is **LIVE**; drop the stale "founder-blocked on Clerk keys" line
- **Done when:** cross-role API calls 403; admin is reachable **and** visible in the portal; worker chat is attributed correctly; `cd backend && python -m pytest tests/test_auth.py tests/test_admin.py` + `npx tsc --noEmit` green

---

## 🧭 The three lanes (product division)

| Lane | Who | Entry path | Portal home | Backend gate |
|------|-----|-----------|-------------|--------------|
| **Client** | buyer of outcomes | `/sign-in` → `/account` → *client* | `/start` | `get_current_client` |
| **Worker** | verified talent | `/account` → *worker* (or `/join`) | `/worker` | `get_current_worker` |
| **Admin** | ops / founder | `/account` (only if admin claim) | `/admin` | `get_current_admin` |

**Lane rules (invariants):**

- Client **never** sees worker failure states — `rework` reads as "In progress" (`state-labels.ts`).
- Worker acts **only** on invited/assigned tasks; worker chat posts as worker.
- Admin is **read-only** audit for now (orders, `event_log`, `ai_decision_log`); no mutating admin actions until P2.
- Admin role is **never** reachable via `PATCH /auth/role` — Clerk claim / allowlist only.

---

## 📦 Partition — where the whole repo actually stands

### ✅ DONE (real, on the live API)

- **Client loop:** scope chat → live OutcomeSpec → quote → confirm → tracker → delivery accept (Stages A–C, `NEXT_PUBLIC_USE_MOCKS=false`)
- **Chat surfaces:** Gemini scope + pricing + matcher chat, SSE streaming, `ai_decision_log` audit
- **Spine:** order/task state machines, `event_log`, durable timer stub, WebSocket live tracker
- **Data:** Postgres + Alembic migrations, pooled sessions, ownership checks (403 cross-client)
- **Worker:** onboarding persists to `worker_profiles`, lifecycle (accept → ready → submit → QA → rework), matcher reads DB profiles
- **Platform:** Clerk login **live**, Cloud Run + Cloud SQL + Secret Manager, Vercel prod, CI (pytest + tsc), read-only admin console, notifications stub + ledger strip

### 🔧 LEFT (incomplete or inconsistent)

- **P0 — role separation** (see above): RBAC, admin pathway, `/auth/me` effective role, worker chat identity, doc reconciliation
- **P1 — honest loop:** real matcher → preference → invite (retire `_ensure_invited` bootstrap + `usr_worker_backup_*` padding); real notifications (retire empty stub); ledger states tied to real events
- **UX wiring (v0):** build the workspace shell per `docs/UX_WIRING.md` §8 — `WorkspaceHeader` + per-portal layouts, client `/orders` dashboard (client home), `JourneyStepper`, framed "Assemble team" + "Accept delivery", optional "Resume scope". Contract glue already shipped (see below).
- **Cleanup:** `SUBPLAN`/`DEPLOY` auth wording contradicts shipped Clerk state

### ⛔ DEFERRED (do not start early — P2+)

real payments / money movement, disputes UI, `Amendment` approve/reject, PM autonomy loop, admin worker-verify + taxonomy CRUD, RAG flywheel, email product, mobile apps, Redis multi-instance WS fan-out.

---

## 🟠 P1 — Make the loop honest end-to-end (NEXT — start when P0 empties)

- Owner: `cursor`
- [ ] Real matcher → preference → invite flow (retire `_ensure_invited` auto-invite bootstrap and backup padding)
- [ ] Notifications: emit real events (invite / priority window / QA result / delivery) — retire the empty stub
- [ ] Surface ledger states (Held → Reserved → Released) driven by actual lifecycle events, not display-only

---

## 🟢 P2 — Deferred (post-slice)

- [ ] Amendment approve/reject flow (Scope Guard is flag-only today)
- [ ] Admin mutating actions (worker verify, taxonomy CRUD, dispute triage)
- [ ] Pricing confirm chat + spec undo (Track F stretch)
- [ ] Payments integration, disputes, PM control loop, RAG flywheel

**Explicitly out of scope (don't build):** real payments, TDS math, disputes UI, PM control loop, RAG flywheel, email product, mobile apps, Redis multi-instance WS fan-out.

---

## ✅ SHIPPED

- [x] **Role model decision (2026-07-13):** "D + Hybrid" — one account switch client↔worker (DB, self-serve), admin via Clerk claim only, `/auth/me` = source of truth, real RBAC (this pipeline reframed around it)
- [x] Planning docs (design notes, tech spec, master plan, diagrams)
- [x] Repo: Next.js 16 at root, v0-compatible, GitHub `gaganTakIITD/project-orchestra`
- [x] Branch model: `main` = v0 UI · `core` = contract + backend
- [x] Shared contract: `lib/types.ts`, `mock-data.ts`, `api.ts`, `hooks.ts`, `state-labels.ts`
- [x] Design tokens + `docs/V0_HANDOFF.md`
- [x] Stage 1 homepage refresh (v0 — Lumena/Bauhaus redesign, Framer Motion, a11y pass)
- [x] **Stage 2 client workflow (v0)** — `/start`, `/proposal/[quoteId]`, `/orders/[orderId]`, preferences; IntentForm + hooks wired; deployed on `main`
- [x] **Scope chat page** — `/scope/[sessionId]` + SSE (v0 on `main`; live on Vercel)
- [x] B2 Spine code: state machines, event_log, TaskSpine/OrderSpine, timer stub, pytest
- [x] B3 slice: auth stub, intent/quote/order API, fixture spec compiler, client hooks
- [x] B3 fulfillment: Architect fixture plan, milestones/candidates/preferences API
- [x] Agent framework: `AGENTS.md` playbook + `.cursor/rules/` (frontend contract, backend spine)
- [x] **S2 Stages A–C:** worker lifecycle, discussion, delivery accept, product smoke (`SUBPLAN_S2_STAGES.md`)
- [x] **Stage D (Cursor slice):** Clerk auth **live** + Gemini gate + DB matcher + onboarding + Cloud Run/Vercel bind
- [x] **Cloud Run API + Secret Manager hygiene** (2026-07-13) — see `docs/DEPLOY_API.md`
- [x] **WebSocket live tracker** — EventBus + `/ws/orders/{id}` + `/ws/tasks/{id}`; `lib/live.ts` invalidation; order + worker pages subscribed
- [x] **Scope Guard (flag-only)** — discussion `scope_flagged` / `scope_change_request`; badges on order + worker threads (no Amendment API)
- [x] **B6 CI** — `.github/workflows/ci.yml` (pytest + tsc) + run-slice scripts
- [x] **Admin console (read-only)** — `/admin` + `GET /admin/orders`, events, AI decisions
- [x] **Notifications stub + ledger strip** — `GET /notifications` (empty OK); `LedgerStrip` on order tracker (Held → Reserved → Released)
- [x] **Clerk go-live** — Vercel + Cloud Run `AUTH_MODE=clerk` (`arriving-serval-22`; revision `orchestra-api-00024-krv` — see `DEPLOY_API.md`)
- [x] **UX Wiring Framework + contract glue (2026-07-13)** — `docs/UX_WIRING.md` (IA + two app-shells + per-lane journey state machines + screen inventory + v0 handoff). Glue: `GET /orders` + `useMyOrders`, `lib/journey.ts` stepper map, `GET /chat/sessions` + `useMyScopes` (resume scope). `test_orders_list.py` + `test_chat_sessions_list.py` green; `tsc --noEmit` clean

### Founder-gated (not code)

- [!] Confirm then `gcloud sql instances delete raysql` (cost cleanup; MySQL leftover — see `docs/DEPLOY_API.md`)

---

## 📐 How to use this pipeline (all agents)

1. **Pick from P0 first** — top item your lane owns. Don't cherry-pick from P1/P2.
2. **Announce** — before starting: scope, files, done-when test.
3. **Ship** — end with something runnable (pytest / curl / browser).
4. **Update this file** — tick boxes, move finished blocks to SHIPPED, promote P1 → P0 when a slot frees.
5. **Blocked?** Mark `[!]` with a one-line reason and move on — don't idle.
6. **Scope creep?** New ideas go to P2, not into the current sprint.

**Escalate to founder when:** contract shapes change, money/legal logic appears, v0 and core lanes collide, or a stage checkpoint slips.
