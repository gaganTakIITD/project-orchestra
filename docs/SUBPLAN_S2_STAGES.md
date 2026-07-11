# Sub-plan S2 — Stage-wise product live (A → C)

> **Sprint goal:** Every major product surface works end-to-end on the **real API** (Spine + `event_log`). Temporary demo role stubs are OK until Stage D (auth deepen).
>
> **Parent:** `docs/PIPELINE.md` · **Plan principle:** top-notch for the stage ≠ forever-final.
>
> **When S2 A–C is done:** tick boxes here + update PIPELINE NOW/SHIPPED. Stage D stays LATER.

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
| **D** | Auth, Gemini required, Matcher from DB, deploy | ⏸ LATER |

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

## Stage D — Deepen (do not start until A–C signed off)

- [ ] Real auth (Clerk recommended) replacing `get_demo_client` / `get_demo_worker`
- [ ] Gemini required for Spec Compiler + Task Packet in prod env
- [ ] Matcher from DB `worker_profiles` (not fixture shortlist)
- [ ] Onboarding persists to `worker_profiles`
- [ ] Deploy (Vercel + API host) + secrets

---

## Ownership

| Work | Owner |
|------|--------|
| Stages A–C | Cursor (`core`) |
| UI polish if slots needed after A–C | v0 (`main`) |
| Auth provider + Gemini key for D | Founder |
