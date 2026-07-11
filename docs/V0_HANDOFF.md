# v0 Handoff Kit — building the core UI on the shared contract

> **You (v0) build the core UI. Cursor builds the thin frontend, the shared contract in `lib/`, and the backend.** This doc is your source of truth so everything snaps together and merges cleanly on GitHub.

---

## TL;DR — the 6 golden rules

1. **Import types, never invent them.** All data shapes live in `@/lib/types`. Use them.
2. **Never fetch directly.** Get data through hooks in `@/lib/hooks` (which call `@/lib/api`). This keeps the mock → real-backend swap invisible.
3. **Use the design tokens.** Style with `bg-background`, `text-foreground`, `text-primary`, `border-border`, etc. Don't hardcode hex colors — the brand lives in `app/globals.css`.
4. **Stay in your lane.** You own `app/**` and `components/**`. Don't edit `lib/**`, `backend/**`, or config — that's Cursor's, and editing it causes merge conflicts.
5. **Presentational components in `components/`, compose pages in `app/`.** Keep data-fetching at the page/route level via hooks; pass plain props into components.
6. **One chat = one branch = one PR.** Work on a v0 branch, open a PR, merge to `main`. Cursor works on a separate branch.

---

## Folder ownership (prevents collisions)

| Path | Owner | Notes |
|------|-------|-------|
| `app/**` (routes, pages, layouts) | **v0** | except `app/layout.tsx` provider wiring + `app/globals.css` tokens are seeded by Cursor — extend, don't rip out |
| `components/**` | **v0** | shadcn/ui + your custom components |
| `lib/**` | **Cursor** | the contract: types, mock data, api, hooks, labels |
| `backend/**`, `*.config.*`, `package.json` | **Cursor** | coordinate dep additions via PR |

---

## The shared contract — where everything is

| File | What it gives you |
|------|-------------------|
| `@/lib/types` | Every entity + enum: `OutcomeOrder`, `FulfillmentTask`, `OutcomeSpec`, `Candidate`, `WorkerProfile`, `TaskStatus`, `OrderStatus`, … |
| `@/lib/hooks` | Ready data hooks: `useOrder`, `usePlan`, `useSpec`, `useQuote`, `useCandidates`, `useDelivery`, `useWorkerProfile`, `useMyTasks`, `useCharter`, `useNotifications`, `useSkus`, + mutations `useSetPreferences`, `useAcceptInterest`, `useSubmit` |
| `@/lib/state-labels` | Dual-view labels: `taskStatusClientLabel`, `taskStatusWorkerLabel`, `orderStatusClientLabel`, `taskStatusTone` (for badge colors) |
| `@/lib/mock-data` | The data the hooks return today (a full "Launch Studio" scenario) — handy to eyeball shapes |
| `app/globals.css` | Brand design tokens (indigo primary, light + dark) |

### Import cheat-sheet

```tsx
"use client";
import { useOrder, usePlan } from "@/lib/hooks";
import type { FulfillmentTask } from "@/lib/types";
import { taskStatusClientLabel, taskStatusTone } from "@/lib/state-labels";

export function OrderTracker({ orderId }: { orderId: string }) {
  const { data: order, isLoading } = useOrder(orderId);
  const { data: plan } = usePlan(orderId);
  if (isLoading || !order || !plan) return <TrackerSkeleton />;
  return (
    <div>
      {plan.tasks.map((t: FulfillmentTask) => (
        <MilestoneRow key={t.id} label={taskStatusClientLabel[t.status]} tone={taskStatusTone[t.status]} />
      ))}
    </div>
  );
}
```

---

## Brand

Trustworthy + modern. **Primary = indigo** (intelligence / trust). Clean neutrals, generous spacing, rounded-`lg` corners, subtle borders. Light + dark both supported (toggle `class="dark"` on `<html>`). Voice: confident, plain-spoken, outcome-focused — _"Tell us the result. We deliver it."_

---

## Route map (build in stage order)

| Route | Screen | Stage | Owner |
|-------|--------|-------|-------|
| `/` | Marketing homepage | 1 | v0 |
| `/start` | Client: describe your outcome (intent) | 2 | v0 |
| `/proposal/[quoteId]` | Client: outcome proposal + price | 2 | v0 |
| `/orders/[orderId]` | Client: live milestone tracker + chat + delivery | 2 | v0 |
| `/orders/[orderId]/preferences/[taskId]` | Client: pick preferred workers | 2 | v0 |
| `/join` | Worker: talent landing | 3 | v0 |
| `/worker/onboarding` | Worker: profile wizard (+ completion %) | 3 | v0 |
| `/worker` | Worker: dashboard / task inbox | 3 | v0 |
| `/worker/tasks/[taskId]` | Worker: task detail (charter, packet, submit, QA) | 3 | v0 |
| `/admin` | Admin console | 5 | later |

---

## Per-screen specs

### Stage 1 — `/` Homepage  ⟵ start here
- **Purpose:** sell Outcome-as-a-Service; route visitors to the two flows.
- **CTAs:** primary → `/start` ("Describe your outcome"); secondary → `/join` ("Join as talent").
- **Sections:** sticky header/nav · hero (headline + subhead + dual CTA) · how it works (Describe → Confirm → Watch → Receive) · why us (outcome vs freelancer directory) · outcome catalog (cards from `useSkus()` — Launch Studio, Brand Starter, Landing Launch: name, description, base_price, typical_days) · "for clients" vs "for talent" split · trust (campus-verified IIT-D talent, AI-verified QA) · FAQ · footer.
- **Data:** `useSkus()` for the catalog cards (optional; safe to render statically too).
- **States:** static; SKU cards show a skeleton while loading.

### Stage 2 — Client workflow
- **`/start`** — chat-style intent capture. Big textarea + example prompts. On submit call `clientApi.createIntent` (via a mutation) → route to `/proposal/quote_healthtrack`. States: empty, submitting.
- **`/proposal/[quoteId]`** — data: `useQuote(quoteId)`, `useSpec()`. Render the `OutcomeSpec`: outcome statement, deliverables, acceptance criteria (badge each `check_type`), in/out-of-scope, assumptions, client inputs; plus price, deadline, revision limit. CTA "Confirm & fund" → `clientApi.acceptQuote` → `/orders/ord_healthtrack`. States: loading, loaded.
- **`/orders/[orderId]`** — data: `useOrder`, `usePlan`, `useDelivery` (when `order.status === "delivered"`), `useDiscussion(taskId)`. Show `progress_pct`, milestones with **client** labels (`orderStatusClientLabel`, `taskStatusClientLabel`), a scoped chat panel, and a delivery-review panel (bundle assets + "Accept outcome"). **Never show worker-side failure states** (rework reads as "In progress"). States: loading, in-progress, delivered.
- **`/orders/[orderId]/preferences/[taskId]`** — data: `useCandidates(orderId, taskId)`, `useSetPreferences`. Cards per `Candidate` (name, headline, `score`, `rationale`, `seller_level`, `on_time_pct`, availability). Let client rank/select **at least 3**; submit → back to tracker. States: loading, selecting (enforce min 3), submitting.

### Stage 3 — Worker workflow
- **`/join`** — talent landing: why join, how earnings work, CTA → `/worker/onboarding`.
- **`/worker/onboarding`** — multi-step profile wizard: basics → skills/tools/task-types (options from `useTaskTypes()` etc.) → portfolio → availability. Show a live **completion %** meter and the **≥70% to go live** gate. Uses `WorkerProfile` shape.
- **`/worker`** — data: `useWorkerProfile`, `useMyTasks`, `useNotifications`. Task inbox grouped by **worker** labels (`taskStatusWorkerLabel`, `taskStatusTone`); for `priority_active` tasks show a countdown to `priority_window_ends`; earnings/stats summary from `profile.stats`. States: empty, has-tasks.
- **`/worker/tasks/[taskId]`** — data: `useCharter(taskId)`, task from `useMyTasks`, `useDiscussion`. Show the frozen **Charter** (scope, deliverables, acceptance criteria, deadline, revision limit), a task **packet** (checklist derived from `acceptance_criteria`), and stage-appropriate actions: `useAcceptInterest`, ready-to-start, `useSubmit` (notes + asset URLs), and QA feedback on rework. States mirror `TaskStatus`.

---

## Ready-to-paste v0 prompt (Stage 2 — client workflow) ⟵ **SHIPPED on main**

## Ready-to-paste v0 prompt (Stage 3 — worker workflow) ⟵ **REQUEST THIS NOW**

> Cursor shipped `TaskPacket` + `useTaskPacket(taskId)` + mock `mockTaskPacket`. Use both Charter and Packet on the task detail page.

```
Build Stage 3 of Project Orchestra worker workflow (update /join + 3 screens).
Client Stage 2 + /scope/[sessionId] are live on main. Wire on MOCK DATA via @/lib/hooks — do NOT edit lib/**.

Golden rules:
- Import types from @/lib/types only (Charter, TaskPacket, WorkerProfile, FulfillmentTask)
- Fetch ONLY via @/lib/hooks — never fetch() directly
- Design tokens: bg-background, text-primary, border-border
- Presentational in components/; pages in app/
- Match indigo Lumena aesthetic (mono labels, border-driven, spacious)

1) UPDATE /join
   - Talent landing: why join, how earnings work
   - Primary CTA "Start onboarding" → /worker/onboarding

2) NEW /worker/onboarding
   - Multi-step wizard: basics → skills/tools/task-types (useTaskTypes()) → portfolio → availability
   - Live profile_completion_pct meter; gate continue at ≥70%
   - Use WorkerProfile shape from mocks (assume logged-in Rohan Verma — no auth UI)

3) NEW /worker
   - useWorkerProfile(), useMyTasks(), useNotifications()
   - Task inbox with taskStatusWorkerLabel + taskStatusTone from @/lib/state-labels
   - Countdown for priority_active tasks (priority_window_ends)
   - Stats from profile.stats
   - Click task → /worker/tasks/[taskId]

4) NEW /worker/tasks/[taskId] — WORKER JOB CARD (critical)
   - useCharter(taskId) — frozen contract: scope, deliverables, acceptance, price, deadline, out_of_scope
   - useTaskPacket(taskId) — job card: brief, checklist (checkboxes), client_inputs, dependencies
   - Task from useMyTasks(); useDiscussion(taskId) for scoped chat panel
   - Actions by status:
     • invited / interest_pool → useAcceptInterest(taskId)
     • mutual_start / in_progress → useSubmit({ notes, asset_urls })
     • rework → show QA feedback + resubmit
   - Layout: Charter summary on top, TaskPacket checklist as primary work surface, discussion below
   - States: loading skeleton, loaded, submitting

Reference mock IDs in lib/mock-data.ts: usr_worker_rohan, task_logo, charter_logo, packet_logo.
No auth/login pages. Do not edit lib/**, backend/**, or package.json unless adding a shadcn component.
```

## Ready-to-paste v0 prompt (Stage 2 — client workflow) ⟵ archived

```
Build Stage 2 of the Project Orchestra client workflow (4 screens). We already have
the marketing homepage at "/" and static shells at "/start" and "/join". Wire the
full client journey on MOCK DATA via our shared contract — do NOT edit lib/**.

Golden rules (must follow):
- Import types from @/lib/types only
- Fetch data ONLY through hooks in @/lib/hooks — never fetch() directly
- Style with design tokens: bg-background, text-primary, border-border, etc.
- Put presentational components in components/; pages in app/
- Match existing Lumena/Bauhaus homepage aesthetic (indigo primary, spacious, mono labels)

Screens to build (in order):

1) UPDATE /start — intent capture
   - Chat-style layout: large textarea + 2–3 example prompt chips
   - On submit: useCreateIntent() from @/lib/hooks with the textarea text
   - On success: router.push(`/proposal/${data.quote_id}`)
   - States: empty, submitting (disable button + spinner), error toast

2) NEW /proposal/[quoteId] — outcome proposal + price
   - On /start success, save intent_id from createIntent response to sessionStorage key "last_intent_id"
   - Data: useQuote(quoteId), useSpec(sessionStorage intent_id)
   - Render OutcomeSpec: outcome_statement, deliverables, acceptance_criteria (badge each check_type),
     in_scope, out_of_scope, assumptions, client_inputs_required
   - Show Quote card: price (INR), deadline, revision_limit, ai_rationale
   - CTA "Confirm & fund": useAcceptQuote(quoteId) → router.push(`/orders/${order_id}`)
   - States: loading skeleton, loaded

3) NEW /orders/[orderId] — live milestone tracker
   - Data: useOrder(orderId), usePlan(orderId)
   - Show progress_pct bar, order status via orderStatusClientLabel from @/lib/state-labels
   - Milestone list from plan.tasks with taskStatusClientLabel + taskStatusTone badges
   - NEVER show worker failure states (rework = "In progress" for client view)
   - Placeholder panels for chat and delivery (can be empty cards labeled "Discussion" / "Delivery" for now)
   - Link to preferences when a task status is "ready" or "invited": `/orders/${orderId}/preferences/${taskId}`

4) NEW /orders/[orderId]/preferences/[taskId] — pick workers
   - Data: useCandidates(orderId, taskId), useSetPreferences(orderId, taskId)
   - Candidate cards: name, headline, score, rationale, seller_level, on_time_pct
   - Client must select/rank at least 3 workers before submit
   - Submit → invalidate + navigate back to /orders/[orderId]
   - States: loading, selecting (show count "2/3 selected"), submitting

Reference mock scenario IDs in lib/mock-data.ts: quote_healthtrack, ord_healthtrack, int_healthtrack.
Import FulfillmentTask, Candidate, Quote types from @/lib/types.

Do not build auth/login pages yet — demo runs as anonymous client on mocks.
Do not edit lib/**, backend/**, or package.json unless adding a shadcn component.
```

---

```
Build the marketing homepage (route "/") for "Project Orchestra", an AI-native
Outcome-as-a-Service platform. Tagline: "Tell us the result. We deliver it."
A client describes a digital outcome (brand, landing page, app feature); an AI
general contractor plans it into tasks, staffs it with verified IIT Delhi student
talent, verifies every handoff, and delivers the finished result.

Use our existing setup: Next.js App Router, Tailwind v4, shadcn/ui. Style ONLY with
our design tokens (bg-background, text-foreground, text-primary [indigo], border-border,
bg-card, text-muted-foreground). Support light + dark. Modern, trustworthy, spacious.

Sections: sticky header w/ logo + nav + "Describe your outcome" button; hero with
headline, subhead, and two CTAs (primary "Describe your outcome" -> /start,
secondary "Join as talent" -> /join); "How it works" 4 steps (Describe, Confirm,
Watch, Receive); "Why Orchestra" (buying an outcome, not managing freelancers);
an outcome catalog of cards (render from the useSkus() hook in @/lib/hooks — each
OutcomeSku has name, description, base_price (INR), typical_days); a two-column
"For clients / For talent" split; a trust band (campus-verified talent, AI-verified
quality); a short FAQ; and a footer.

Import the SKU type from @/lib/types and the useSkus hook from @/lib/hooks. Put
reusable pieces in components/ and compose them in app/page.tsx. Do not edit lib/**.
```

---

## The v0 ↔ GitHub workflow (side by side)

**One-time setup**
1. The repo is on GitHub with the Next.js app **at the root** (required — v0's build runs from the repo root).
2. In v0 → **Import from GitHub** → select this repo → base branch `main` → root directory = repository root.

**Every UI task**
1. Start a **new v0 chat** → v0 creates a dedicated **branch off `main`** and syncs each generation as a commit.
2. Prompt v0 (use the specs above). Review the live preview.
3. When happy, **open a PR from v0** and merge into `main`.

**Cursor, in parallel**
- Works on a separate branch (e.g. `core`) for `lib/**` + `backend/**`, opens its own PRs into `main`.
- Because ownership is split by folder, v0 PRs and Cursor PRs rarely touch the same files. If `package.json` conflicts (both added deps), resolve by keeping both dependency lists.

**Result:** v0 polishes screens while Cursor hardens the contract and builds the Spine. The homepage and workflows come to life on mock data; when the backend is ready, Cursor flips `NEXT_PUBLIC_USE_MOCKS=false` and every screen keeps working.
