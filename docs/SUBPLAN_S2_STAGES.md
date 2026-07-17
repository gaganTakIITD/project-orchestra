# Sub-plan S2 — Stage-wise product live (A → C)

> **Sprint goal:** Every major product surface works end-to-end on the **real API** (Spine + `event_log`). Temporary demo role stubs are OK until Stage D (auth deepen).
>
> **Parent:** `docs/PIPELINE.md` · **Plan principle:** top-notch for the stage ≠ forever-final.
>
> **When S2 A–C is done:** tick boxes here + update PIPELINE NOW/SHIPPED. **Stage D deepen is NOW** (bind → profiles → matcher → Gemini → Clerk).

---

## Outcome (one sentence)

A founder can run the product path with `NEXT_PUBLIC_USE_MOCKS=false` against Docker: scope/intent → quote → order → worker accept → submit → (optional) delivery accept — **no fake buttons that 404**.

---

## Stages

| Stage | Scope | Status |
|-------|--------|--------|
| **A** | Worker lifecycle APIs + Submission + Spine | ✅ Complete |
| **B** | Discussion thread + delivery get/accept + order close | ✅ Complete |
| **C** | Product default = real API + smoke (scope→submit) | ✅ Complete |
| **D** | Auth, Gemini required, Matcher from DB, deploy | 🔄 **NOW** — Clerk live; **`raysql` delete founder-blocked** |

---

## Stage A — Worker lifecycle ✅

**Endpoints**

- `POST /api/v1/tasks/{id}/accept-interest` → Spine `interest_accepted` (+ priority grant); returns `{ status: "accepted" }` (Spine: `priority_active`)
- `POST /api/v1/tasks/{id}/ready-to-start` → `start_requested` → mutual start → `in_progress`
- `POST /api/v1/tasks/{id}/submit` → persist `submissions` + Spine `submitted` + stage auto-QA → `completed`

**Done when:** From a confirmed order, worker can accept and submit; events land in DB.

**Verify:** `cd backend && python -m pytest tests/test_task_lifecycle.py -v`

---

## Stage B — Discussion + delivery ✅

**Endpoints**

- `GET/POST /api/v1/tasks/{id}/discussion` — scoped thread (persisted)
- `GET /api/v1/orders/{id}/delivery` — bundle from submissions (all tasks completed)
- `POST /api/v1/orders/{id}/accept-delivery` → order Spine `client_accept` → `closed`

**Done when:** Client can see delivery bundle and accept outcome after full DAG complete.

---

## Stage C — Product path = real API ✅

**Local product path**

```env
# .env.local
NEXT_PUBLIC_USE_MOCKS=false
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

```bash
docker compose up -d --build
curl http://localhost:8000/api/v1/health
cd backend && python -m pytest tests/test_product_smoke.py -v
npm run dev   # browser against real API
```

Mocks remain only for CI / offline v0 work — not the “app works” story.

**Done when:** `test_product_smoke` proves intent → preferences → accept → submit without mocks.

---

## Stage D — Deepen ⟵ **NOW**

- [x] **Auth first slice:** `AUTH_MODE=demo|clerk`, Clerk JWT verify + `users.external_auth_id`, FastAPI `get_current_client` / `get_current_worker`, frontend `@clerk/nextjs` + `/sign-in` `/sign-up` (Clerk live on Vercel + Cloud Run; see `docs/DEPLOY_API.md`)
- [x] **Clerk go-live:** Vercel + Cloud Run `AUTH_MODE=clerk` (`arriving-serval-22`; see `docs/DEPLOY_API.md`)
- [x] Gemini required gate in code (`APP_ENV=production` / `REQUIRE_GEMINI`; Spec Compiler + Task Packet via gateway; no silent fixture)
- [x] Founder: `GEMINI_API_KEY` on Cloud Run via Secret Manager (`orchestra-gemini-api-key`) — live
- [x] Matcher from DB `worker_profiles` (not fixture shortlist)
- [x] Onboarding persists to `worker_profiles`
- [x] **Deploy API + secrets:** Cloud Run live; `DATABASE_URL` / `SECRET_KEY` via Secret Manager; plaintext removed from committed `cloudrun-service.yaml`
- [x] **Vercel env bind:** `NEXT_PUBLIC_USE_MOCKS=false` + Cloud Run `NEXT_PUBLIC_API_BASE_URL` on Production + Preview (**non-sensitive**)
- [x] **Bind gate #1:** Production redeployed (`vercel.json` → Next.js; `pnpm-lock` synced); Cloud Run URL baked, CORS OK, API 3 SKUs
- [x] **`raysql` + `orchestra-pg` deleted** on gen-lang-client (2026-07-17) — see `docs/DEPLOY_API.md`

---

## Ownership

| Work | Owner |
|------|--------|
| Stages A–C | Cursor (`core`) |
| UI polish if slots needed after A–C | v0 (`main`) |
| Auth provider + Gemini key for D | Founder |
