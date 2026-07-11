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

**👉 If you are v0 (or prompting v0), read [`docs/V0_HANDOFF.md`](docs/V0_HANDOFF.md) first.**

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

```bash
npm install
npm run dev        # http://localhost:3000
```

The app runs entirely on **mock data** today (`NEXT_PUBLIC_USE_MOCKS` defaults to `true`). No backend required to build and preview every screen.

## The build stages

1. **Homepage** — public marketing landing (v0)
2. **Client workflow** — describe → proposal → preferences → live tracker → delivery (v0 on the contract)
3. **Worker workflow** — profile → inbox → mutual start → submit → earnings (v0 on the contract)
4. **AI + Spine** — real FastAPI backend + Gemini agents; swap mocks → real API (Cursor)
5. **Finishing pass** — realtime, admin, auth, disputes, polish
