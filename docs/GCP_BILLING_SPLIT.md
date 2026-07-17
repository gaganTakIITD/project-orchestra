# Dual-project billing split (GenAI vs infra)

> **Why:** `gen-lang-client` has **~95k GenAI free credits** (good for Gemini / Vertex). Infra there (Cloud SQL, Cloud Run, networking) still **bills cash**. **raystartup** has the **~30k infra free credits** — Cloud SQL / Cloud Run / Artifact Registry / networking hit those and show **₹0 subtotals**. Put AI usage on gen-lang-client; put Orchestra infra on raystartup.
>
> **AI auth rule:** **Do not use a raw Gemini / AI Studio API key** in prod. Call **Vertex AI Gemini** with the Cloud Run **service account** (ADC). No `GEMINI_API_KEY` secret on Cloud Run.

## Confirmed targets

| Concern | Value |
|---------|--------|
| **AI project (95k GenAI credits)** | `gen-lang-client-0795401430` |
| **Infra project (30k free credits)** | `raystartup` |
| **Infra Cloud SQL** | `raystartup:us-central1:orchestra-trial-pg` — instance **on the 30k-credit project** |
| **Region** | `us-central1` |
| **AI auth** | Vertex AI + Cloud Run SA (ADC) — **not** a pasted API key |

```bash
export INFRA_PROJECT=raystartup
export AI_PROJECT=gen-lang-client-0795401430
export REGION=us-central1
export SQL_INSTANCE=orchestra-trial-pg
export SQL_CONNECTION=raystartup:us-central1:orchestra-trial-pg
```

## End-to-end flow (target)

```text
Browser (Vercel)
    │  Clerk JWT
    ▼
Cloud Run orchestra-api          ← project: raystartup (30k infra credits)
    │  Postgres via connector
    ▼
Cloud SQL orchestra-trial-pg     ← raystartup:us-central1:orchestra-trial-pg

Cloud Run (same revision)
    │  Vertex Gemini call as runtime SA (ADC — no API key)
    │  vertexai=True, project=gen-lang-client-0795401430
    ▼
Vertex AI / Gemini               ← bills gen-lang-client (95k GenAI credits)
```

| Step | What happens |
|------|----------------|
| 1 | User hits Vercel frontend |
| 2 | API calls go to Cloud Run in **`raystartup`** |
| 3 | API reads/writes **`orchestra-trial-pg`** (30k credits) |
| 4 | Scope / quote / matcher / QA call **Vertex Gemini** using the Cloud Run service account |
| 5 | Those AI calls are attributed to **`gen-lang-client`** so the **95k GenAI** pool applies |
| 6 | No AI Studio key in Secret Manager; SA needs `roles/aiplatform.user` on the AI project |

### Cross-project IAM (required for no-API-key)

Cloud Run runs in `raystartup`, but Vertex must bill/use `gen-lang-client`:

```bash
# Runtime SA of Cloud Run in raystartup (example — use the real SA email)
RUNTIME_SA="$(gcloud run services describe orchestra-api \
  --region=$REGION --project=$INFRA_PROJECT \
  --format='value(spec.template.spec.serviceAccountName)')"
# If empty, default compute SA: PROJECT_NUMBER-compute@developer.gserviceaccount.com

gcloud projects add-iam-policy-binding "$AI_PROJECT" \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/aiplatform.user"
```

Enable Vertex on the AI project:

```bash
gcloud services enable aiplatform.googleapis.com --project="$AI_PROJECT"
```

App config (target — replace API-key path in code):

```text
GEMINI_AUTH=vertex          # not api_key
VERTEX_PROJECT=gen-lang-client-0795401430
VERTEX_LOCATION=us-central1
# No GEMINI_API_KEY in production
```

Client shape (`google-genai`):

```python
from google import genai
client = genai.Client(
    vertexai=True,
    project=settings.vertex_project,   # gen-lang-client-0795401430
    location=settings.vertex_location, # us-central1
)
# Uses Application Default Credentials = Cloud Run service account
```

### Today vs target (honest)

| | **Today (live on gen-lang-client)** | **Target** |
|--|-------------------------------------|------------|
| API + DB | `orchestra-pg` + Cloud Run — **paying** (SQL ₹127, Run residual ₹52 in Jul snapshot) | raystartup `orchestra-trial-pg` + Cloud Run — **30k infra** |
| AI billing lines | **Both** appear: Gemini API (~₹42) + Vertex AI (~₹9) | Prefer **Vertex only** on gen-lang-client so GenAI App Builder credits can apply |
| GenAI App Builder credit | **₹95,700 still 100% remaining** — not offsetting the paid Gemini/Vertex/SQL lines above | Route AI through Vertex SKUs that the trial credit covers; keep infra off this project |
| Orchestra **repo** AI client | `genai.Client(api_key=…)` in `gateway.py` / `scope_guard.py` | `genai.Client(vertexai=True, project=gen-lang-client-…)` via Cloud Run SA |

**Auth note (looked back):** The committed deploy template historically bound env `GEMINI_API_KEY` ← Secret Manager `orchestra-gemini-api-key`, and the Python client always used `api_key=`. That does **not** prove a key was pasted in the live console — live env can differ from git. Billing **does** show a **Gemini API** line (typical Generative Language / AI Studio path) **and** a smaller **Vertex AI** line on the same project. Target remains: **Vertex + SA only, no raw API key.**

### gen-lang-client July billing snapshot (founder)

| Service | Subtotal (≈) | Notes |
|---------|--------------|--------|
| Cloud SQL | ₹127 | **Move off** → raystartup |
| Cloud Run | ₹52 after savings | **Move off** → raystartup |
| Gemini API | ₹42 | AI — keep on this project; align to Vertex/credit SKU |
| Artifact Registry | ₹17 | Move with Cloud Run |
| Vertex AI | ₹9 | AI — keep; prefer this path |
| Networking | ₹0 after savings | — |
| **GenAI App Builder trial** | ₹95,700 remaining (100%) | Available — not consuming the infra lines above |

Infra (SQL/Run/AR) should leave this project. AI stays here under the GenAI offer.

## Target ownership

| Concern | GCP project | Why |
|---------|-------------|-----|
| **Gemini / Vertex / GenAI API calls** | `gen-lang-client-0795401430` | 95k GenAI credits via **Vertex + SA** (no API key) |
| **Cloud SQL (`orchestra-trial-pg`)** | `raystartup` (30k credits) | Free infra credits → ₹0 |
| **Cloud Run (`orchestra-api`)** | `raystartup` | Same |
| **Artifact Registry, VPC connector, Cloud Build (API images)** | `raystartup` | Same |
| **Secret Manager (DB URL, SECRET_KEY only)** | `raystartup` | **Do not** store a Gemini API key |
| **AI identity** | Cloud Run runtime SA → `roles/aiplatform.user` on gen-lang-client | ADC / Vertex |

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

### 3. Secrets on raystartup (DB + app only — **no Gemini API key**)

```bash
# DATABASE_URL: postgresql+asyncpg://USER:PASS@/DBNAME  (connector fills host)
python -c "open('tmp','wb').write(b'postgresql+asyncpg://USER:PASS@/orchestra')"
gcloud secrets create orchestra-database-url --data-file=tmp --project="$INFRA_PROJECT" 2>/dev/null \
  || gcloud secrets versions add orchestra-database-url --data-file=tmp --project="$INFRA_PROJECT"
rm tmp

openssl rand -hex 32 | tr -d '\n' > tmp
gcloud secrets create orchestra-secret-key --data-file=tmp --project="$INFRA_PROJECT" 2>/dev/null \
  || gcloud secrets versions add orchestra-secret-key --data-file=tmp --project="$INFRA_PROJECT"
rm tmp

# DO NOT create orchestra-gemini-api-key for production.
# Use Vertex + Cloud Run SA instead (see "Cross-project IAM" above).
```

Grant the **raystartup** Cloud Run runtime SA `roles/secretmanager.secretAccessor` on **database-url** and **secret-key** only. Then grant that SA `roles/aiplatform.user` on `$AI_PROJECT`.

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
- Secrets for DB / app only (**no** Gemini API key)
- Cloud Run SA → `roles/aiplatform.user` on gen-lang-client
- Cloud Scheduler for timer tick

## Repo status after this confirmation

- [x] `INFRA_PROJECT=raystartup` + SQL `orchestra-trial-pg` locked in docs + deploy YAML
- [x] Policy: **no direct Gemini API key** — Vertex + SA (documented)
- [ ] Code: switch `genai.Client(api_key=…)` → Vertex ADC (`GEMINI_AUTH=vertex`)
- [ ] Founder: IAM + deploy Cloud Run in `raystartup` against `orchestra-trial-pg`
- [ ] Founder: flip Vercel `NEXT_PUBLIC_API_BASE_URL`
- [ ] Founder: delete `orchestra-pg` (+ optional old Cloud Run / `raysql`) on gen-lang-client
- [ ] Agent: paste new Cloud Run URL into `docs/DEPLOY_API.md` Live table
- [ ] Remove `GEMINI_API_KEY` / `orchestra-gemini-api-key` from Cloud Run after Vertex lands

## This Cloud Agent cannot execute the move

No `gcloud` binary / GCP credentials in the agent environment. Founder runs the commands above on a machine with access to both projects.
