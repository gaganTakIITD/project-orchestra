# Hosting the API (Cloud Run + Cloud SQL Postgres)

## Billing split (required)

| Workload | Project | Reason |
|----------|---------|--------|
| **Gemini / GenAI** | `gen-lang-client-0795401430` | ~95k GenAI free credits |
| **Cloud SQL, Cloud Run, Artifact Registry, VPC, Scheduler** | `raystartup` | ~30k infra free credits → ₹0 on those line items |
| **Target SQL** | `raystartup:us-central1:orchestra-trial-pg` | Instance on the **30k-credit** project (reuse) |

Full cutover runbook: **`docs/GCP_BILLING_SPLIT.md`**. Until cutover completes, the Live table below is still on gen-lang-client (you pay for SQL/Run there). Deploy YAML already points at raystartup SQL.

## Live (pre-cutover — gen-lang-client API still serving)

| | |
|--|--|
| **API (current)** | https://orchestra-api-979112189932.us-central1.run.app |
| **Health** | https://orchestra-api-979112189932.us-central1.run.app/api/v1/health |
| **Catalog** | https://orchestra-api-979112189932.us-central1.run.app/api/v1/catalog/skus |
| **Cloud SQL (current / paid)** | `gen-lang-client-0795401430:us-central1:orchestra-pg` |
| **Cloud SQL (target / ₹0 infra)** | `raystartup:us-central1:orchestra-trial-pg` |
| **Frontend** | https://project-orchestra-khaki.vercel.app |
| **Post-cutover** | New Cloud Run URL in `raystartup` + Vercel `NEXT_PUBLIC_API_BASE_URL`; then delete gen-lang-client `orchestra-pg` |

## Why `raysql` kept failing

`raysql` is **MySQL 8.4**. This backend is Postgres (asyncpg / Alembic). The Cloud SQL Connector finally surfaced it as:

`IncompatibleDriverError: ... MYSQL_8_4 ... only be used with Cloud SQL POSTGRES`

Also avoid Cloud Run `/cloudsql/...` Unix sockets with asyncpg — they raise `NotADirectoryError` on gen2. Use the **Cloud SQL Python Connector + private IP + Serverless VPC Access**.

## Cost note — `raysql` delete (founder confirm)

`raysql` is `db-perf-optimized-N-8` (Enterprise Plus MySQL) — expensive if unused. **Not deleted yet** (needs founder confirm). When ready:

```bash
gcloud sql instances delete raysql --project=gen-lang-client-0795401430 --quiet
```

## Secrets (Secret Manager)

Committed deploy YAML must **not** contain DB passwords or `SECRET_KEY`. Live secrets:

| Env var | Secret name |
|---------|-------------|
| `DATABASE_URL` | `orchestra-database-url` |
| `SECRET_KEY` | `orchestra-secret-key` |
| `GEMINI_API_KEY` | `orchestra-gemini-api-key` |

Runtime SA (`979112189932-compute@developer.gserviceaccount.com`) has `roles/secretmanager.secretAccessor` on these secrets.

Rotate (do not commit values):

```bash
echo -n "$NEW_DATABASE_URL" | gcloud secrets versions add orchestra-database-url --data-file=- --project=gen-lang-client-0795401430
echo -n "$NEW_SECRET_KEY" | gcloud secrets versions add orchestra-secret-key --data-file=- --project=gen-lang-client-0795401430
echo -n "$NEW_GEMINI_API_KEY" | gcloud secrets versions add orchestra-gemini-api-key --data-file=- --project=gen-lang-client-0795401430
```

Non-secret env (CORS, `AUTH_MODE`, Cloud SQL instance, etc.) stays in `backend/cloudrun-service.yaml`. Local override file `backend/.cloudrun-env.json` and generated `backend/.cloudrun-deploy.yaml` are **gitignored**.

**Windows note:** do not use PowerShell `echo` to create secrets — it appends `\r\n` and breaks the DB name. Prefer:

```bash
python -c "open('tmp','wb').write(b'postgresql+asyncpg://USER:PASS@/orchestra')"
gcloud secrets versions add orchestra-database-url --data-file=tmp --project=gen-lang-client-0795401430
rm tmp
```

## Redeploy

```bash
cd backend
# build
TAG=v$(date +%Y%m%d%H%M%S)   # or PowerShell equivalent
# After billing cutover — build + deploy in raystartup (see docs/GCP_BILLING_SPLIT.md)
IMG=us-central1-docker.pkg.dev/raystartup/orchestra/api:$TAG
gcloud builds submit --tag $IMG --project=raystartup

# copy template → local deploy file, substitute image, then replace:
# (PowerShell) (Get-Content cloudrun-service.yaml) -replace 'IMAGE_PLACEHOLDER',$IMG | Set-Content .cloudrun-deploy.yaml
gcloud run services replace .cloudrun-deploy.yaml --region=us-central1 --project=raystartup
```

Pre-cutover (legacy, still serving today): use `--project=gen-lang-client-0795401430` and the old Artifact Registry path — only until raystartup Cloud Run is live.

`DATABASE_URL` / `SECRET_KEY` come from Secret Manager via `secretKeyRef` in the YAML. Do not paste them into committed files.

## Vercel frontend bind (Phase 1)

**Status (2026-07-13):** set on Vercel project `project-orchestra` for **Production** and **Preview**:

```
NEXT_PUBLIC_USE_MOCKS=false
NEXT_PUBLIC_API_BASE_URL=https://orchestra-api-979112189932.us-central1.run.app/api/v1
```

`NEXT_PUBLIC_*` are baked in at **build** time — trigger a redeploy after env changes for Production to pick them up.

**Config fix (2026-07-13):** Removed legacy `experimentalServices` from `vercel.json` (backend is on Cloud Run, not a Vercel service). File is now `{ "framework": "nextjs" }`.

**Production redeploy (2026-07-13):** `npx vercel --prod` succeeded after syncing `pnpm-lock.yaml` for `@clerk/nextjs`. Live alias: https://project-orchestra-khaki.vercel.app

**Bind verification:** production JS bundles bake `NEXT_PUBLIC_API_BASE_URL` → Cloud Run (`979112189932`); CORS allows the Vercel origin; API `/catalog/skus` returns 3 SKUs. Homepage catalog is client-rendered — confirm 3 SKU cards in browser DevTools → Network → `catalog/skus`.

**Important:** always pass `--no-sensitive` for `NEXT_PUBLIC_*`. Sensitive-typed vars are unavailable at Next build time, so the client falls back to mocks / localhost. Re-set + redeploy if `vercel env pull` shows empty `""` for those keys.

If CLI is not authenticated on another machine:

```bash
npx vercel login
npx vercel link --yes --project project-orchestra --scope mclmarkscalculator-3730s-projects
npx vercel env add NEXT_PUBLIC_USE_MOCKS production --value "false" --yes --force --no-sensitive
npx vercel env add NEXT_PUBLIC_USE_MOCKS preview --value "false" --yes --force --no-sensitive
npx vercel env add NEXT_PUBLIC_API_BASE_URL production --value "https://orchestra-api-979112189932.us-central1.run.app/api/v1" --yes --force --no-sensitive
npx vercel env add NEXT_PUBLIC_API_BASE_URL preview --value "https://orchestra-api-979112189932.us-central1.run.app/api/v1" --yes --force --no-sensitive
# then redeploy Production so Next bakes the vars in
npx vercel --prod
```

Or set the same two vars in the Vercel dashboard → Project → Settings → Environment Variables → Production + Preview (not Sensitive).

**Done when:** homepage `useSkus()` shows 3 SKUs from Cloud Run (bind gate #1). **Met** after 2026-07-13 Production redeploy (env baked + CORS + API verified; browser SKU cards = final visual check).

### Stage D chat smoke (browser — demo auth, no Clerk)

API chat is live (`POST /chat/sessions` → 201; messages + SSE work; CORS allows Production). Middleware does **not** protect `/start`/`/scope` when Clerk keys are unset.

**UI fix (2026-07-13):** `/start` was flashing/stuck on “Failed to load chat” after a successful session create (idle treated as failure before redirect). `/scope/[id]` used RQ `isLoading` and SSR’d “Could not resume…”. Fixed in `components/scope-chat-surface.tsx` + `app/scope/[sessionId]/page.tsx` — **redeploy Vercel Production** to pick up.

**Founder path:** open https://project-orchestra-khaki.vercel.app → Begin → wait for `/scope/<uuid>` → send one outcome sentence → job description panel updates → **Get my quote** → `/proposal/<quoteId>` → **Confirm & begin work** → tracker shows milestones, **Pick your team** (ready tasks), and live **Chat with team**.

**UI fix (2026-07-13):** `/proposal/[quoteId]` and `/orders/[orderId]` read Next 16 async `params` via `useParams` (same race class as `/scope`). Without this, finalize succeeded but the proposal page showed “Proposal not found”.

**Talent + chat (2026-07-13 / updated 2026-07-17):** Seeded **10 workers** on Cloud Run — **5 original** campus (`@iitd.ac.in`, verified) + **5 fake** demo fillers (`@orchestra.demo`, unverified). Preferences page uses `useParams`; tracker wires `useDiscussion` / `usePostDiscussion` for per-task team chat.

## Founder-gated next (Phase 3–4 — do not invent credentials)

### Gemini (Cloud Run)

**Status (2026-07-13):** Secret Manager secret `orchestra-gemini-api-key` is configured; Cloud Run `orchestra-api` binds env `GEMINI_API_KEY` via `secretKeyRef` (not plaintext). Runtime SA has `secretAccessor`.

Rotate (do not commit values; on Windows avoid PowerShell `echo` — write bytes to a temp file):

```bash
gcloud secrets versions add orchestra-gemini-api-key --data-file=tmp --project=gen-lang-client-0795401430
gcloud run services update orchestra-api --region=us-central1 \
  --update-secrets=GEMINI_API_KEY=orchestra-gemini-api-key:latest \
  --project=gen-lang-client-0795401430
```

### Clerk (Vercel + Cloud Run) — founder checklist

**Cursor-complete:** `AUTH_MODE=demo|clerk` backend + `@clerk/nextjs` frontend + mock-JWKS pytest (`backend/tests/test_auth.py`). Committed `cloudrun-service.yaml` is a **deploy template only** (may still show `AUTH_MODE=demo`); it is **not** the live service config. Do **not** invent or commit Clerk secrets.

**Status (2026-07-13):** **live** — Clerk app `arriving-serval-22`; Vercel Production + Preview have `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` + `CLERK_SECRET_KEY`; Cloud Run revision `orchestra-api-00024-krv` has `AUTH_MODE=clerk` + JWKS/issuer for `https://arriving-serval-22.clerk.accounts.dev`. Live env was set via `gcloud run services update` (template yaml is not the source of truth for AUTH_MODE). **Rotate Clerk keys** if they were pasted in chat.

**Smoke (founder):** sign in at https://project-orchestra-khaki.vercel.app → Begin → scope chat → quote → confirm. DevTools → Network: API calls carry `Authorization: Bearer …`; `GET /api/v1/auth/me` without token returns `401`.

#### Founder steps (reference — completed 2026-07-13)

1. **Create a Clerk application** at [clerk.com](https://clerk.com) → copy keys from the Dashboard (API Keys / JWT).
2. **Vercel** (Production + Preview) — set, then **redeploy** (`npx vercel --prod`):

| Env var | Where | Notes |
|---------|--------|--------|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Vercel | `pk_…` — use `--no-sensitive` (baked at build) |
| `CLERK_SECRET_KEY` | Vercel | `sk_…` — sensitive OK |

3. **Cloud Run** — env-only update (no image rebuild). Set `AUTH_MODE=clerk` plus JWT verify vars (from Clerk Frontend API / JWKS):

| Env var | Required | Example shape (do not invent values) |
|---------|----------|--------------------------------------|
| `AUTH_MODE` | yes | `clerk` (today: `demo` in `cloudrun-service.yaml`) |
| `CLERK_JWKS_URL` | yes | `https://YOUR_INSTANCE.clerk.accounts.dev/.well-known/jwks.json` |
| `CLERK_ISSUER` | yes | `https://YOUR_INSTANCE.clerk.accounts.dev` |
| `CLERK_AUDIENCE` | optional | leave unset unless Clerk JWT has an `aud` claim |

Prefer Secret Manager for JWKS/issuer if you want rotation without YAML edits; plain env update is enough to flip.

```bash
# After keys exist — example only; substitute YOUR real values / secret names
gcloud run services update orchestra-api --region=us-central1 \
  --update-env-vars=AUTH_MODE=clerk,CLERK_JWKS_URL=https://YOUR_INSTANCE.clerk.accounts.dev/.well-known/jwks.json,CLERK_ISSUER=https://YOUR_INSTANCE.clerk.accounts.dev \
  --project=gen-lang-client-0795401430
```

4. **Smoke:** sign in on Vercel → `GET /api/v1/auth/me` with Bearer JWT returns the Clerk-linked user. Keep `AUTH_MODE=demo` for local Docker + pytest.

Local `.env.local` should keep `NEXT_PUBLIC_API_BASE_URL=http://localhost:3000` for Docker work only when testing frontend against itself — use `http://localhost:8000/api/v1` for API. Do not commit `.env.local`. See `.env.example` for the full local Clerk var list.

---

## Campus dual-account smoke checklist (P0 harden)

Run on **prod** (Vercel + Cloud Run) with two Clerk accounts.

1. **Client account** — `/account` → client → `/start` → scope chat → Get quote → confirm → `/orders/{id}`
2. **Assemble team** — open preferences / matcher chat; rank ≥3 real workers → finalize preferences (task → `invited`)
3. **Worker account** — `/account` → worker → Inbox → Accept interest → Ready to start → Submit
4. **Client** — accept delivery when order `delivered`
5. **Admin** (claim/allowlist) — `/admin` → open order events (`event_log` trail)
6. **Notifications** — workspace bell shows invite / QA / delivery rows; mark-read works
7. **Ledger strip** — Held after confirm → Reserved after mutual start → Released after accept

### Cloud Scheduler — durable timers

Priority windows need a tick on Cloud Run (in-process loop is off by default: `TIMER_TICK_SECONDS=0`).

```bash
# Create an OIDC-authenticated job hitting the tick endpoint every 5 minutes
gcloud scheduler jobs create http orchestra-timer-tick \
  --location=us-central1 \
  --schedule="*/5 * * * *" \
  --uri="https://YOUR_CLOUD_RUN_URL/api/v1/internal/timers/tick" \
  --http-method=POST \
  --oidc-service-account-email=YOUR_SA@PROJECT.iam.gserviceaccount.com \
  --project=gen-lang-client-0795401430
```

Local/dev: `POST http://localhost:8000/api/v1/internal/timers/tick` or set `TIMER_TICK_SECONDS=60`.

### Founder cost cleanup

1. **Billing split (primary):** point Cloud Run at **`raystartup:us-central1:orchestra-trial-pg`** and deploy API in project `raystartup`. Keep Gemini on **gen-lang-client**. Runbook: `docs/GCP_BILLING_SPLIT.md`.
2. After cutover: delete `orchestra-pg` on gen-lang-client (stops paid Postgres there).
3. Confirm then: `gcloud sql instances delete raysql --project=gen-lang-client-0795401430 --quiet` (leftover MySQL — not Orchestra).

