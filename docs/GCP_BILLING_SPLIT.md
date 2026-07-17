# Dual-project billing split (GenAI vs infra)

> **Why:** `gen-lang-client` has **~95k GenAI free credits** (good for Gemini / Vertex). Infra there (Cloud SQL, Cloud Run, networking) still **bills cash**. The **raystartup** GCP project covers Cloud SQL / Cloud Run / Artifact Registry / networking with savings → **₹0 subtotals**. Put AI usage on gen-lang-client; put Orchestra infra on raystartup.

## Target ownership

| Concern | GCP project | Why |
|---------|-------------|-----|
| **Gemini / Vertex / GenAI API calls** | `gen-lang-client-0795401430` | 95k GenAI credits |
| **Cloud SQL (`orchestra-pg`)** | **raystartup** (`INFRA_PROJECT`) | Infra credits → ₹0 |
| **Cloud Run (`orchestra-api`)** | **raystartup** | Same |
| **Artifact Registry, VPC connector, Cloud Build (API images)** | **raystartup** | Same |
| **Secret Manager (DB URL, SECRET_KEY)** | **raystartup** | Lives with the API |
| **`GEMINI_API_KEY` secret** | Stored in **raystartup** Secret Manager (value from AI Studio / gen-lang-client key) | Cloud Run reads local secret; **usage still bills gen-lang-client** if the key is from that project’s GenAI |

**Founder fill-in (required once):**

```bash
# Project ID from GCP console for the account whose billing shows Cloud SQL/Run at ₹0
# (screenshot label: "raystartup orchestra pg")
export INFRA_PROJECT="<raystartup-project-id>"
export AI_PROJECT=gen-lang-client-0795401430
export REGION=us-central1
```

Until `INFRA_PROJECT` is set and cutover is done, production still runs on `AI_PROJECT` (paying for SQL/Run there).

## Current (wrong for credits) — live until cutover

| Resource | Today |
|----------|--------|
| API | `https://orchestra-api-979112189932.us-central1.run.app` |
| Cloud SQL | `gen-lang-client-0795401430:us-central1:orchestra-pg` |
| Private IP | `10.22.0.5` via connector `orchestra-vpc` |
| Leftover cost | `raysql` MySQL on gen-lang-client — delete after confirm |

## Cutover plan (founder runs `gcloud` — this environment has no GCP credentials)

Do this in one maintenance window. Keep old stack up until new `/health` is green, then flip Vercel, then tear down old infra.

### 0. Prerequisites

```bash
gcloud auth login
gcloud config set project "$INFRA_PROJECT"
# Enable APIs
gcloud services enable \
  run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com \
  artifactregistry.googleapis.com cloudbuild.googleapis.com \
  vpcaccess.googleapis.com compute.googleapis.com \
  --project="$INFRA_PROJECT"
```

### 1. Create Postgres on raystartup (or reuse if `orchestra-pg` already exists there)

```bash
# Skip create if instance already exists in INFRA_PROJECT
gcloud sql instances describe orchestra-pg --project="$INFRA_PROJECT" 2>/dev/null \
  || gcloud sql instances create orchestra-pg \
       --database-version=POSTGRES_16 \
       --tier=db-f1-micro \
       --region="$REGION" \
       --storage-size=10GB \
       --network=default \
       --no-assign-ip \
       --project="$INFRA_PROJECT"

gcloud sql databases create orchestra --instance=orchestra-pg --project="$INFRA_PROJECT" 2>/dev/null || true
gcloud sql users create orchestra --instance=orchestra-pg --password='REDACTED' --project="$INFRA_PROJECT"
```

Prefer private IP + Serverless VPC Access (same pattern as today). Create connector if missing:

```bash
gcloud compute networks vpc-access connectors create orchestra-vpc \
  --region="$REGION" \
  --network=default \
  --range=10.8.0.0/28 \
  --project="$INFRA_PROJECT" 2>/dev/null || true
```

Note the new instance connection name:

```text
$INFRA_PROJECT:$REGION:orchestra-pg
```

### 2. Migrate data (dump old → restore new)

From a machine that can reach **both** instances (Cloud Shell on either project + temporary public IP / Auth proxy, or export via Cloud SQL export to GCS):

```bash
# Example with Cloud SQL Auth Proxy + pg_dump (adjust connection names / passwords)
pg_dump -Fc -h 127.0.0.1 -p 5432 -U orchestra orchestra > orchestra.dump
pg_restore -h 127.0.0.1 -p 5433 -U orchestra -d orchestra --clean --if-exists orchestra.dump
```

**Pilot / empty OK:** skip dump; new Cloud Run with `AUTO_SEED=true` recreates catalog + 10 worker seed. You lose live orders/users unless you dump/restore or re-run Clerk-linked smoke.

### 3. Secrets on raystartup

```bash
# DATABASE_URL: postgresql+asyncpg://USER:PASS@/orchestra  (connector fills host)
python -c "open('tmp','wb').write(b'postgresql+asyncpg://USER:PASS@/orchestra')"
gcloud secrets create orchestra-database-url --data-file=tmp --project="$INFRA_PROJECT" 2>/dev/null \
  || gcloud secrets versions add orchestra-database-url --data-file=tmp --project="$INFRA_PROJECT"
rm tmp

# SECRET_KEY — generate new or copy from old project
openssl rand -hex 32 | tr -d '\n' > tmp
gcloud secrets create orchestra-secret-key --data-file=tmp --project="$INFRA_PROJECT" 2>/dev/null \
  || gcloud secrets versions add orchestra-secret-key --data-file=tmp --project="$INFRA_PROJECT"
rm tmp

# GEMINI_API_KEY — same key that bills under gen-lang-client GenAI credits
# (paste the key bytes; do not commit)
gcloud secrets create orchestra-gemini-api-key --data-file=gemini.key --project="$INFRA_PROJECT" 2>/dev/null \
  || gcloud secrets versions add orchestra-gemini-api-key --data-file=gemini.key --project="$INFRA_PROJECT"
```

Grant the **raystartup** Cloud Run runtime SA `roles/secretmanager.secretAccessor` on those three secrets.

### 4. Artifact Registry + build + deploy Cloud Run on raystartup

Update `backend/cloudrun-service.yaml` connection annotations to:

```yaml
run.googleapis.com/cloudsql-instances: $INFRA_PROJECT:us-central1:orchestra-pg
run.googleapis.com/vpc-access-connector: projects/$INFRA_PROJECT/locations/us-central1/connectors/orchestra-vpc
# env CLOUD_SQL_INSTANCE: same connection name
```

Then:

```bash
cd backend
gcloud artifacts repositories create orchestra \
  --repository-format=docker --location="$REGION" --project="$INFRA_PROJECT" 2>/dev/null || true

TAG=v$(date +%Y%m%d%H%M%S)
IMG=$REGION-docker.pkg.dev/$INFRA_PROJECT/orchestra/api:$TAG
gcloud builds submit --tag "$IMG" --project="$INFRA_PROJECT"

# Substitute IMAGE_PLACEHOLDER + project connection names into .cloudrun-deploy.yaml
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

# Optional: delete old Cloud Run service + Artifact Registry images in AI_PROJECT
gcloud run services delete orchestra-api --region="$REGION" --project="$AI_PROJECT" --quiet
```

**Do not** disable GenAI / API keys on `AI_PROJECT` — Gemini traffic should keep using that project’s credits.

## What stays on gen-lang-client

- Gemini / Vertex **usage and GenAI credits**
- Any GenAI-only apps unrelated to Orchestra infra

## What must live on raystartup after cutover

- `orchestra-pg` (Postgres)
- `orchestra-api` (Cloud Run)
- Artifact Registry `orchestra/api`
- VPC connector `orchestra-vpc`
- Secrets for DB / app / Gemini key (key value can still be the GenAI-project key)
- Cloud Scheduler for timer tick

## Agent / repo follow-up after founder sets `INFRA_PROJECT`

1. Patch `backend/cloudrun-service.yaml` connection names to `$INFRA_PROJECT`.
2. Replace live URLs in `docs/DEPLOY_API.md`.
3. Mark Gate items in `docs/PIPELINE.md` done.
4. Redeploy from `main` so matcher + 10-worker seed are on the new service.

## This Cloud Agent cannot execute the move

No `gcloud` binary / GCP credentials in the agent environment. Founder (or a machine with both projects’ IAM) must run the commands above. Docs + YAML placeholders are prepared so the cutover is mechanical once `INFRA_PROJECT` is known.
