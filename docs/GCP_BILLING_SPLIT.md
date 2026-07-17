# Dual-project billing split (strict credit rules)

> **raystartup free trial (strict):** ₹28,219.33 until **2026-10-12**. Covers first-party GCP (Cloud Run, Cloud SQL, Storage, Artifact Registry) **and** Vertex AI API (first-party Gemini, AutoML, training, pipelines). Does **not** cover Gemini Developer API (AI Studio), partner MaaS, Marketplace, premium OS licenses, or Workspace/domains.
>
> **gen-lang-client ₹95.7k (strict):** GenAI App Builder credit — **only** Vertex AI Agent Builder **Search** + **Conversation**. Does **not** cover Cloud Run/SQL or standalone Gemini SDK / Model Garden.

## Credit matrix (do not guess)

### gen-lang-client — GenAI App Builder trial ₹95,700 (100% remaining)

| Covered by credit (₹0 out-of-pocket) | **Not** covered (you pay) |
|--------------------------------------|---------------------------|
| **Vertex AI Search** — queries, document indexing (PDF/HTML/web), datastore storage | **Cloud Run**, Artifact Registry, **Cloud SQL**, standard Cloud Storage |
| **Vertex AI Conversation** — multi-turn Agent Builder / Dialogflow CX sessions | **Standalone Gemini** via SDKs or **Vertex AI Model Garden** (e.g. Flash/Pro `generate_content`) |
| | **Networking** — static IPs, egress, load balancing |

### raystartup — GCP free trial ₹28,219.33 · until **2026-10-12**

Track usage anytime in the Google Cloud Billing Report Dashboard.

| **Covered by trial credits** (eligible) | **Not covered** (direct charge) |
|-----------------------------------------|----------------------------------|
| **First-party GCP:** Cloud Run, Cloud SQL, Cloud Storage, Artifact Registry | **Gemini Developer API (AI Studio)** and partner Model-as-a-Service APIs |
| **Vertex AI API:** first-party Gemini models, AutoML, custom training, pipeline executions | **Marketplace** third-party software / SaaS |
| | **Premium OS** VM licenses (Windows, RHEL, SUSE, SQL Server, etc.) |
| | **Google Workspace** + domain registration |

**GPU/TPU note:** Adding GPUs/TPUs to VMs requires upgrading the billing account; after upgrade, remaining trial credits still offset **eligible** usage.

**Orchestra implication on raystartup:** use **Vertex AI** (first-party Gemini via ADC / Model Garden) — **never** Gemini Developer API / AI Studio API keys. Cloud Run + `orchestra-trial-pg` + Vertex Gemini are all trial-eligible.

## Confirmed targets

| Concern | Value |
|---------|--------|
| **Orchestra host project** | `raystartup` — free trial ₹28,219.33 until **2026-10-12** |
| **Cloud SQL** | `raystartup:us-central1:orchestra-trial-pg` |
| **Standalone Gemini** | **Vertex AI on `raystartup`** (first-party models — trial-eligible). **Not** Gemini Developer API / AI Studio |
| **gen-lang-client** | **Agent Builder Search / Conversation only** (₹95.7k) — not Orchestra host/SDK |
| **AI auth** | `GEMINI_AUTH=vertex`, **no** `GEMINI_API_KEY` / AI Studio |

```bash
export INFRA_PROJECT=raystartup
export AGENT_BUILDER_PROJECT=gen-lang-client-0795401430   # Search/Conversation only
export REGION=us-central1
export SQL_INSTANCE=orchestra-trial-pg
export SQL_CONNECTION=raystartup:us-central1:orchestra-trial-pg
# Orchestra Gemini bills here (free trial), NOT gen-lang-client:
export VERTEX_PROJECT=raystartup
```

## End-to-end flow (target)

```text
Browser (Vercel)
    │  Clerk JWT
    ▼
Cloud Run orchestra-api                 ← project: raystartup (free trial ✅)
    │
    ├─► Cloud SQL orchestra-trial-pg    ← raystartup (free trial ✅)
    │
    └─► Vertex AI Gemini (first-party)  ← vertexai=True, project=raystartup
                                          SA ADC — NO AI Studio / Developer API key
                                          (trial covers Vertex AI Gemini ✅)

FORBIDDEN on raystartup (direct charge / wrong API):
    Gemini Developer API (AI Studio) API keys
    Marketplace / partner MaaS / Workspace

OPTIONAL later (burns ₹95.7k on gen-lang-client):
    Agent Builder Search / Conversation ← only if product uses those consoles
```

| Step | What happens |
|------|----------------|
| 1 | User hits Vercel |
| 2 | API on **raystartup** Cloud Run (trial-eligible) |
| 3 | DB = **`orchestra-trial-pg`** on raystartup (trial-eligible) |
| 4 | Scope / quote / matcher / QA = **Vertex AI Gemini on `raystartup`** (trial-eligible) |
| 5 | **Never** use Gemini Developer API / AI Studio keys (not trial-eligible; also wrong for ₹95.7k) |
| 6 | gen-lang-client stays for **Agent Builder Search/Conversation** only |

### App config (standalone Gemini on raystartup)

```text
GEMINI_AUTH=vertex
VERTEX_PROJECT=raystartup
VERTEX_LOCATION=us-central1
# No GEMINI_API_KEY
```

```python
from google import genai
client = genai.Client(
    vertexai=True,
    project="raystartup",
    location="us-central1",
)
# ADC = Cloud Run runtime SA in raystartup → roles/aiplatform.user on raystartup
```

Enable Vertex on raystartup:

```bash
gcloud services enable aiplatform.googleapis.com --project=raystartup
```

Grant the Cloud Run runtime SA `roles/aiplatform.user` **on raystartup** (same project — no cross-project needed for Orchestra SDK calls).

## What must NOT run on gen-lang-client (Orchestra)

- Cloud Run (`orchestra-api`)
- Cloud SQL (`orchestra-pg` — delete after cutover)
- Artifact Registry for Orchestra images
- Standalone Gemini / Model Garden SDK calls for Orchestra
- Networking dedicated to Orchestra

## What MAY run on gen-lang-client

- **Vertex AI Agent Builder → Search** (indexing, queries, datastores)
- **Vertex AI Agent Builder → Conversation** (Dialogflow CX / agent chat in that console)
- Only when product deliberately uses those surfaces to consume the ₹95.7k credit

## Today vs target

| | **Today (live)** | **Target** |
|--|------------------|------------|
| API + DB | gen-lang-client `orchestra-pg` — **paying** | raystartup `orchestra-trial-pg` — **₹0 trial** |
| Standalone Gemini | Appears as Gemini API / Vertex lines on gen-lang-client — **cash** (₹95.7k does not apply) | Vertex on **raystartup** (trial covers while active) |
| ₹95.7k GenAI App Builder | 100% unused — correct, we are not in Agent Builder Search/Conversation | Keep unused until we ship Agent Builder features |
| Auth | Repo still `api_key=` client; prefer Vertex ADC | `vertexai=True`, project=`raystartup` |

### gen-lang-client July billing snapshot

| Service | Subtotal (≈) | Correct home |
|---------|--------------|--------------|
| Cloud SQL | ₹127 | **raystartup** |
| Cloud Run | ₹52 | **raystartup** |
| Gemini API | ₹42 | **raystartup** (standalone — not ₹95.7k) |
| Artifact Registry | ₹17 | **raystartup** |
| Vertex AI | ₹9 | **raystartup** if Model Garden; Agent Builder only on gen-lang-client |
| **GenAI App Builder trial** | ₹95,700 @ 100% | Search + Conversation **only** |

### raystartup billing snapshot (Jul 1–17)

| | |
|--|--|
| **Free trial** | **₹28,219.33** remaining · expires **2026-10-12** |
| **Net** | ₹232 − ₹232 = **₹0.00** |

| Service | After savings | Trial-eligible? |
|---------|---------------|-----------------|
| Cloud Run | **₹0** | Yes |
| Cloud SQL | **₹0** | Yes |
| AR / Storage / Build | **₹0** | Yes |
| Vertex AI Gemini (add for Orchestra) | — | Yes (first-party Vertex) |
| Gemini Developer API / AI Studio | — | **No — do not use** |

## Ownership table

| Concern | Project | Why |
|---------|---------|-----|
| Cloud SQL `orchestra-trial-pg` | `raystartup` | Trial → ₹0 |
| Cloud Run `orchestra-api` | `raystartup` | Trial → ₹0 |
| Artifact Registry, VPC, Scheduler, DB secrets | `raystartup` | Same |
| Standalone Vertex AI Gemini (Orchestra) | `raystartup` | Free trial covers first-party Vertex Gemini |
| Agent Builder Search / Conversation | `gen-lang-client-0795401430` | **Only** place ₹95.7k applies |
| Gemini Developer API / AI Studio | **nowhere for Orchestra** | Not covered by raystartup trial; not ₹95.7k |

## Cutover plan (founder — no gcloud in this agent)

Keep old stack until new `/health` is green, then flip Vercel, then tear down gen-lang-client Orchestra infra.

### 0. Prerequisites

```bash
export INFRA_PROJECT=raystartup
export REGION=us-central1
gcloud auth login
gcloud config set project "$INFRA_PROJECT"
gcloud services enable \
  run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com \
  artifactregistry.googleapis.com cloudbuild.googleapis.com \
  vpcaccess.googleapis.com compute.googleapis.com aiplatform.googleapis.com \
  --project="$INFRA_PROJECT"
```

### 1. Reuse `orchestra-trial-pg`

```bash
gcloud sql instances describe orchestra-trial-pg --project="$INFRA_PROJECT"
gcloud sql databases list --instance=orchestra-trial-pg --project="$INFRA_PROJECT"
```

VPC connector if missing:

```bash
gcloud compute networks vpc-access connectors describe orchestra-vpc \
  --region="$REGION" --project="$INFRA_PROJECT" 2>/dev/null \
  || gcloud compute networks vpc-access connectors create orchestra-vpc \
       --region="$REGION" --network=default --range=10.8.0.0/28 \
       --project="$INFRA_PROJECT"
```

### 2. Data migrate (optional)

Pilot/empty OK with `AUTO_SEED=true`. Otherwise `pg_dump` old `orchestra-pg` → restore into `orchestra-trial-pg`.

### 3. Secrets on raystartup (DB + app only — no Gemini API key)

```bash
# DATABASE_URL + SECRET_KEY only
# Grant Cloud Run SA secretAccessor + roles/aiplatform.user on raystartup
```

### 4. Deploy Cloud Run on raystartup

`backend/cloudrun-service.yaml` → SQL `orchestra-trial-pg`, `VERTEX_PROJECT=raystartup`.

```bash
cd backend
TAG=v$(date +%Y%m%d%H%M%S)
IMG=$REGION-docker.pkg.dev/$INFRA_PROJECT/orchestra/api:$TAG
gcloud builds submit --tag "$IMG" --project="$INFRA_PROJECT"
# substitute IMAGE_PLACEHOLDER → replace service
gcloud run services replace .cloudrun-deploy.yaml --region="$REGION" --project="$INFRA_PROJECT"
# Clerk env update as today
```

### 5. Flip Vercel → new Cloud Run URL

### 6. Tear down Orchestra on gen-lang-client

```bash
gcloud sql instances delete orchestra-pg --project=gen-lang-client-0795401430 --quiet
gcloud sql instances delete raysql --project=gen-lang-client-0795401430 --quiet   # if unused
gcloud run services delete orchestra-api --region=us-central1 \
  --project=gen-lang-client-0795401430 --quiet
```

Leave gen-lang-client for **Agent Builder** work only.

## Repo status

- [x] Credit rules documented (both accounts)
- [x] Code: `genai.Client(api_key=…)` → Vertex ADC via `GEMINI_AUTH=vertex` / `VERTEX_PROJECT=raystartup`
- [x] Deploy template: no `GEMINI_API_KEY`; Vertex env on raystartup
- [ ] Founder: deploy + Vercel flip + delete paid SQL/Run on gen-lang-client
- [ ] Later (optional): Agent Builder features on gen-lang-client to use ₹95.7k

## This Cloud Agent cannot execute GCP cutover

No `gcloud` / credentials here. Founder runs the commands on a machine with access to both projects.
