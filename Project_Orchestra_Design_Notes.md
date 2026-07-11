# Project Orchestra — Design Notes & Decisions

> **What this document is:** A structured archive of the full design conversation for Project Orchestra, our AI-native Outcome-as-a-Service platform for the Gemini X Prize. Written so any team member (or future-us) can read it top to bottom and understand the concept, the model, the workflows, the backend, and the AI automation strategy.
>
> **Status:** Design / pre-build. Legal, tax, and payment sections need professional validation before handling real money.
>
> **Related files:**
> - `Project_Orchestra_Framework.docx` — original vision document
> - `canvases/project-orchestra-real-market-model.canvas.tsx` — interactive real-market model (open beside chat in Cursor)

---

## Table of Contents

1. [Core Concept](#1-core-concept)
2. [The Two IIT Delhi Communities](#2-the-two-iit-delhi-communities)
3. [Gemini X Prize Alignment](#3-gemini-x-prize-alignment)
4. [What "AI-Native" Actually Means](#4-what-ai-native-actually-means)
5. [Outcome-as-a-Service (OaaS) Model](#5-outcome-as-a-service-oaas-model)
6. [Preference & Acceptance Models](#6-preference--acceptance-models)
7. [Mutual Start & Trust](#7-mutual-start--trust)
8. [Later Discussion & Scope Control](#8-later-discussion--scope-control)
9. [Client Workflow](#9-client-workflow)
10. [Worker Workflow](#10-worker-workflow)
11. [How the Two Workflows Connect](#11-how-the-two-workflows-connect)
12. [Backend Vocabulary (Entities)](#12-backend-vocabulary-entities)
13. [Non-Negotiable Backend Rules](#13-non-negotiable-backend-rules)
14. [Money, Trust & Safety](#14-money-trust--safety)
15. [AI Automation Architecture](#15-ai-automation-architecture)
16. [Model Refinements That Enable Automation](#16-model-refinements-that-enable-automation)
17. [Gemini Implementation Map](#17-gemini-implementation-map)
18. [Worker Profile / Marketplace Data (Research)](#18-worker-profile--marketplace-data-research)
19. [Go-to-Market & Rollout](#19-go-to-market--rollout)
20. [Open Questions & Next Steps](#20-open-questions--next-steps)

---

## 1. Core Concept

Project Orchestra is an **AI-native Outcome-as-a-Service (OaaS) platform**. The client does not hire freelancers or manage a project. They **buy a clearly defined result** — for example, a brand identity plus a landing page — for a fixed price, fixed deadline, and clear definition of "done."

The platform takes full responsibility for planning the work, finding the right people, managing handoffs, checking quality, and delivering the final result. **AI (Gemini) acts as the general contractor**; IIT Delhi design and tech students act as the workforce.

- The **client** speaks in **outcome / milestone** language.
- The **worker** speaks in **task** language.
- A single backend keeps both views in sync.

**One-line promise:** *"Tell us the result you need. We deliver it — planned, staffed, verified, and handed over."*

---

## 2. The Two IIT Delhi Communities

The initial supply of talent comes from two campus communities:

| Community | Role | Typical work |
|-----------|------|--------------|
| **Tech** (DevClub-style) | Web apps, backend, AI/ML | React/Next.js, Node/Python, FastAPI, ML models, deployment |
| **Design** (Design Club-style) | Alternative to a design studio | Branding, UI/UX, Figma, graphics, pitch decks |

**Common campus stack (from research):**
- **Frontend:** React, Next.js, Vue, Vite, Tailwind CSS, TypeScript
- **Backend:** Node.js/Express/NestJS or Python (Django/FastAPI/Flask)
- **Databases:** MongoDB, PostgreSQL
- **AI/ML:** PyTorch, TensorFlow, sklearn, LangChain, RAG pipelines
- **Design:** Figma, Canva
- **Tooling:** Git, Docker, Vercel

Having both communities means the full pipeline (design → build → deploy) exists in-house.

---

## 3. Gemini X Prize Alignment

The platform is a strong entry under **Entrepreneurship & Job Creation / Small Business Services** because:

- **AI-native operations:** the core value is impossible without orchestrated LLM reasoning (scoping, routing, QA).
- **Human potential unleashed:** removes the project-management barrier for founders and small businesses.
- **Job creation:** delivers actionable tasks directly to student workers — no bidding, no cover letters.
- **Measurable traction:** a constrained campus MVP can show a live transaction loop within a compressed timeline.

---

## 4. What "AI-Native" Actually Means

AI-native means **the buyer buys an outcome and AI owns the workflow end to end** — not a chatbot on a freelance board.

**It IS:**
- User states intent → AI scopes into a task graph (DAG)
- AI assigns tasks to Design/Tech squads
- AI manages dependencies, deadlines, handoffs
- AI verifies deliverables before the next step unlocks
- AI re-plans when someone drops or quality fails

**It is NOT:**
- Gemini only writing the project brief
- AI only "suggesting" freelancers
- Humans still coordinating each other over WhatsApp

**Key point:** AI-native does not mean "no humans." Designers design, developers code — **Gemini orchestrates.**

---

## 5. Outcome-as-a-Service (OaaS) Model

### The shift: matching → outcome

- **Matching model (weak):** post job → browse profiles → pick people → manage discussion → chase delivery.
- **OaaS model (target):** describe result → platform quotes one outcome package → confirm → platform delivers by deadline.

### What the client buys — the Outcome Package

1. **Outcome statement** — one sentence of what "done" means
2. **Deliverables** — concrete artifacts received
3. **Acceptance criteria** — measurable pass/fail evidence
4. **In-scope / out-of-scope** — the boundary
5. **Fixed price** — one upfront price
6. **Timeline** — delivery commitment / milestones
7. **Revision & warranty policy**
8. **Single accountability** — the platform / AI contractor

### Critical correction

Sell **controllable, verifiable delivery outcomes** ("a production-ready landing page meeting agreed criteria"), **not** uncontrollable business results ("double your revenue"). Business KPIs can be a shared target or bonus — never the unconditional guarantee.

### Three commercial products (not one universal promise)

- **Catalog Outcome** — standardized, repeatable, objective acceptance (fixed price/SLA)
- **Configured Outcome** — standard package + bounded priced options
- **Discovery-to-Outcome** — ambiguous/high-risk requests buy a paid discovery sprint first, then a fixed proposal

### Seed SKUs

- **Design:** Brand Starter, UI Sprint, Fest Creative Kit
- **Tech:** Landing Launch, API + Dashboard MVP, AI Feature Add-on
- **Combined (the wedge):** Launch Studio (brand + UI + landing + deploy), Event Ops Pack, Pitch Ready

---

## 6. Preference & Acceptance Models

The client picks **at least 3 preferred workers** (ranked P1, P2, P3) from an AI-recommended shortlist. Two ways to run the offer:

### Model 1 — Sequential offer
Only one worker sees the offer at a time. P1 first; if they reject/expire, it goes to P2, then P3. Clean but slow; good workers may never see it.

### Model 2 — Parallel accept, priority start (CHOSEN DEFAULT)
- All 3 preferred workers can **accept interest in parallel**.
- Accepting = "I'm available," **not** "I'm working."
- **P1 gets first right to start** within a time window.
- If P1 doesn't **start** in the window, priority passes to the next **already-accepted** backup — no reposting.
- If none start → re-shortlist or open pool.

**Principle:** *Anyone can accept interest; only priority (then backups in order) can start; start is mutual.*

---

## 7. Mutual Start & Trust

**Trust is earned and locked at the moment work mutually starts** — when both sides explicitly commit.

- **Worker action:** "Ready to Start"
- **Client/platform action:** "Confirm & Start Together"
- Only then → status `mutually_started`

**What activates at mutual start:**
1. **Charter frozen** — scope, deliverables, deadline, price, revision limit, out-of-scope
2. **Payout reserved** in ledger
3. **Scoped chat opens** (not before)
4. **Delivery timer starts**
5. Identity / campus-verified / portfolio / past-completion visible to both

**Trust states (low → high):**
`preference_selected` → `accepted_interest` → `priority_active` → `start_requested` → **`mutually_started`** (trust layer ON) → `submitted` → `qa_passed`/`completed`

**Principle:** *Interest ≠ trust. Mutual start = the contract moment.*

---

## 8. Later Discussion & Scope Control

After mutual start, chat opens — but it is a **task-bound room**, not open negotiation.

**Allowed:** clarifications, references/files, WIP feedback within revision limit, checkpoint approvals.

**Not allowed without an Amendment:** new deliverables, silent deadline/price changes, unlimited revisions.

**Mechanisms:**
- **Task Charter pinned** at top of chat (immutable source of truth)
- **Scope-tagged messages:** `clarification`, `reference`, `scope_change_request`, `delivery_update`
- **AI Scope Guard** flags drift and proposes a formal amendment
- **No silent edits** — changes create versioned `Amendment #1`, `#2`, …
- **Revision boundary** — e.g. 2 rounds included; beyond that needs amendment
- **Structured delivery** — final submission via a Submit button, not chat links

**Principle:** *Discussion builds trust through clarity; amendments change scope. Free conversation, always anchored to the frozen job description.*

---

## 9. Client Workflow

**Phases:** Describe → Confirm → Ground (preferences) → Watch → Accept.

1. **Describe:** states goal in chat → `Intent` created, `OutcomeSpec` drafted
2. **Proposal:** reviews outcome card → `Quote` → `OutcomeOrder (confirmed)`
3. **Fund:** authorizes milestone funds → `Ledger: FUNDS_AUTHORIZED`
4. **Ground:** ranks ≥3 preferences → `PreferenceSet` stored
5. **Watch:** live milestone tracker; scoped chat; approves amendments
6. **Accept:** reviews Delivery Bundle → `OutcomeOrder (delivered → closed)`

The client mostly **watches progress**, not manages people. Internal failures (rework) are hidden — they see a smooth "in progress."

### Client-facing order states
`Describing → Proposal → Confirmed → AssemblingTeam → InProgress → (Clarifying / AmendmentReview) → Delivered → Closed`

---

## 10. Worker Workflow

**Phases:** Build Profile → Get Matched → Show Interest → Get Priority → Mutual Start → Execute → Get Paid.

1. **Onboard:** skills, tools, task types, portfolio → `WorkerProfile`, `completion %`
2. **Go live:** set available + hours → enters matching pool (needs ≥70% completion)
3. **Invited:** receives offer as a preference → task `INVITED`
4. **Interest:** accepts (parallel) → `INTEREST_POOL`
5. **Priority:** gets window → `PRIORITY_ACTIVE` → taps Ready to Start → `START_REQUESTED`
6. **Mutual start:** confirmed → `Charter` frozen, `MUTUAL_START`, payout reserved
7. **Execute:** does work, uploads → `Submission`, `SUBMITTED`
8. **QA:** pass → `COMPLETED`; fail → `REWORK` (within revision limit)
9. **Paid:** `Payout` (minus TDS), stats + portfolio updated

### Worker per-task states
`INVITED → ACCEPTED_INTEREST → (BACKUP_WAITING | PRIORITY_ACTIVE) → START_REQUESTED → MUTUAL_START → IN_PROGRESS → SUBMITTED → (REWORK ↔ SUBMITTED) → COMPLETED → PAID` (plus `RELEASED`, `EXPIRED`, `DECLINED`)

---

## 11. How the Two Workflows Connect

The client view and worker view are **two languages describing the same backend `Task` object.** That object holds state, acceptance criteria, payout, deadline, and assigned worker.

| Backend Task state | Client sees | Worker sees |
|--------------------|-------------|-------------|
| `READY` | "Assembling team" | "New offer available" |
| `MUTUAL_START` | "Delivery started" | "Charter locked, begin work" |
| `SUBMITTED` | "In progress" | "Submitted, under review" |
| `REWORK` | "In progress" (failure hidden) | "Fix checklist" |
| `COMPLETED` | "Milestone done" | "Passed + paid" |
| `delivered` | "Ready to accept" | (task closed) |

**Money and progress only advance when QA passes.**

---

## 12. Backend Vocabulary (Entities)

| Term | Meaning |
|------|---------|
| `OutcomeSKU` | Catalog template of a sellable outcome |
| `OutcomeSpec` | Frozen definition of "done" (deliverables + acceptance criteria) |
| `Quote` | Priced, time-bound proposal from intent |
| `OutcomeOrder` | Confirmed contract between client and platform |
| `Charter` | Immutable snapshot of scope/price/deadline at start |
| `Amendment` | The only legal way to change a Charter |
| `FulfillmentPlan` | Internal DAG of tasks to deliver the order |
| `Task` (DAG node) | One unit of work with its own acceptance check |
| `PreferenceSet` | Client's ranked list of preferred workers |
| `Interest` | Worker's parallel "I'm available" signal |
| `Activation` | Priority grant to one worker to start |
| `MutualStart` | Both sides confirm → work + payout lock |
| `Submission` | Structured deliverable upload |
| `QAReview` | Evidence-based pass/fail decision |
| `Ledger` | Double-entry record of all money movement |
| `Payout` | Release of funds to a worker after acceptance |
| `EventLog` | Append-only audit of every state change |

### Bounded-context domains
Identity & trust · Catalog & quoting · Orders & contracts · Fulfillment · Delivery & quality · Money · Communication · Risk & support.

---

## 13. Non-Negotiable Backend Rules

1. **`OutcomeSpec` is frozen at confirm** — only an `Amendment` can change it.
2. **Chat never mutates contract state** — all changes go through structured actions.
3. **Timers are durable jobs** (queue/workflow engine), never in-memory sleeps.
4. **Every money movement is double-entry** — no balance without balanced entries.
5. **Every consequential state change writes to `EventLog`** with actor + reason.
6. **A task has one `MUTUAL_START` worker** — backups stay reserved, never active.
7. **Payout releases only after QA pass + acceptance rule** — auto-accept on client silence is allowed but logged.

---

## 14. Money, Trust & Safety

### Money flow (ledger states)
`FUNDS_AUTHORIZED → MILESTONE_RESERVED → WORKER_PAYABLE → TDS_DEDUCTED → PAYOUT_RELEASED`
Branches: `REFUND_PENDING → REFUNDED`, `DISPUTE_HOLD → (WORKER_PAYABLE | REFUND_PENDING)`

- Use a **licensed payment/marketplace partner** — do not informally hold customer funds or casually call an internal wallet "escrow."
- Maintain an **immutable double-entry ledger** internally.

### Payment policy by order shape
- **Small catalog:** 100% funded before start; release after verified delivery; auto-accept if client silent
- **Multi-milestone:** first milestone + authorization schedule; release per accepted milestone
- **Discovery sprint:** 100% upfront; acceptance doesn't imply delivery quote
- **Amendment:** additional amount funded before changed work

### Trust system (evidence + remedies)
Verified identities · frozen versioned scope · milestone funding · visible progress + backups · objective quality evidence · neutral dispute process. Reputation is **task-type-specific and complexity-adjusted**, not a single star rating; workers can appeal automated signals.

### Compliance boundary (India, needs professional validation)
- **Tax:** e-commerce operator TDS obligations (Income Tax Act 2025, **Section 393(1) Sl. 8(v)**, 0.1% on gross, ₹5 lakh threshold for individuals with PAN/Aadhaar) — build a ledger-grade settlement engine from day one.
- **Privacy (DPDP Act 2023 / Rules 2025):** platform is a **Data Fiduciary** — purpose-specific consent, security safeguards (encryption/masking/tokenisation), access/correction/erasure rights, grievance redressal, breach response.
- **Worker classification:** "outcome-based" does not automatically remove employment risk — avoid excessive control over schedule/methods/exclusivity; get India-specific legal advice.

> These are product-architecture notes, **not** legal/tax advice. Validate with Indian counsel + a chartered accountant before handling real money.

---

## 15. AI Automation Architecture

### The golden rule — two kinds of automation
1. **Process automation** → deterministic **state machine** (state transitions, timers, unlocking, payouts). Never an LLM.
2. **Reasoning automation** → **Gemini** (intent, scoping, pricing inputs, matching, QA judgment, scope detection).

**Architecture:** a deterministic **spine** (orchestrator/state machine) that calls AI **reasoning nodes** at defined decision points. **AI proposes; the spine enforces and records.**

### AI reasoning nodes (where AI plugs in)

| Stage | AI node | Reads | Outputs | Guardrail |
|-------|---------|-------|---------|-----------|
| Intent → spec | **Spec Compiler** | raw intent + references | schema-valid `OutcomeSpec` w/ task-types | must validate; missing → ask, don't hallucinate |
| Feasibility | **Risk Classifier** | spec | risk tier + feasibility | high-risk → discovery/human |
| Pricing | **Pricing Reasoner** | spec + history | *estimates* effort/complexity/rework | deterministic function sets final price within band |
| Plan | **Architect** | spec | task DAG | must be acyclic; every node has criteria + type |
| Matching | **Matcher (retrieve + rerank)** | task + profiles | ranked shortlist + rationale | eligible/available only; rationale logged |
| Mutual start | **Task Packet Generator** | charter | brief + checklist + opening message | derived from frozen charter |
| Discussion | **Scope Guard** | each chat message | clarification vs scope-change | proposes amendment; can't change charter |
| Submission | **QA Judge** | deliverable + criteria | pass/fail + confidence | deterministic checks first; prod-software needs human approver |
| Continuous | **PM Control Loop** | all active orders | risk alerts + replan proposals | executes only within policy |
| Flags | **Dispute/Anomaly Triage** | evidence package | structured summary + recommendation | never issues final refund/ban |

---

## 16. Model Refinements That Enable Automation

1. **Machine-checkable acceptance criteria** — each criterion has a `check_type`: `deterministic` (auto-verify), `ai_judged` (Gemini rubric), or `human_required`. Turns QA into an executable contract. *(Highest leverage.)*
2. **Task-type ontology** — a controlled vocabulary (logo_design, figma_ui, landing_page_frontend, …) shared by scoping, matching, pricing, QA. Each type has default deliverables, criteria, effort, QA rubric.
3. **Confidence + rationale on every AI decision** — enables **confidence-gated autonomy**: raise thresholds as data proves reliability, so autonomy grows without a rewrite.
4. **Continuous PM control loop** — add a time-driven loop (not just event-driven) that monitors risk and intervenes early. The showpiece of autonomy.
5. **Explicit data flywheel** — every completed outcome feeds pricing (actual vs estimate), QA rubrics (pass/fail patterns), matching (rerank outcomes), and RAG templates. Gets smarter with every job.
6. **Humans as an explicit tier** — per decision: AI-alone / AI-proposes-human-approves / human-only. Money, bans, regulated judgments, prod-software sign-off stay human.

---

## 17. Gemini Implementation Map

| Capability | Where used |
|------------|------------|
| **Structured output + function calling** | Spec Compiler, Architect (schema-valid specs & DAGs) |
| **Embeddings** | Matcher retrieval (profiles + tasks → vectors) |
| **Reranking reasoning** | Matcher shortlist with rationale |
| **Gemini Vision** | QA of design deliverables (logos, UI, creatives) |
| **Long-context reasoning** | QA of code/copy vs acceptance criteria |
| **Fast classification** | Scope Guard on message stream |
| **Reasoning over state + history** | PM control loop interventions |
| **RAG over past projects** | Grounding for scoping, pricing, QA templates |

### Recommended build order (max leverage)
1. **Spec Compiler + checkable acceptance criteria** (everything depends on it)
2. **Deterministic + AI QA split** (verified handoffs = core promise)
3. **Matcher rerank**
4. **PM control loop** (demo showpiece)
Pricing & dispute triage stay semi-manual until data makes them safe to automate.

---

## 18. Worker Profile / Marketplace Data (Research)

### Patterns across Upwork / Fiverr / Contra / Toptal
Identity + trust → structured skills → portfolio proof → availability + rate → performance history → social proof links.

### Copy vs skip vs add
- **Copy:** structured skills w/ proficiency, portfolio w/ tags + outcome, availability status, headline + bio, proof links (GitHub/Figma/Behance/LinkedIn), post-project performance metrics.
- **Skip (MVP):** Fiverr-style gig packages, proposals/cover letters, heavy KYC, hourly bidding.
- **Add (AI-native + campus):** `community_type`, `task_types`, `tools`, `weekly_hours_available`, `max_concurrent_tasks`, `campus_verified`, `embedding_vector`.

### Profile layers
- **Layer 1 (signup):** name, email, photo, community_type, headline, bio, availability, campus_verified + skills + tools
- **Layer 2 (matchable):** task_types, hours, concurrency, payout range, portfolio (≥1), links, languages
- **Layer 3 (post-task):** tasks_completed, on_time_pct, avg_qa_score, avg_rating, response_time, seller_level

### Match score (v1)
`task_type 40% + skills/tools 25% + availability 20% + qa_history 10% + on_time 5%`
Only workers at **≥70% profile completion** enter the matching pool.

---

## 19. Go-to-Market & Rollout

Phased, with promotion gates — only advance when the previous phase proves on-time delivery at positive margin.

| Phase | Market boundary | What's real | Promotion gate |
|-------|-----------------|-------------|----------------|
| 0 — Concierge pilot | IITD, one SKU, invited | Real charter/delivery; manual ops behind UI | 10+ outcomes; failure taxonomy understood |
| 1 — Managed campus | 3–5 catalog outcomes | Payments, ledger, QA, disputes | ≥90% on-time; positive CM after rework |
| 2 — Delhi startup wedge | Verified SMB/startups | KYB, contracts, support SLA, warranty | Repeat rate; low critical-dispute rate |
| 3 — Vertical expansion | Selected digital categories | Specialist QA + category policies | Each SKU independently profitable |
| 4 — Geographic scale | Broader supply/demand | Tax/localization, fraud ops, governance | Ops stable without founder intervention |

**Recommended wedge:** one controllable combined outcome — a **launch-ready brand + landing page**. Exclude custom backends, regulated data, and performance marketing until data proves pricing/QA/recovery assumptions.

---

## 20. Open Questions & Next Steps

### Immediate next artifacts (pick one to start coding)
1. **`OutcomeSpec` schema + machine-checkable acceptance criteria + task-type ontology** — the foundation everything depends on.
2. **FastAPI endpoint contract** for the client + worker journeys.
3. **SQL schema** for `OutcomeOrder`, `Task`, `PreferenceSet`, `Interest`, `Charter`, `Ledger`.
4. **AI control-loop** detailed design.

### Open questions to resolve
- Mutual start **per-milestone** vs **per-order** (leaning per-milestone for MVP clarity).
- Whether workers see their **preference rank** (may hide to avoid harshness).
- Interest bonus for backups who never start? (optional, later).
- Warranty window length for delivered outcomes.
- Exact revision-limit defaults per SKU.

### Recommended tech baseline
FastAPI modular monolith · PostgreSQL (source of truth) · object storage w/ signed URLs + malware scan · durable queue/workflow engine for timers · provider-hosted payments · Gemini behind an AI gateway (schemas + policy + tracing) · search/vector index when scale requires.

---

*End of design notes. Keep this document updated as decisions evolve.*
