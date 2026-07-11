# Project Orchestra

**Outcome-as-a-Service.** Tell us the digital result you need — a brand, a landing page, an app feature — and our AI general contractor (Gemini) plans it into tasks, staffs it with verified IIT Delhi talent, verifies every handoff, and delivers the finished outcome. See `docs/` for the full product, technical, and business specs.

> **Architecture bet:** a deterministic **Spine** (state machine, timers, ledger, policy) that calls **Gemini reasoning nodes** at decision points. _AI proposes; the Spine enforces and records._

---

## How this repo is built — two builders, side by side

The frontend is built in parallel by two collaborators, coordinated through GitHub and a **shared contract**:

| Builder | Owns | What they produce |
|---------|------|-------------------|
| **Vercel v0** | The **core UI** — `app/**`, `components/**`, styling | Polished, on-brand screens & components (shadcn/ui + Tailwind) |
| **Cursor (this side)** | The **thin frontend + shared context + backend** — `lib/**`, `backend/**`, config | Types, mock data, API client, hooks, design tokens, and the real Spine + AI |

The two never collide because both build against the **frozen contract** in `lib/`. When the real backend lands, the UI keeps working unchanged — we just flip one flag.

**👉 Start here, whoever you are:**

| You are | Read first |
|---------|-----------|
| Any agent or contributor | [`docs/PIPELINE.md`](docs/PIPELINE.md) — what to work on now · [`AGENTS.md`](AGENTS.md) — the rules |
| v0 (or prompting v0) | [`docs/V0_HANDOFF.md`](docs/V0_HANDOFF.md) — UI contract + per-screen specs |
| Backend work | [`docs/BACKEND_IMPLEMENTATION_PLAN.md`](docs/BACKEND_IMPLEMENTATION_PLAN.md) — phases B1–B6 |

---

## Repo layout

```text
.
├── app/                # Next.js App Router — routes & pages        [v0 owns]
├── components/         # UI components (shadcn/ui + custom)          [v0 owns]
├── lib/                # SHARED CONTEXT — the contract               [Cursor owns]
│   ├── types.ts        #   API/DB types (mirrors Tech Spec §4/§7/§8)
│   ├── mock-data.ts    #   contract-shaped fixtures (Launch Studio)
│   ├── api.ts          #   mock-first API client (swap to real: 1 flag)
│   ├── hooks.ts        #   TanStack Query hooks — screens call these
│   ├── state-labels.ts #   dual-view labels (client vs worker language)
│   ├── providers.tsx   #   TanStack Query provider (mounted in layout)
│   └── utils.ts        #   cn() for Tailwind class merging
├── app/globals.css     # design tokens (brand) — v0 components inherit these
├── backend/            # FastAPI Spine + Gemini agents (Stage 4)     [Cursor owns]
└── docs/               # product / technical / business specs
```

## Stack

Next.js 16 (App Router) · React 19 · TypeScript · Tailwind CSS v4 · shadcn/ui · TanStack Query · Zod. Backend (Stage 4): FastAPI · PostgreSQL + pgvector · Redis · Gemini.

## Getting started

### Frontend only (mocks — offline / no Docker)

```bash
npm install
npm run dev        # http://localhost:3000
```

Mocks apply when `NEXT_PUBLIC_USE_MOCKS` is unset or not `false`. Prefer the full-stack product path below for “does the app work?”

### Full stack — product path (real API)

**Requires Docker Desktop running.**

```bash
# 1. Env
cp .env.example .env
# For Next.js, create .env.local with:
#   NEXT_PUBLIC_USE_MOCKS=false
#   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1

# 2. Backend + data stores
docker compose up -d --build

# 3. Verify API + product smoke
curl http://localhost:8000/api/v1/health
cd backend && python -m pytest tests/test_product_smoke.py -v

# 4. Frontend
npm install
npm run dev
```

See **`docs/SUBPLAN_S2_STAGES.md`** for stage A–C status and Stage D deepen work.

## The build stages

1. **Homepage** — public marketing landing (v0)
2. **Client workflow** — describe → proposal → preferences → live tracker → delivery (v0 on the contract)
3. **Worker workflow** — profile → inbox → mutual start → submit → earnings (v0 on the contract)
4. **AI + Spine** — real FastAPI backend + Gemini agents; swap mocks → real API (Cursor)
5. **Finishing pass** — realtime, admin, auth, disputes, polish
