# Project Orchestra — Build Pipeline

> **Single source of truth for what to work on.** Every agent (Cursor, v0, human) reads this before starting and updates it after finishing. If it's not here, it's not planned; if you did it, mark it.
>
> **North star:** Production Outcome-as-a-Service — client **co-creates the OutcomeSpec in real time with Gemini** (chat + live spec panel), confirms quote, Spine executes plan/match/QA/delivery with live tracker updates. See `docs/SPEC_CO_CREATION.md`.
>
> **Current goal (set 2026-07-17): Close the campus harden gate, then pilot.** Code for the campus-ready chapter is shipped. What remains is **founder ops + a few product decisions**, not feature breadth.

**Legend:** `[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked / needs founder

**Owners:** `v0` = Vercel v0 on `main` · `cursor` = Cursor agents on `core` · `founder` = human decision

---

## Status snapshot (2026-07-17) — honest read

| Layer | Reality |
|-------|---------|
| **Product loop (code)** | Shipped end-to-end on live API: scope → quote → confirm → invite → work → deliver → accept |
| **Market features (code)** | Amendments, admin verify/taxonomy, reputation/media, email/Sentry, Razorpay **sandbox**, disputes/PM tick, RAG — all `[x]` |
| **Live stack** | Clerk + Cloud Run + Cloud SQL (`orchestra-trial-pg`) on **raystartup** + Vercel + Vertex — up (`/health` OK) |
| **What's actually left** | **Founder-gated ops** (prod smoke, gen-lang-client teardown when IAM allows); then pilot |
| **Billing** | raystartup trial → Run/SQL/Vertex Gemini; gen-lang-client ₹95.7k = Agent Builder only — `docs/GCP_BILLING_SPLIT.md` |
| **Payments** | Stay `PAYMENTS_ENABLED=false` until harden passes — sandbox ledger only |

**Chapter done when:** founder runs outcomes on prod without engineering babysitting; scope changes go through Amendments; admin verifies workers; real money stays off until harden is green.

---

## Proceed plan (do in this order)

### Gate 0 — Founder decisions (undecided today)

Resolve these so agents don't invent policy. Defaults in parentheses are the lean MVP choice if you want speed.

| # | Decision | Options / default | Blocks |
|---|----------|-------------------|--------|
| D1 | **Delete `raysql`?** | Yes (recommended — unused expensive MySQL leftover) vs keep | Cost only; not product |
| D8 | **Dual-account credit split** | Orchestra on **raystartup** (trial: Run/SQL/**Vertex Gemini**; never AI Studio). gen-lang-client = Agent Builder Search/Conversation only (₹95.7k) | `docs/GCP_BILLING_SPLIT.md` |
| D2 | **Warranty window** after delivery | e.g. 7 / 14 / 30 days (**default: 14**) | Dispute UX copy + timer policy later |
| D3 | **Revision limit defaults per SKU** | e.g. Launch Studio = 2 rounds (**default: 2**) | Quote/amendment expectations |
| D4 | **Workers see preference rank?** | Hide (**default**) vs show | Matcher / preferences UI |
| D5 | **Mutual start grain** | Per-milestone / per-task (**already leaning this**) vs per-order | Already implemented per-task — confirm freeze |
| D6 | **When to flip real Razorpay** | Only after Gate 1 green (**hard rule**) | Money / legal |
| D7 | **Pilot cohort** | Who are the first 5–10 clients + workers? | Concierge ops, not code |

Design-notes leftovers (D2–D5) live in `Project_Orchestra_Design_Notes.md` §20 — still open, not blocking Gate 1.

---

### Gate 1 — Harden the live campus loop (P0 — **NOW**)

Owner: `founder` (ops) · docs already written in `docs/DEPLOY_API.md`

- [x] Dual-account smoke checklist documented
- [x] Cloud Scheduler instructions for `POST /api/v1/internal/timers/tick` documented
- [x] Notifications UI (badge + list) on `WorkspaceHeader`
- [x] Browser smoke checklist documented
- [x] **Billing cutover (2026-07-17):** API on raystartup — https://orchestra-api-444869825431.us-central1.run.app; Vercel bound; Vertex + Clerk live
- [!] **Founder: run dual-account smoke on prod** (client + worker + admin `event_log` + notifications + ledger strip)
- [x] **Founder: Cloud Scheduler** `orchestra-timer-tick` on raystartup (5 min)
- [!] **Founder: delete gen-lang-client Orchestra infra** — blocked (no IAM on `gen-lang-client-0795401430` for `gagantak000@gmail.com`); owner must delete `orchestra-api`, `orchestra-pg`, confirm `raysql`

**Done when:** Non-engineer completes one full outcome on prod with two Clerk accounts; admin sees `event_log`; timers tick; **Orchestra bills on raystartup**; gen-lang-client has **no** Orchestra Cloud Run/SQL.

**Cursor role during Gate 1:** standby for bugs found in smoke only — no new features.

---

### Gate 2 — Campus pilot (ops, not sprints)

After Gate 1 is green:

1. Seed / verify real campus workers via `/admin` (`campus_verified`)
2. Run 3–5 concierge outcomes with invited clients (founder as PM if needed)
3. Log failure modes in `event_log` + a simple pilot notes doc
4. Keep payments sandbox; use ledger strip for trust narrative only
5. Fix only what breaks the loop (vertical slice > new SKUs)

**Done when:** ≥3 real outcomes closed on prod; founder can babysit less each time.

---

### Gate 3 — Next product chapter (only after Gate 1)

Do **not** start these until harden is green. Order matters:

| Order | Work | Owner | Notes |
|------|------|-------|-------|
| 1 | Production payments enablement | `founder` + `cursor` | Flip `PAYMENTS_ENABLED` + Razorpay live keys; keep double-entry; no silent money |
| 2 | Dispute UX polish + warranty timers | `cursor` + `v0` | Backend disputes exist; tighten after D2 |
| 3 | Email deliverability + templates QA | `cursor` | Resend already wired — harden templates for invites/delivery |
| 4 | Multi-SKU / catalog expansion | `founder` + `cursor` | Only if pilot demand is clear |
| 5 | TDS / payout productization | `founder` + `cursor` | Deferred until real payouts |
| 6 | Redis multi-instance WS fan-out | `cursor` | Only if multi-instance Cloud Run needed |
| 7 | Meilisearch / mobile | — | Explicitly deferred |

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
- Admin mutating actions unlocked (verify + taxonomy); disputes later polish.
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
- **Market sprints:** Amendments, admin ops, reputation/media, email/Sentry, payments sandbox, disputes/PM, RAG
- **Worker onboarding + delivery UX:** industry-grade profile capture; order tracker as delivery console

### LEFT (this chapter)

- Gate 1 founder ops (prod smoke, **gen-lang-client teardown when IAM allows**)
- Gate 0 product decisions D1–D8 (mostly policy; D5 already implemented; **D8 billing split is cost-critical**)
- Payments stay sandbox until Gate 1 green

### DEFERRED further

Mobile apps, Redis multi-instance WS fan-out, full TDS productization, Meilisearch, multi-vertical SKUs.

---

## Worker onboarding UX — industry-grade profile capture

- Owner: `cursor` (+ v0 polish later)
- [x] Replace demo wizard (prefilled Rohan + fake bank) with empty/hydrate form
- [x] Collect real contract fields: community, headline, task_types, availability, social links, payout range
- [x] Taxonomy pickers via `useSkills` / `useTools` / `useTaskTypes` (no invented IDs)
- [x] Per-step validation + live completion meter matching server formula (`lib/profile-completion.ts`)
- [x] `/join` explains what is collected and why; no fake bank promises
- [x] `/worker` inbox: live/not-live badge, profile CTA when &lt;70%, priority countdown
- **Done when:** Worker can go from `/join` → complete ≥70% → receive invites with matchable task_types

---

## Client + delivery UX polish

- Owner: `cursor`
- [x] Order tracker → delivery console (primary CTA, deliverables first-class, collapsed plan)
- [x] Proposal confirm: inline errors, funds story, stepper on `confirm`
- [x] My outcomes: next-action cards, compact progress (no full stepper per row)
- [x] Worker job card: stage banners, checklist-gated submit, discussion composer
- **Done when:** Client can review & accept delivery without hunting; worker submit path is clear

---

## SHIPPED (code chapters)

- [x] Role-true Orchestra (P0 RBAC, 2026-07-13)
- [x] Honest loop P1 (2026-07-13): no `_ensure_invited`; real notifications; event-driven ledger; durable timers
- [x] UX wiring finish (Plan E, 2026-07-13)
- [x] Alembic chain linear through `0016_project_templates`
- [x] Next Chapter Sprints 2–8 (2026-07-13): Amendments → admin → reputation/media → email → payments sandbox → disputes/PM → RAG
- [x] Planning docs, contract, Spine, S2 A–D, Clerk go-live, Cloud Run, WebSocket, CI, Scope Guard flag-only
- [x] Role model "D + Hybrid", branch model, V0 handoff, Stage 1–2 UI
- [x] Worker onboarding UX + client/delivery UX polish (2026-07-17)

### Founder-gated (not code)

- [!] Run prod dual-account smoke (`docs/DEPLOY_API.md` — Campus dual-account smoke checklist)
- [x] Billing cutover to raystartup (`docs/GCP_BILLING_SPLIT.md`, live API `444869825431`)
- [x] Cloud Scheduler `orchestra-timer-tick` on raystartup
- [!] Delete gen-lang-client `orchestra-api` / `orchestra-pg` / `raysql` — **IAM blocked**; needs project owner
- [!] Optional hygiene: rotate Clerk keys if they were ever pasted in chat

---

## How to use this pipeline (all agents)

1. **Pick from Gate 1 first** — unless founder already marked it green.
2. **Announce** — scope, files, done-when test.
3. **Ship** — runnable (pytest / curl / browser).
4. **Update this file** — tick boxes, move finished work to SHIPPED.
5. **Blocked?** Mark `[!]` with one-line reason.
6. **Scope creep?** Gate 3 items wait; do not expand catalog or enable live payments early.

**Escalate to founder when:** contract shapes change, money/legal logic appears, v0 and core lanes collide, or a stage checkpoint slips.
