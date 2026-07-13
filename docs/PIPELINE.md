# Project Orchestra — Build Pipeline

> **Single source of truth for what to work on.** Every agent (Cursor, v0, human) reads this before starting and updates it after finishing. If it's not here, it's not planned; if you did it, mark it.
>
> **North star:** Production Outcome-as-a-Service — client **co-creates the OutcomeSpec in real time with Gemini** (chat + live spec panel), confirms quote, Spine executes plan/match/QA/delivery with live tracker updates. See `docs/SPEC_CO_CREATION.md`.
>
> **Current goal (set 2026-07-13): "Campus-ready Orchestra."** P0 role-true + P1 honest loop shipped. Harden the live demo, then Spec Release-3 market features (amendments → admin → reputation/media → email → payments last).
>
> **Progress guide (human-readable architecture):** [`docs/CURRENT_ARCHITECTURE.md`](CURRENT_ARCHITECTURE.md) — master architecture, three portals, UI wiring/buttons, frameworks, shipped vs founder-open.

**Legend:** `[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked

**Owners:** `v0` = Vercel v0 on `main` · `cursor` = Cursor agents on `core` · `founder` = human decision

---

## THE GOAL (this chapter) — Campus-ready Orchestra

The full `intent → delivered` loop works on the live API with honest invites, event-driven ledger states, real notifications, and durable priority timers. Next: make the campus pilot boringly reliable, then unlock Amendment / admin ops / reputation / email / payments in sequence.

**Done when (chapter):** founder runs outcomes on prod without engineering babysitting; scope changes go through Amendments; admin verifies workers; payments stay sandbox until harden is green.

---

## P0 — Harden the live campus loop

- Owner: `cursor` + `founder` + `v0`
- [x] Dual-account smoke checklist documented in `docs/DEPLOY_API.md` (founder: run on prod)
- [x] Cloud Scheduler instructions for `POST /api/v1/internal/timers/tick` in `docs/DEPLOY_API.md` (founder: create job)
- [x] Notifications UI (badge + list) on `WorkspaceHeader`
- [x] Browser smoke checklist in `docs/DEPLOY_API.md`
- **Done when:** Non-engineer completes one outcome on prod with two accounts; admin sees `event_log`
- **Founder remaining:** actually run the checklist on Vercel + create Scheduler job + delete `raysql`

---

## The three lanes (product division)

| Lane | Who | Entry path | Portal home | Backend gate |
|------|-----|-----------|-------------|--------------|
| **Client** | buyer of outcomes | `/sign-in` → `/account` → *client* | `/orders` | `get_current_client` |
| **Worker** | verified talent | `/account` → *worker* (or `/join`) | `/worker` | `get_current_worker` |
| **Admin** | ops / founder | `/account` (only if admin claim) | `/admin` | `get_current_admin` |

**Lane rules (invariants):**

- Client **never** sees worker failure states — `rework` reads as "In progress" (`state-labels.ts`).
- Worker acts **only** on invited/assigned tasks; worker chat posts as worker.
- Admin mutating actions unlocked starting Sprint 3 (verify + taxonomy); disputes later.
- Admin role is **never** reachable via `PATCH /auth/role` — Clerk claim / allowlist only.

---

## Partition — where the whole repo actually stands

### DONE (real, on the live API)

- **Client loop:** scope chat → OutcomeSpec → quote → confirm → tracker → delivery accept
- **Honest invite:** preferences_set → invited required before accept (no `_ensure_invited` / backup padding)
- **Chat surfaces:** Gemini scope + pricing + matcher chat, SSE, `ai_decision_log`
- **Spine:** order/task state machines, `event_log`, durable Postgres timers, WebSocket tracker
- **Platform:** Clerk live, Cloud Run + Cloud SQL + Secret Manager, Vercel, CI, admin read console
- **Notifications:** event-projected invite / priority / QA / delivery
- **Ledger:** Held → Reserved → Released via confirm / mutual start / accept-delivery
- **UX shell:** WorkspaceHeader, JourneyStepper, framed CTAs, `/orders` home, Resume scope

### LEFT (this chapter)

- Harden remaining P0 items (prod dual-account smoke, Cloud Scheduler)
- Payments stay sandbox (`PAYMENTS_ENABLED=false`) until harden is green

### DEFERRED further

Mobile apps, Redis multi-instance WS fan-out, full TDS productization, Meilisearch, multi-vertical SKUs.

### Discovery Engine RAG (Agent Builder credits)

- [x] `google-cloud-discoveryengine` service + `POST /api/v1/knowledge/query` (2026-07-13)
- [ ] Wire Spec Compiler / support chat to prefer Discovery Engine when `DATA_STORE_ID` set
- Docs: [`DISCOVERY_ENGINE_RAG.md`](DISCOVERY_ENGINE_RAG.md)

---

## P1 — Amendments

- [x] Amendment contract + create from Scope Guard `scope_change_request`
- [x] Approve / reject + charter/spec versioning + `event_log`
- [x] UI: amendment card on discussion / tracker

---

## P2 — Admin ops → reputation/media → email → payments → disputes/PM → RAG

- [x] Admin worker verify + taxonomy CRUD; matcher verified-only
- [x] `worker_stats` + signed media uploads
- [x] Transactional email (Resend) + Sentry + AI quality view
- [x] Razorpay sandbox + double-entry ledger (after harden stable)
- [x] Disputes + PM control loop tick
- [x] RAG `project_templates` + Spec Compiler retrieve

**Payments rule:** Do not enable production Razorpay until P0 harden is green.

---

## SHIPPED

- [x] Role-true Orchestra (P0 RBAC, 2026-07-13)
- [x] Honest loop P1 (2026-07-13): no `_ensure_invited`; real notifications; event-driven ledger; durable timers
- [x] UX wiring finish (Plan E, 2026-07-13)
- [x] Alembic chain linear through `0016_project_templates` (amendments → worker_stats → ledger_entries → disputes → RAG)
- [x] Next Chapter Sprints 2–8 (2026-07-13): Amendments, admin ops, reputation/media, email/Sentry, payments sandbox, disputes/PM tick, RAG
- [x] Planning docs, contract, Spine, S2 A–D, Clerk go-live, Cloud Run, WebSocket, CI, Scope Guard flag-only
- [x] Role model "D + Hybrid", branch model, V0 handoff, Stage 1–2 UI

### Founder-gated (not code)

- [!] Confirm then `gcloud sql instances delete raysql` (cost cleanup — see `docs/DEPLOY_API.md`)

---

## How to use this pipeline (all agents)

1. **Pick from P0 first** — top item your lane owns.
2. **Announce** — scope, files, done-when test.
3. **Ship** — runnable (pytest / curl / browser).
4. **Update this file** — tick boxes, move finished work to SHIPPED.
5. **Blocked?** Mark `[!]` with one-line reason.
6. **Scope creep?** Later sprints, not current P0.

**Escalate to founder when:** contract shapes change, money/legal logic appears, v0 and core lanes collide, or a stage checkpoint slips.
