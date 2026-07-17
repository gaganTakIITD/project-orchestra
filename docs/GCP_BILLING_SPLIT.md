# Dual-project billing split (GenAI vs infra)

> **Why:** `gen-lang-client` has **~95k GenAI free credits** (good for Gemini / Vertex). Infra there (Cloud SQL, Cloud Run, networking) still **bills cash**. **raystartup** has the **~30k infra free credits** — Cloud SQL / Cloud Run / Artifact Registry / networking hit those and show **₹0 subtotals**. Put AI usage on gen-lang-client; put Orchestra infra on raystartup.

## Confirmed targets

| Concern | Value |
|---------|--------|
| **AI project (95k GenAI credits)** | `gen-lang-client-0795401430` |
| **Infra project (30k free credits)** | `raystartup` |
| **Infra Cloud SQL** | `raystartup:us-central1:orchestra-trial-pg` — instance **on the 30k-credit project** |
| **Region** | `us-central1` |

```bash
export INFRA_PROJECT=raystartup
export AI_PROJECT=gen-lang-client-0795401430
export REGION=us-central1
export SQL_INSTANCE=orchestra-trial-pg
export SQL_CONNECTION=raystartup:us-central1:orchestra-trial-pg
```

## Target ownership

| Concern | GCP project | Why |
|---------|-------------|-----|
| **Gemini / Vertex / GenAI API calls** | `gen-lang-client-0795401430` | 95k GenAI credits |
| **Cloud SQL (`orchestra-trial-pg`)** | `raystartup` (30k credits) | Free infra credits → ₹0 |
| **Cloud Run (`orchestra-api`)** | `raystartup` | Same |
| **Artifact Registry, VPC connector, Cloud Build (API images)** | `raystartup` | Same |
| **Secret Manager (DB URL, SECRET_KEY)** | `raystartup` | Lives with the API |
| **`GEMINI_API_KEY` secret** | Stored in **raystartup** Secret Manager (value from AI Studio / gen-lang-client key) | Cloud Run reads local secret; **usage still bills gen-lang-client** if the key is from that project’s GenAI |

Until cutover is done, production still runs on `AI_PROJECT` (paying for SQL/Run there).

## Current (wrong for credits) — live until cutover

| Resource | Today |
|----------|--------|
| API | `https://orchestra-api-979112189932.us-central1.run.app` |
| Cloud SQL | `gen-lang-client-0795401430:us-central1:orchestra-pg` |
| Private IP | `10.22.0.5` via connector `orchestra-vpc` |
| Leftover cost | `raysql` MySQL on gen-lang-client — delete after confirm |

## Target infra (confirmed)

| Resource | After cutover |
|----------|----------------|
| Cloud SQL | `raystartup:us-central1:orchestra-trial-pg` (**exists** — reuse, do not recreate) |
| Cloud Run | Deploy `orchestra-api` in project `raystartup` |
| Connection env | `CLOUD_SQL_INSTANCE=raystartup:us-central1:orchestra-trial-pg` |

## Cutover plan (founder runs `gcloud` — this environment has no GCP credentials)

Do this in one maintenance window. Keep old stack up until new `/health` is green, then flip Vercel, then tear down old infra.

### 0. Prerequisites

```bash
gcloud auth login
gcloud config set project "$INFRA_PROJECT"
gcloud services enable \
  run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com \
  artifactregistry.googleapis.com cloudbuild.googleapis.com \
  vpcaccess.googleapis.com compute.googleapis.com \
  --project="$INFRA_PROJECT"
```

### 1. Reuse existing Postgres `orchestra-trial-pg` (do not create a second instance)

```bash
gcloud sql instances describe orchestra-trial-pg --project="$INFRA_PROJECT"
# Confirm POSTGRES (not MySQL). Note private IP + network.

# Ensure app database + user exist (names may already be set — adjust to match instance)
gcloud sql databases list --instance=orchestra-trial-pg --project="$INFRA_PROJECT"
gcloud sql users list --instance=orchestra-trial-pg --project="$INFRA_PROJECT"
```

Prefer private IP + Serverless VPC Access (same pattern as today). Create connector if missing:

```bash
gcloud compute networks vpc-access connectors describe orchestra-vpc \
  --region="$REGION" --project="$INFRA_PROJECT" 2>/dev/null \
  || gcloud compute networks vpc-access connectors create orchestra-vpc \
       --region="$REGION" \
       --network=default \
       --range=10.8.0.0/28 \
       --project="$INFRA_PROJECT"
```

Connection name (committed in `backend/cloudrun-service.yaml`):

```text
raystartup:us-central1:orchestra-trial-pg
```

### 2. Migrate data (dump old → restore new) — optional

From a machine that can reach **both** instances (Cloud Shell + Auth proxy, or Cloud SQL export to GCS):

```bash
# Old: gen-lang-client … orchestra-pg  →  New: raystartup … orchestra-trial-pg
pg_dump -Fc -h 127.0.0.1 -p 5432 -U orchestra orchestra > orchestra.dump
pg_restore -h 127.0.0.1 -p 5433 -U orchestra -d orchestra --clean --if-exists orchestra.dump
```

**Pilot / empty OK:** skip dump; new Cloud Run with `AUTO_SEED=true` recreates catalog + 10 worker seed. You lose live orders/users unless you dump/restore or re-run Clerk-linked smoke.

### 3. Secrets on raystartup

```bash
# DATABASE_URL: postgresql+asyncpg://USER:PASS@/DBNAME  (connector fills host)
# Use the real user/db on orchestra-trial-pg — do not invent passwords in git
python -c "open('tmp','wb').write(b'postgresql+asyncpg://USER:PASS@/orchestra')"
gcloud secrets create orchestra-database-url --data-file=tmp --project="$INFRA_PROJECT" 2>/dev/null \
  || gcloud secrets versions add orchestra-database-url --data-file=tmp --project="$INFRA_PROJECT"
rm tmp

openssl rand -hex 32 | tr -d '\n' > tmp
gcloud secrets create orchestra-secret-key --data-file=tmp --project="$INFRA_PROJECT" 2>/dev/null \
  || gcloud secrets versions add orchestra-secret-key --data-file=tmp --project="$INFRA_PROJECT"
rm tmp

# GEMINI_API_KEY — same key that bills under gen-lang-client GenAI credits
gcloud secrets create orchestra-gemini-api-key --data-file=gemini.key --project="$INFRA_PROJECT" 2>/dev/null \
  || gcloud secrets versions add orchestra-gemini-api-key --data-file=gemini.key --project="$INFRA_PROJECT"
```

Grant the **raystartup** Cloud Run runtime SA `roles/secretmanager.secretAccessor` on those three secrets.

### 4. Artifact Registry + build + deploy Cloud Run on raystartup

`backend/cloudrun-service.yaml` is already pointed at `raystartup:us-central1:orchestra-trial-pg`.

```bash
cd backend
gcloud artifacts repositories create orchestra \
  --repository-format=docker --location="$REGION" --project="$INFRA_PROJECT" 2>/dev/null || true

TAG=v$(date +%Y%m%d%H%M%S)
IMG=$REGION-docker.pkg.dev/$INFRA_PROJECT/orchestra/api:$TAG
gcloud builds submit --tag "$IMG" --project="$INFRA_PROJECT"

# Substitute IMAGE_PLACEHOLDER → $IMG into .cloudrun-deploy.yaml, then:
gcloud run services replace .cloudrun-deploy.yaml --region="$REGION" --project="$INFRA_PROJECT"

# Preserve live Clerk auth (template may still say AUTH_MODE=demo)
gcloud run services update orchestra-api --region="$REGION" --project="$INFRA_PROJECT" \
  --update-env-vars=AUTH_MODE=clerk,CLERK_JWKS_URL=https://arriving-serval-22.clerk.accounts.dev/.well-known/jwks.json,CLERK_ISSUER=https://arriving-serval-22.clerk.accounts.dev
```

Record new URL:

```bash
gcloud run services describe orchestra-api --region="$REGION" --project="$INFRA_PROJECT" \
  --format='value(status.url)'
# → https://orchestra-api-…….run.app
```

Smoke: `curl -sS "$NEW_URL/api/v1/health"` and `/api/v1/catalog/skus`.

### 5. Point Vercel at the new API

```bash
npx vercel env add NEXT_PUBLIC_API_BASE_URL production --value "$NEW_URL/api/v1" --yes --force --no-sensitive
npx vercel env add NEXT_PUBLIC_API_BASE_URL preview --value "$NEW_URL/api/v1" --yes --force --no-sensitive
npx vercel --prod
```

CORS on Cloud Run must include `https://project-orchestra-khaki.vercel.app` (already in template).

### 6. Cloud Scheduler (timers) — recreate on raystartup

Point the job at `$NEW_URL/api/v1/internal/timers/tick` with OIDC SA in `$INFRA_PROJECT`.

### 7. Tear down paid infra on gen-lang-client (after cutover verified)

**Only after** Vercel + new health + one smoke outcome work:

```bash
# Stop paying for Orchestra Postgres on the GenAI project
gcloud sql instances delete orchestra-pg --project="$AI_PROJECT" --quiet

# Leftover expensive MySQL (if still present)
gcloud sql instances delete raysql --project="$AI_PROJECT" --quiet

# Optional: delete old Cloud Run on gen-lang-client
gcloud run services delete orchestra-api --region="$REGION" --project="$AI_PROJECT" --quiet
```

**Do not** disable GenAI / API keys on `AI_PROJECT` — Gemini traffic should keep using that project’s credits.

## What stays on gen-lang-client

- Gemini / Vertex **usage and GenAI credits**
- Any GenAI-only apps unrelated to Orchestra infra

## What must live on raystartup after cutover

- `orchestra-trial-pg` (Postgres) — **confirmed**
- `orchestra-api` (Cloud Run)
- Artifact Registry `orchestra/api`
- VPC connector `orchestra-vpc` (or whatever connector reaches the instance private IP)
- Secrets for DB / app / Gemini key (key value can still be the GenAI-project key)
- Cloud Scheduler for timer tick

## Repo status after this confirmation

- [x] `INFRA_PROJECT=raystartup` + SQL connection locked in docs + `backend/cloudrun-service.yaml`
- [ ] Founder: deploy Cloud Run in `raystartup` against `orchestra-trial-pg`
- [ ] Founder: flip Vercel `NEXT_PUBLIC_API_BASE_URL`
- [ ] Founder: delete `orchestra-pg` (+ optional old Cloud Run / `raysql`) on gen-lang-client
- [ ] Agent: paste new Cloud Run URL into `docs/DEPLOY_API.md` Live table

## This Cloud Agent cannot execute the move

No `gcloud` binary / GCP credentials in the agent environment. Founder runs the commands above on a machine with access to both projects.
