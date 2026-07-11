# Project Orchestra — Full Technical Specification

> **Purpose:** Everything needed to build the platform — databases, APIs, agents, services, events, infrastructure, and build order.
>
> **Companion doc:** `Project_Orchestra_Design_Notes.md` (product model & decisions)
>
> **Architecture principle:** Deterministic **orchestrator spine** + Gemini **reasoning nodes**. AI proposes; spine enforces.

---
# Project Orchestra — Startup Master Plan

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Tech Stack](#2-tech-stack)
3. [Repository Structure](#3-repository-structure)
4. [Database Schema](#4-database-schema)
5. [State Machines](#5-state-machines)
6. [Event System](#6-event-system)
7. [API Contract](#7-api-contract)
8. [AI Agents](#8-ai-agents)
9. [Backend Services](#9-backend-services)
10. [External Integrations](#10-external-integrations)
11. [Security & Compliance](#11-security--compliance)
12. [Infrastructure & Deployment](#12-infrastructure--deployment)
13. [Build Phases](#13-build-phases)
14. [Environment Variables](#14-environment-variables)

---

## 1. System Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                        │
│   Client Portal  │  Worker Dashboard  │  Admin Console           │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST + WebSocket
┌────────────────────────────▼────────────────────────────────────┐
│                    API GATEWAY (FastAPI)                         │
│              Auth · RBAC · Rate limit · Request ID                │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Domain        │   │ ORCHESTRATOR  │   │ AI GATEWAY    │
│ Services      │   │ (State Machine│   │ (Gemini)      │
│               │   │  + Timers)    │   │               │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
              ┌─────────────────────────────┐
              │ PostgreSQL (source of truth) │
              │ Redis (queues + pub/sub)     │
              │ S3/MinIO (files)             │
              │ pgvector (embeddings)        │
              └─────────────────────────────┘
```

### Three runtime layers

| Layer | Role | Technology |
|-------|------|------------|
| **Spine** | State transitions, timers, ledger, policy | Python + PostgreSQL + Redis/workflow |
| **Domain services** | CRUD, business rules, queries | FastAPI modules |
| **AI nodes** | Reasoning at decision points | Gemini via AI Gateway |

---

## 2. Tech Stack

### Backend
| Component | Choice | Why |
|-----------|--------|-----|
| API framework | **FastAPI** | Async, OpenAPI, WebSockets, IITD-familiar |
| ORM | **SQLAlchemy 2.0** + **Alembic** | Migrations, typed models |
| Validation | **Pydantic v2** | Schemas for API + AI outputs |
| Auth | **JWT** + refresh tokens | Stateless API; optional OAuth later |
| Task queue | **Celery** or **ARQ** + Redis | Durable timers, retries |
| Workflow | **Custom state machine** + outbox | Explicit control; no black-box BPM |
| Real-time | **WebSockets** (FastAPI) | Order/task progress |

### Data
| Component | Choice | Why |
|-----------|--------|-----|
| Primary DB | **PostgreSQL 15+** | ACID, JSONB, relations |
| Vector search | **pgvector** extension | Worker/task embeddings in same DB |
| Cache / queue | **Redis 7** | Sessions, pub/sub, job broker |
| Object storage | **S3** or **MinIO** (dev) | Portfolio, submissions, bundles |
| Search (later) | **Meilisearch** or PG full-text | Profile/SKU search at scale |

### AI
| Component | Choice | Why |
|-----------|--------|-----|
| LLM | **Gemini 1.5 Pro** (reasoning) | Scoping, QA, PM loop |
| LLM fast | **Gemini 1.5 Flash** | Scope guard, classification |
| Vision | **Gemini Pro Vision** | Design QA |
| Embeddings | **text-embedding-004** (Google) | Matcher retrieval |
| AI framework | **Thin custom gateway** | Schema validation, tracing, retries |
| RAG store | **pgvector** + template table | Past project patterns |

### Frontend
| Component | Choice | Why |
|-----------|--------|-----|
| Framework | **Next.js 14** (App Router) | SSR, API routes, campus stack |
| Styling | **Tailwind CSS** | Matches design handoff |
| State | **TanStack Query** + Zustand | Server state + UI state |
| Real-time | **native WebSocket** hook | Live tracker |
| Forms | **React Hook Form** + Zod | Typed forms |

### DevOps (MVP)
| Component | Choice |
|-----------|--------|
| Containers | Docker + docker-compose |
| CI | GitHub Actions |
| Deploy | Railway / Render / Cloud Run |
| Monitoring | Sentry + structured logs |
| Secrets | `.env` + platform secret manager |

---

## 3. Repository Structure

```text
gemini_Xprixe/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entry
│   │   ├── config.py               # Settings / env
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── clients.py
│   │   │   │   ├── workers.py
│   │   │   │   ├── intents.py
│   │   │   │   ├── quotes.py
│   │   │   │   ├── orders.py
│   │   │   │   ├── tasks.py
│   │   │   │   ├── discussions.py
│   │   │   │   ├── submissions.py
│   │   │   │   ├── amendments.py
│   │   │   │   ├── taxonomy.py
│   │   │   │   ├── media.py
│   │   │   │   ├── admin.py
│   │   │   │   └── ws.py
│   │   ├── models/                 # SQLAlchemy models
│   │   ├── schemas/                # Pydantic request/response
│   │   ├── services/               # Domain logic
│   │   │   ├── auth_service.py
│   │   │   ├── intent_service.py
│   │   │   ├── quote_service.py
│   │   │   ├── order_service.py
│   │   │   ├── fulfillment_service.py
│   │   │   ├── task_service.py
│   │   │   ├── preference_service.py
│   │   │   ├── discussion_service.py
│   │   │   ├── submission_service.py
│   │   │   ├── qa_service.py
│   │   │   ├── ledger_service.py
│   │   │   ├── worker_profile_service.py
│   │   │   └── notification_service.py
│   │   ├── orchestrator/           # THE SPINE (not AI)
│   │   │   ├── state_machine.py
│   │   │   ├── transitions.py
│   │   │   ├── timers.py
│   │   │   ├── handlers.py         # Event → action
│   │   │   └── policy.py           # Guardrails
│   │   ├── ai/                     # Reasoning nodes
│   │   │   ├── gateway.py          # Gemini client wrapper
│   │   │   ├── spec_compiler.py
│   │   │   ├── risk_classifier.py
│   │   │   ├── pricing_reasoner.py
│   │   │   ├── architect.py
│   │   │   ├── matcher.py
│   │   │   ├── task_packet_generator.py
│   │   │   ├── scope_guard.py
│   │   │   ├── qa_judge.py
│   │   │   ├── pm_control_loop.py
│   │   │   └── dispute_triage.py
│   │   ├── workers_jobs/           # Background jobs
│   │   │   ├── timer_jobs.py
│   │   │   ├── ai_jobs.py
│   │   │   └── notification_jobs.py
│   │   └── db/
│   │       ├── session.py
│   │       └── migrations/         # Alembic
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── (client)/               # Client portal routes
│   │   ├── (worker)/               # Worker dashboard routes
│   │   ├── (admin)/                # Admin console
│   │   └── api/                    # BFF proxies if needed
│   ├── components/
│   ├── lib/
│   └── package.json
├── shared/
│   └── schemas/                    # Shared JSON schemas (optional)
├── docker-compose.yml
├── Project_Orchestra_Design_Notes.md
└── Project_Orchestra_Technical_Spec.md
```

---

## 4. Database Schema

### 4.1 Identity & Trust

```sql
-- users
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255),
    full_name       VARCHAR(255) NOT NULL,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('client','worker','admin')),
    profile_photo_url TEXT,
    phone           VARCHAR(20),
    is_active       BOOLEAN DEFAULT TRUE,
    email_verified  BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- client_profiles
CREATE TABLE client_profiles (
    user_id         UUID PRIMARY KEY REFERENCES users(id),
    organization    VARCHAR(255),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- worker_profiles
CREATE TABLE worker_profiles (
    user_id                 UUID PRIMARY KEY REFERENCES users(id),
    community_type          VARCHAR(20) CHECK (community_type IN ('design','tech','both')),
    headline                VARCHAR(80),
    bio                     TEXT,
    availability_status     VARCHAR(20) DEFAULT 'unavailable'
                            CHECK (availability_status IN ('available','busy','unavailable')),
    weekly_hours_available  INT DEFAULT 0,
    max_concurrent_tasks    INT DEFAULT 2,
    payout_min              DECIMAL(10,2),
    payout_max              DECIMAL(10,2),
    campus_verified         BOOLEAN DEFAULT FALSE,
    is_active               BOOLEAN DEFAULT FALSE,
    profile_completion_pct  INT DEFAULT 0,
    github_url              TEXT,
    figma_url               TEXT,
    behance_url             TEXT,
    linkedin_url            TEXT,
    embedding               VECTOR(768),          -- pgvector
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- worker_stats (materialized / updated on task complete)
CREATE TABLE worker_stats (
    worker_id           UUID PRIMARY KEY REFERENCES worker_profiles(user_id),
    tasks_completed     INT DEFAULT 0,
    on_time_pct         DECIMAL(5,2) DEFAULT 0,
    avg_qa_score        DECIMAL(5,2) DEFAULT 0,
    avg_rating          DECIMAL(3,2) DEFAULT 0,
    response_time_hours DECIMAL(6,2),
    seller_level        VARCHAR(20) DEFAULT 'new'
                        CHECK (seller_level IN ('new','rising','trusted','top')),
    last_active_at      TIMESTAMPTZ,
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.2 Taxonomy (shared language)

```sql
CREATE TABLE skills (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(100) NOT NULL,
    slug        VARCHAR(100) UNIQUE NOT NULL,
    category    VARCHAR(30) CHECK (category IN ('design','frontend','backend','ai_ml','other'))
);

CREATE TABLE tools (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(100) NOT NULL,
    slug        VARCHAR(100) UNIQUE NOT NULL,
    category    VARCHAR(30)
);

CREATE TABLE task_types (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,
    slug            VARCHAR(100) UNIQUE NOT NULL,
    community_type  VARCHAR(20) CHECK (community_type IN ('design','tech','both')),
    description     TEXT,
    default_rubric  JSONB,              -- default QA rubric
    typical_hours   DECIMAL(6,2),
    embedding       VECTOR(768)
);

CREATE TABLE worker_skills (
    worker_id       UUID REFERENCES worker_profiles(user_id),
    skill_id        UUID REFERENCES skills(id),
    proficiency     VARCHAR(20) CHECK (proficiency IN ('beginner','intermediate','advanced','expert')),
    years_experience DECIMAL(4,1),
    PRIMARY KEY (worker_id, skill_id)
);

CREATE TABLE worker_tools (
    worker_id   UUID REFERENCES worker_profiles(user_id),
    tool_id     UUID REFERENCES tools(id),
    proficiency VARCHAR(20),
    PRIMARY KEY (worker_id, tool_id)
);

CREATE TABLE worker_task_types (
    worker_id       UUID REFERENCES worker_profiles(user_id),
    task_type_id    UUID REFERENCES task_types(id),
    proficiency     VARCHAR(20),
    PRIMARY KEY (worker_id, task_type_id)
);

CREATE TABLE portfolio_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id       UUID REFERENCES worker_profiles(user_id),
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    category        VARCHAR(50),
    cover_image_url TEXT,
    project_url     TEXT,
    tags            JSONB DEFAULT '[]',
    tools_used      JSONB DEFAULT '[]',
    is_featured     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.3 Catalog & Quoting

```sql
CREATE TABLE outcome_skus (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug            VARCHAR(100) UNIQUE NOT NULL,
    name            VARCHAR(255) NOT NULL,
    category        VARCHAR(30),        -- design, tech, combined
    description     TEXT,
    base_price      DECIMAL(10,2),
    typical_days    INT,
    revision_limit  INT DEFAULT 2,
    template_spec   JSONB NOT NULL,     -- default OutcomeSpec template
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE intents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       UUID REFERENCES users(id),
    raw_text        TEXT NOT NULL,
    attachments     JSONB DEFAULT '[]',
    status          VARCHAR(30) DEFAULT 'captured',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE outcome_specs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    intent_id           UUID REFERENCES intents(id),
    sku_id              UUID REFERENCES outcome_skus(id),  -- nullable if custom
    outcome_statement   TEXT NOT NULL,
    deliverables        JSONB NOT NULL,       -- [{name, format, required}]
    acceptance_criteria JSONB NOT NULL,       -- [{criterion, check_type, rule}]
    in_scope            JSONB DEFAULT '[]',
    out_of_scope        JSONB DEFAULT '[]',
    assumptions         JSONB DEFAULT '[]',
    client_inputs       JSONB DEFAULT '[]',   -- what client must provide
    risk_tier           VARCHAR(20),          -- L0, L1, L2, L3
    version             INT DEFAULT 1,
    frozen_at           TIMESTAMPTZ,          -- set when order confirmed
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE quotes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    spec_id         UUID REFERENCES outcome_specs(id),
    client_id       UUID REFERENCES users(id),
    price           DECIMAL(10,2) NOT NULL,
    deadline        TIMESTAMPTZ NOT NULL,
    revision_limit  INT DEFAULT 2,
    reserve_amount  DECIMAL(10,2),          -- internal risk reserve
    labor_estimate  DECIMAL(10,2),        -- internal expected payouts
    status          VARCHAR(20) DEFAULT 'issued'
                    CHECK (status IN ('issued','accepted','expired','superseded')),
    valid_until     TIMESTAMPTZ,
    ai_confidence   DECIMAL(4,3),
    ai_rationale    TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.4 Orders & Contracts

```sql
CREATE TABLE outcome_orders (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       UUID REFERENCES users(id),
    quote_id        UUID REFERENCES quotes(id),
    spec_id         UUID REFERENCES outcome_specs(id),
    sku_id          UUID REFERENCES outcome_skus(id),
    status          VARCHAR(30) NOT NULL DEFAULT 'confirmed',
    -- statuses: confirmed, assembling_team, delivery_active,
    --           under_quality_check, delivered, closed,
    --           amendment_pending, escalated, cancelled
    price           DECIMAL(10,2) NOT NULL,
    deadline        TIMESTAMPTZ NOT NULL,
    revision_limit  INT DEFAULT 2,
    progress_pct    INT DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE charters (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id        UUID REFERENCES outcome_orders(id),
    task_id         UUID,                   -- nullable = order-level; set = task-level
    version         INT DEFAULT 1,
    snapshot        JSONB NOT NULL,           -- frozen spec + price + deadline + criteria
    mutual_start_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE amendments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id            UUID REFERENCES outcome_orders(id),
    charter_id          UUID REFERENCES charters(id),
    requested_by        UUID REFERENCES users(id),
    delta_description   TEXT NOT NULL,
    price_delta         DECIMAL(10,2) DEFAULT 0,
    time_delta_hours    INT DEFAULT 0,
    new_criteria        JSONB,
    status              VARCHAR(20) DEFAULT 'requested'
                        CHECK (status IN ('requested','priced','approved','rejected')),
    approved_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.5 Fulfillment (DAG + Tasks)

```sql
CREATE TABLE fulfillment_plans (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id    UUID UNIQUE REFERENCES outcome_orders(id),
    dag_json    JSONB NOT NULL,             -- full graph definition
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE fulfillment_tasks (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id             UUID REFERENCES fulfillment_plans(id),
    order_id            UUID REFERENCES outcome_orders(id),
    task_type_id        UUID REFERENCES task_types(id),
    title               VARCHAR(255) NOT NULL,
    description         TEXT,
    acceptance_criteria JSONB NOT NULL,
    status              VARCHAR(30) NOT NULL DEFAULT 'blocked',
    -- blocked, ready, invited, interest_pool, priority_active,
    -- start_requested, mutual_start, in_progress, submitted,
    -- rework, completed, cancelled
    sequence_order      INT,
    payout_amount       DECIMAL(10,2),
    deadline            TIMESTAMPTZ,
    assigned_worker_id  UUID REFERENCES users(id),
    revision_count      INT DEFAULT 0,
    revision_limit      INT DEFAULT 2,
    priority_window_ends TIMESTAMPTZ,
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE task_dependencies (
    task_id         UUID REFERENCES fulfillment_tasks(id),
    depends_on_id   UUID REFERENCES fulfillment_tasks(id),
    PRIMARY KEY (task_id, depends_on_id)
);

CREATE TABLE preference_sets (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id     UUID REFERENCES fulfillment_tasks(id),
    order_id    UUID REFERENCES outcome_orders(id),
    created_by  UUID REFERENCES users(id),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE preference_entries (
    preference_set_id   UUID REFERENCES preference_sets(id),
    worker_id           UUID REFERENCES users(id),
    rank                INT NOT NULL,       -- 1 = highest
    PRIMARY KEY (preference_set_id, worker_id)
);

CREATE TABLE task_interests (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id     UUID REFERENCES fulfillment_tasks(id),
    worker_id   UUID REFERENCES users(id),
    status      VARCHAR(20) DEFAULT 'accepted'
                CHECK (status IN ('accepted','declined','expired','released')),
    rank_at_accept INT,                     -- their preference rank when accepted
    accepted_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (task_id, worker_id)
);

CREATE TABLE task_activations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         UUID REFERENCES fulfillment_tasks(id),
    worker_id       UUID REFERENCES users(id),
    activation_type VARCHAR(20) CHECK (activation_type IN ('priority','backup')),
    window_starts   TIMESTAMPTZ NOT NULL,
    window_ends     TIMESTAMPTZ NOT NULL,
    status          VARCHAR(20) DEFAULT 'active'
                    CHECK (status IN ('active','used','expired','superseded')),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.6 Delivery & Quality

```sql
CREATE TABLE submissions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         UUID REFERENCES fulfillment_tasks(id),
    worker_id       UUID REFERENCES users(id),
    notes           TEXT,
    asset_urls      JSONB NOT NULL DEFAULT '[]',
    version         INT DEFAULT 1,
    submitted_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE qa_reviews (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id   UUID REFERENCES submissions(id),
    task_id         UUID REFERENCES fulfillment_tasks(id),
    result          VARCHAR(10) CHECK (result IN ('pass','fail')),
    score           DECIMAL(5,2),
    confidence      DECIMAL(4,3),
    feedback        TEXT,
    evidence        JSONB,                  -- per-criterion results
    reviewed_by     VARCHAR(20) DEFAULT 'ai'  -- 'ai' or user_id
                    CHECK (reviewed_by IN ('ai') OR reviewed_by IS NOT NULL),
    human_reviewer_id UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE delivery_bundles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id        UUID REFERENCES outcome_orders(id),
    assets          JSONB NOT NULL,           -- [{name, url, type}]
    qa_summary      JSONB,
    charter_snapshot JSONB,
    delivered_at    TIMESTAMPTZ DEFAULT NOW(),
    accepted_at     TIMESTAMPTZ,
    accepted_by     UUID REFERENCES users(id)
);
```

### 4.7 Communication

```sql
CREATE TABLE discussion_threads (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id     UUID REFERENCES fulfillment_tasks(id),
    order_id    UUID REFERENCES outcome_orders(id),
    status      VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active','archived')),
    opened_at   TIMESTAMPTZ DEFAULT NOW(),
    closed_at   TIMESTAMPTZ
);

CREATE TABLE discussion_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id       UUID REFERENCES discussion_threads(id),
    sender_id       UUID REFERENCES users(id),
    body            TEXT NOT NULL,
    message_type    VARCHAR(30) DEFAULT 'clarification'
                    CHECK (message_type IN (
                        'clarification','reference','scope_change_request',
                        'delivery_update','system'
                    )),
    attachments     JSONB DEFAULT '[]',
    scope_flagged   BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.8 Money (Ledger)

```sql
CREATE TABLE ledger_accounts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code        VARCHAR(50) UNIQUE NOT NULL,
    name        VARCHAR(255) NOT NULL,
    type        VARCHAR(20) CHECK (type IN ('asset','liability','revenue','expense'))
);

CREATE TABLE ledger_entries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id  UUID NOT NULL,          -- groups debit+credit
    account_id      UUID REFERENCES ledger_accounts(id),
    order_id        UUID REFERENCES outcome_orders(id),
    task_id         UUID REFERENCES fulfillment_tasks(id),
    debit           DECIMAL(12,2) DEFAULT 0,
    credit          DECIMAL(12,2) DEFAULT 0,
    description     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE payouts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id       UUID REFERENCES users(id),
    task_id         UUID REFERENCES fulfillment_tasks(id),
    gross_amount    DECIMAL(10,2) NOT NULL,
    tds_amount      DECIMAL(10,2) DEFAULT 0,
    net_amount      DECIMAL(10,2) NOT NULL,
    status          VARCHAR(20) DEFAULT 'pending'
                    CHECK (status IN ('pending','processing','released','failed')),
    released_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE payment_authorizations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id            UUID REFERENCES outcome_orders(id),
    amount              DECIMAL(10,2) NOT NULL,
    provider            VARCHAR(50),        -- razorpay, stripe, etc.
    provider_ref          VARCHAR(255),
    status              VARCHAR(20) DEFAULT 'authorized'
                        CHECK (status IN ('authorized','captured','refunded','failed')),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.9 Platform (events, media, AI logs)

```sql
CREATE TABLE event_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type  VARCHAR(50) NOT NULL,   -- order, task, quote, etc.
    aggregate_id    UUID NOT NULL,
    event_type      VARCHAR(100) NOT NULL,
    actor_id        UUID REFERENCES users(id),
    actor_type      VARCHAR(20),            -- client, worker, system, ai
    payload         JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_event_log_aggregate ON event_log(aggregate_type, aggregate_id);
CREATE INDEX idx_event_log_type ON event_log(event_type);

CREATE TABLE media_assets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uploader_id     UUID REFERENCES users(id),
    filename        VARCHAR(255),
    mime_type       VARCHAR(100),
    storage_key     TEXT NOT NULL,
    url             TEXT,
    size_bytes      BIGINT,
    scanned         BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ai_decision_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name      VARCHAR(50) NOT NULL,
    model_version   VARCHAR(50),
    input_ref       JSONB,                  -- {type, id}
    output          JSONB NOT NULL,
    confidence      DECIMAL(4,3),
    rationale       TEXT,
    policy_result   VARCHAR(20),          -- approved, escalated, rejected
    latency_ms      INT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE project_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku_id          UUID REFERENCES outcome_skus(id),
    name            VARCHAR(255),
    dag_template    JSONB,
    spec_template   JSONB,
    success_count   INT DEFAULT 0,
    embedding       VECTOR(768),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE notifications (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id),
    type        VARCHAR(50),
    title       VARCHAR(255),
    body        TEXT,
    ref_type    VARCHAR(50),
    ref_id      UUID,
    read        BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE dispute_cases (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id        UUID REFERENCES outcome_orders(id),
    task_id         UUID REFERENCES fulfillment_tasks(id),
    raised_by       UUID REFERENCES users(id),
    reason          TEXT,
    status          VARCHAR(20) DEFAULT 'open'
                    CHECK (status IN ('open','investigating','resolved','closed')),
    ai_summary      JSONB,
    resolution      TEXT,
    resolved_by     UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.10 Seed data required at boot

```text
skills          → React, Figma, Logo Design, Python, Tailwind, ...
tools           → Figma, Next.js, VS Code, PyTorch, ...
task_types      → brand_identity, logo_design, figma_ui_design,
                  landing_page_frontend, api_backend, deployment_devops
outcome_skus    → launch_studio, brand_starter, landing_launch
ledger_accounts → client_funds, milestone_reserve, worker_payable,
                  platform_revenue, tds_payable, risk_reserve, refund_payable
```

---

## 5. State Machines

### 5.1 Outcome Order

```text
confirmed
  → assembling_team      (plan + preferences set)
  → delivery_active      (first mutual start)
  → under_quality_check  (all tasks submitted)
  → delivered            (bundle ready)
  → closed               (client accepted / auto-accept)

Branches:
  amendment_pending → delivery_active
  escalated → delivery_active | cancelled
  confirmed → cancelled (pre-start only)
```

### 5.2 Fulfillment Task

```text
blocked → ready                    (dependencies met)
ready → invited                    (preferences set, workers notified)
invited → interest_pool            (≥1 worker accepted interest)
interest_pool → priority_active    (top accepted worker gets window)
priority_active → start_requested  (worker taps Ready to Start)
start_requested → mutual_start     (client/platform confirms)
mutual_start → in_progress
in_progress → submitted
submitted → rework | completed     (QA result)
rework → submitted

priority_active → priority_active  (timeout → promote backup)
priority_active → preferences_exhausted → invited (re-shortlist)

Terminal: completed, cancelled, released (backup superseded)
```

### 5.3 Transition ownership

| Transition | Triggered by | Owner |
|------------|--------------|-------|
| `blocked → ready` | Dependency completed | **Spine** (orchestrator) |
| `ready → invited` | Preferences stored | **Spine** |
| `invited → interest_pool` | Worker accepts | **Spine** (API handler) |
| `interest_pool → priority_active` | Ranking logic | **Spine** + timer job |
| `priority_active → start_requested` | Worker action | **Spine** (API) |
| `start_requested → mutual_start` | Client confirm | **Spine** (API) |
| `submitted → completed` | QA pass | **Spine** (after AI QA node) |
| `submitted → rework` | QA fail | **Spine** |
| `completed → unlock next` | DAG logic | **Spine** |

**AI never calls state transitions directly.** AI returns structured decisions; spine validates and executes.

---

## 6. Event System

### 6.1 Pattern: Transactional Outbox

```text
1. Domain action in DB transaction
2. Insert event_log row in same transaction
3. Outbox worker publishes to Redis queue
4. Orchestrator handlers consume → side effects (notify, timer, AI job)
```

### 6.2 Core events

| Event | Producer | Consumers |
|-------|----------|-----------|
| `IntentCaptured` | Intent API | Spec Compiler job |
| `SpecCompiled` | AI gateway | Risk classifier, quote flow |
| `QuoteIssued` | Quote service | Notify client |
| `OrderConfirmed` | Order API | Plan builder, payment auth |
| `FundsAuthorized` | Payment webhook | Unlock plan generation |
| `PlanApproved` | Architect | Task creation, notify client |
| `PreferencesSet` | Preference API | Procurement / invites |
| `InterestAccepted` | Worker API | Priority logic |
| `ActivationGranted` | Orchestrator | Timer job + notify worker |
| `ActivationExpired` | Timer job | Promote backup |
| `MutualStartConfirmed` | Confirm API | Charter freeze, ledger reserve, open chat |
| `SubmissionReceived` | Submit API | QA Judge job |
| `QualityPassed` | QA service | Payout, unlock deps, notify |
| `QualityFailed` | QA service | Rework notify |
| `AmendmentApproved` | Amendment API | Charter version, replan |
| `OutcomeClosed` | Accept API | Archive, stats update, RAG ingest |

### 6.3 Durable timers (Redis + worker)

| Timer | Duration | Action on expiry |
|-------|----------|------------------|
| `priority_window` | 12–24h (configurable) | Promote backup or exhaust |
| `quote_validity` | 48h | Mark quote expired |
| `client_acceptance` | 72h post-delivery | Auto-accept bundle |
| `sla_breach_check` | continuous (PM loop) | Alert + replan proposal |

---

## 7. API Contract

Base: `/api/v1` · Auth: `Bearer JWT` · All responses: JSON

### 7.1 Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | `{email, password, full_name, role}` |
| POST | `/auth/login` | Returns `{access_token, refresh_token}` |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Current user + role profile |

### 7.2 Taxonomy (public/read)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/taxonomy/skills` | `?category=design` |
| GET | `/taxonomy/tools` | All tools |
| GET | `/taxonomy/task-types` | `?community=tech` |
| GET | `/catalog/skus` | Active outcome SKUs |
| GET | `/catalog/skus/{slug}` | SKU detail + template spec |

### 7.3 Client — Intent & Quote

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/intents` | `{raw_text, attachments[]}` → triggers Spec Compiler |
| GET | `/intents/{id}` | Intent + compiled spec status |
| POST | `/intents/{id}/clarify` | Answer AI clarifying questions |
| GET | `/quotes/{id}` | Outcome proposal (price, deadline, spec) |
| POST | `/quotes/{id}/accept` | Confirm → creates OutcomeOrder |

### 7.4 Client — Orders

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/orders` | List client's orders |
| GET | `/orders/{id}` | Order detail + progress |
| GET | `/orders/{id}/milestones` | Client-facing milestone view |
| GET | `/orders/{id}/delivery` | Delivery bundle when ready |
| POST | `/orders/{id}/accept-delivery` | Final acceptance |
| POST | `/orders/{id}/fund` | Initiate payment authorization |

### 7.5 Client — Preferences

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/orders/{id}/tasks/{task_id}/candidates` | AI-ranked worker shortlist |
| POST | `/orders/{id}/tasks/{task_id}/preferences` | `{ranked_worker_ids: [uuid,...]}` min 3 |

### 7.6 Client — Mutual Start & Discussion

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/tasks/{id}/confirm-start` | Confirm worker ready → mutual start |
| GET | `/tasks/{id}/charter` | Frozen charter for task |
| GET | `/tasks/{id}/discussion` | Thread messages |
| POST | `/tasks/{id}/discussion/messages` | `{body, message_type}` |
| POST | `/orders/{id}/amendments` | Request scope change |
| POST | `/amendments/{id}/approve` | Approve + fund delta |

### 7.7 Worker — Profile

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/workers/profile` | Create worker profile |
| GET | `/workers/profile` | Own profile |
| PUT | `/workers/profile` | Update headline, bio, links |
| PUT | `/workers/profile/skills` | `[{skill_id, proficiency}]` |
| PUT | `/workers/profile/tools` | `[{tool_id, proficiency}]` |
| PUT | `/workers/profile/task-types` | `[{task_type_id, proficiency}]` |
| POST | `/workers/portfolio` | Add portfolio item |
| PATCH | `/workers/profile/availability` | `{status, weekly_hours}` |
| GET | `/workers/profile/completion` | `{pct, missing_fields[]}` |
| POST | `/workers/verify-campus` | IITD email verification |

### 7.8 Worker — Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/workers/me/tasks` | `?status=offered,active` |
| GET | `/workers/me/earnings` | Payout history |
| POST | `/tasks/{id}/accept-interest` | Accept interest (parallel) |
| POST | `/tasks/{id}/decline` | Decline offer |
| POST | `/tasks/{id}/ready-to-start` | Request start (priority holder) |
| GET | `/tasks/{id}/packet` | Task brief + checklist + inputs |
| POST | `/tasks/{id}/submit` | `{notes, asset_urls[]}` |
| GET | `/tasks/{id}/qa-result` | Latest QA feedback |

### 7.9 Media

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/media/upload` | Multipart → `{asset_id, url}` |
| GET | `/media/{id}` | Signed download URL |

### 7.10 Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/orders` | All orders + filters |
| PATCH | `/admin/workers/{id}/verify` | Campus verify |
| GET | `/admin/disputes` | Open dispute cases |
| POST | `/admin/disputes/{id}/resolve` | Human resolution |
| GET | `/admin/ai-decisions` | AI decision audit log |
| POST | `/admin/taxonomy/*` | CRUD skills/tools/task-types |

### 7.11 WebSocket

| Channel | Payload | Who subscribes |
|---------|---------|----------------|
| `order:{id}` | milestone updates, status changes | Client |
| `task:{id}` | state changes, QA result | Worker |
| `user:{id}` | notifications | Both |

```json
// Example WS message
{
  "type": "milestone_updated",
  "order_id": "uuid",
  "milestone": "Brand identity",
  "status": "completed",
  "progress_pct": 40,
  "timestamp": "ISO8601"
}
```

### 7.12 Internal (orchestrator / workers only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/internal/orchestrator/tick` | PM control loop (cron) |
| POST | `/internal/timers/{timer_id}/fire` | Timer callback |
| POST | `/internal/ai/spec-compile` | Async spec job |
| POST | `/internal/ai/qa-review` | Async QA job |
| POST | `/internal/match/workers` | `{task_id}` → ranked list |

---

## 8. AI Agents

### 8.1 Agent registry

| Agent | Model | Trigger | Output schema | Autonomy |
|-------|-------|---------|---------------|----------|
| **Spec Compiler** | Gemini 1.5 Pro | `IntentCaptured` | `OutcomeSpec` | Auto if schema valid |
| **Risk Classifier** | Gemini Flash | `SpecCompiled` | `{risk_tier, feasible, reason}` | Auto; L3 → human |
| **Pricing Reasoner** | Gemini Pro | Spec approved | `{effort_estimates[], rework_prob}` | Inputs only; math prices |
| **Architect** | Gemini 1.5 Pro | `OrderConfirmed` | `FulfillmentPlan` DAG | Auto if DAG valid |
| **Matcher** | Embed + Gemini Pro | Task `ready` | `RankedShortlist[]` | Auto if ≥3 candidates |
| **Task Packet Generator** | Gemini Flash | `MutualStartConfirmed` | `TaskPacket` | Auto |
| **Scope Guard** | Gemini Flash | Each chat message | `{type, scope_drift: bool}` | Auto flag only |
| **QA Judge** | Gemini Pro + Vision | `SubmissionReceived` | `QAReview` | Auto L0/L1; L2 human |
| **PM Control Loop** | Gemini Pro | Cron every 15min | `Intervention[]` | Propose only; spine executes |
| **Dispute Triage** | Gemini Pro | Dispute opened | `CaseSummary` | Human decides |

### 8.2 Spec Compiler (detail)

**Input:**
```json
{
  "intent_text": "I need a brand and landing page for my healthcare startup",
  "attachments": [],
  "sku_hint": "launch_studio",
  "clarifications": []
}
```

**Output (strict schema):**
```json
{
  "outcome_statement": "Launch-ready healthcare startup brand and responsive landing page",
  "deliverables": [
    {"name": "Logo", "format": "SVG+PNG", "required": true},
    {"name": "Brand guide", "format": "PDF", "required": true},
    {"name": "Figma UI", "format": "Figma link", "required": true},
    {"name": "Live landing page", "format": "URL", "required": true}
  ],
  "acceptance_criteria": [
    {"criterion": "Logo delivered in SVG and PNG", "check_type": "deterministic", "rule": "files_include_format(['svg','png'])"},
    {"criterion": "Landing page loads under 3s on mobile", "check_type": "deterministic", "rule": "lighthouse_performance >= 70"},
    {"criterion": "Visual design matches healthcare professional tone", "check_type": "ai_judged", "rubric": "..."},
    {"criterion": "Page is responsive on mobile and desktop", "check_type": "deterministic", "rule": "responsive_check_pass"}
  ],
  "in_scope": ["1 landing page", "2 revision rounds"],
  "out_of_scope": ["CMS", "SEO", "content writing", "mobile app"],
  "assumptions": ["Client provides company name and tagline"],
  "client_inputs_required": ["company_name", "tagline", "reference_sites"],
  "mapped_task_types": ["brand_identity", "logo_design", "figma_ui_design", "landing_page_frontend", "deployment_devops"],
  "clarifying_questions": []
}
```

### 8.3 Architect (detail)

**Output:**
```json
{
  "tasks": [
    {"id": "t1", "task_type": "brand_identity", "title": "Brand direction", "depends_on": [], "payout": 1500, "hours": 4},
    {"id": "t2", "task_type": "logo_design", "title": "Logo design", "depends_on": ["t1"], "payout": 2000, "hours": 6},
    {"id": "t3", "task_type": "figma_ui_design", "title": "UI design", "depends_on": ["t2"], "payout": 3000, "hours": 8},
    {"id": "t4", "task_type": "landing_page_frontend", "title": "Build landing page", "depends_on": ["t3"], "payout": 4000, "hours": 10},
    {"id": "t5", "task_type": "deployment_devops", "title": "Deploy", "depends_on": ["t4"], "payout": 1000, "hours": 2}
  ],
  "critical_path_hours": 30,
  "milestones": [
    {"name": "Brand ready", "task_ids": ["t1","t2"], "client_label": "Brand identity complete"},
    {"name": "Design ready", "task_ids": ["t3"], "client_label": "UI design complete"},
    {"name": "Live site", "task_ids": ["t4","t5"], "client_label": "Website live"}
  ]
}
```

### 8.4 Matcher (detail)

**Pipeline:**
```text
1. Filter: task_type match + availability=available + completion≥70% + capacity
2. Retrieve: pgvector similarity (task embedding ↔ worker embedding), top 20
3. Rerank: Gemini scores each on fit, past QA on this task_type, on_time, complexity
4. Output: top 10 with rationale; client picks ≥3
```

**Output:**
```json
{
  "candidates": [
    {
      "worker_id": "uuid",
      "score": 0.92,
      "rationale": "Expert in logo_design, 12 completed tasks, 95% on-time, strong portfolio in healthcare",
      "availability": "available",
      "seller_level": "trusted"
    }
  ]
}
```

### 8.5 QA Judge (detail)

**Two-layer execution:**
```text
Layer 1 — Deterministic (no AI):
  - Required files/formats present?
  - Build passes? Tests pass?
  - Lighthouse score ≥ threshold?
  - URL reachable?

Layer 2 — AI judged (Gemini):
  - Vision: design matches brief/rubric?
  - Reasoning: code quality, copy alignment?
  - Returns: {result, score, confidence, per_criterion_evidence}
```

**Policy:**
- All deterministic must pass before AI layer runs.
- `confidence < 0.7` → escalate to human reviewer.
- `risk_tier L2+` → always require human sign-off even if AI passes.

### 8.6 AI Gateway (shared wrapper)

```python
# Pseudocode — every agent uses this
async def call_agent(
    agent_name: str,
    model: str,
    prompt: str,
    input_data: dict,
    output_schema: type[BaseModel],
    confidence_threshold: float = 0.75,
) -> AgentResult:
    response = await gemini.generate(
        model=model,
        prompt=prompt,
        response_schema=output_schema,
        temperature=0.2,
    )
    validated = output_schema.model_validate(response)
    log_ai_decision(agent_name, model, input_data, validated, response.confidence)
    if response.confidence < confidence_threshold:
        return AgentResult(output=validated, action="escalate")
    return AgentResult(output=validated, action="approve")
```

---

## 9. Backend Services

| Service | Responsibility | Key methods |
|---------|----------------|-------------|
| **AuthService** | Register, login, JWT, campus verify | `register()`, `verify_token()` |
| **IntentService** | Capture intent, trigger spec compile | `create_intent()`, `add_clarification()` |
| **QuoteService** | Price, issue, accept quotes | `generate_quote()`, `accept_quote()` |
| **OrderService** | Order lifecycle, progress calc | `create_order()`, `update_progress()` |
| **FulfillmentService** | Plan, DAG, dependencies | `build_plan()`, `unlock_ready_tasks()` |
| **TaskService** | Task state, assignments | `transition()`, `assign_worker()` |
| **PreferenceService** | Preferences, interests, activation | `set_preferences()`, `accept_interest()`, `promote_backup()` |
| **DiscussionService** | Threads, messages, scope guard | `open_thread()`, `post_message()` |
| **SubmissionService** | Deliverable uploads | `submit()`, `get_latest()` |
| **QAService** | Run checks, record results | `run_qa()`, `get_result()` |
| **LedgerService** | Double-entry, payouts, TDS | `authorize()`, `reserve()`, `release_payout()` |
| **WorkerProfileService** | Profile CRUD, completion %, embeddings | `upsert_profile()`, `compute_completion()` |
| **NotificationService** | In-app, email, push | `notify()`, `mark_read()` |
| **MediaService** | Upload, scan, signed URLs | `upload()`, `get_signed_url()` |
| **Orchestrator** | State machine, timers, event handlers | `handle_event()`, `fire_timer()` |

---

## 10. External Integrations

| Integration | Purpose | MVP approach |
|-------------|---------|--------------|
| **Gemini API** | All AI agents | Direct API key; gateway wrapper |
| **Razorpay** (India) | Payment authorize/capture/refund | Sandbox for hackathon |
| **Razorpay Route / Payouts** | Worker payouts | Phase 1+ |
| **SendGrid / Resend** | Email notifications | Phase 1 |
| **S3 / MinIO** | File storage | MinIO local; S3 prod |
| **Sentry** | Error tracking | From day 1 |
| **Clerk / Auth0** (optional) | OAuth social login | Later |

---

## 11. Security & Compliance

| Area | Implementation |
|------|----------------|
| Auth | JWT short-lived + refresh; bcrypt passwords |
| RBAC | `client`, `worker`, `admin` middleware on routes |
| Data scope | Workers see only their tasks; clients see only their orders |
| File upload | MIME validation, size limits, virus scan hook |
| Rate limiting | Per-IP + per-user on auth and AI endpoints |
| Audit | Every state change → `event_log` |
| AI safety | Schema validation, confidence gates, no autonomous money actions |
| PII | Encrypt sensitive fields; DPDP consent on signup |
| Secrets | Env vars only; never in code/logs |

---

## 12. Infrastructure & Deployment

### Local dev (docker-compose)

```yaml
services:
  api:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [postgres, redis, minio]

  worker:
    build: ./backend
    command: arq app.workers_jobs.WorkerSettings
    depends_on: [postgres, redis]

  postgres:
    image: pgvector/pgvector:pg15
    volumes: [pgdata:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine

  minio:
    image: minio/minio
    command: server /data

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
```

### Production (Phase 1)
- API + worker: **Cloud Run** or **Railway**
- DB: **Supabase** or **Neon** (managed Postgres + pgvector)
- Redis: **Upstash**
- Storage: **AWS S3** or **Cloudflare R2**
- Frontend: **Vercel**

---

## 13. Build Phases

### Release 1 — Truth layer (Week 1–2)
**Goal:** Profiles, SKUs, intent → spec → quote → order. Manual ops behind UI.

| Build | Tables | APIs | Agents |
|-------|--------|------|--------|
| Auth + users | users, worker_profiles | `/auth/*` | — |
| Taxonomy seed | skills, tools, task_types | `/taxonomy/*`, `/catalog/*` | — |
| Worker profile | worker_skills, portfolio | `/workers/*` | — |
| Intent + spec | intents, outcome_specs | `/intents/*` | Spec Compiler |
| Quote + order | quotes, outcome_orders | `/quotes/*`, `/orders/*` | Risk Classifier, Pricing Reasoner |
| Admin | — | `/admin/*` | — |

### Release 2 — Execution layer (Week 3–4)
**Goal:** Full task lifecycle with preferences, mutual start, QA.

| Build | Tables | APIs | Agents |
|-------|--------|------|--------|
| Fulfillment DAG | fulfillment_plans, fulfillment_tasks, task_dependencies | — | Architect |
| Preferences | preference_sets, preference_entries, task_interests, task_activations | `/preferences`, `/tasks/accept-interest` | Matcher |
| Mutual start | charters | `/tasks/ready-to-start`, `/confirm-start` | Task Packet Generator |
| Discussion | discussion_threads, discussion_messages | `/discussion/*` | Scope Guard |
| Submission + QA | submissions, qa_reviews | `/tasks/submit`, `/qa-result` | QA Judge |
| Orchestrator | event_log | `/internal/*`, WebSocket | — |
| Timers | — | timer jobs | — |

### Release 3 — Market layer (Week 5–6)
**Goal:** Money, disputes, reputation, PM loop.

| Build | Tables | APIs | Agents |
|-------|--------|------|--------|
| Payments | payment_authorizations, ledger_*, payouts | `/orders/fund` | — |
| Delivery | delivery_bundles | `/orders/delivery`, `/accept-delivery` | — |
| Disputes | dispute_cases | `/admin/disputes/*` | Dispute Triage |
| Reputation | worker_stats | — | — |
| PM loop | — | cron `/internal/orchestrator/tick` | PM Control Loop |
| RAG | project_templates | — | Spec Compiler (enhanced) |
| Notifications | notifications | WebSocket `user:{id}` | — |

---

## 14. Environment Variables

```bash
# App
APP_ENV=development
SECRET_KEY=
API_BASE_URL=http://localhost:8000

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/orchestra

# Redis
REDIS_URL=redis://localhost:6379/0

# Storage
S3_ENDPOINT=http://localhost:9000
S3_BUCKET=orchestra-assets
S3_ACCESS_KEY=
S3_SECRET_KEY=

# AI
GEMINI_API_KEY=
GEMINI_MODEL_PRO=gemini-1.5-pro
GEMINI_MODEL_FLASH=gemini-1.5-flash
GEMINI_EMBEDDING_MODEL=text-embedding-004

# Auth
JWT_SECRET=
JWT_EXPIRY_MINUTES=60
JWT_REFRESH_EXPIRY_DAYS=7

# Payments (Phase 1+)
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=

# Email (Phase 1+)
SMTP_URL=

# Monitoring
SENTRY_DSN=

# Policy
PRIORITY_WINDOW_HOURS=24
QUOTE_VALIDITY_HOURS=48
CLIENT_ACCEPTANCE_HOURS=72
PROFILE_COMPLETION_THRESHOLD=70
QA_CONFIDENCE_THRESHOLD=0.75
```

---

## Quick reference: what talks to what

```text
Client UI ──REST/WS──► API Gateway
                          │
Worker UI ──REST/WS──►    │
                          ▼
                    Domain Services ◄──► PostgreSQL
                          │
                          ▼
                    Orchestrator (spine)
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
          Timer Jobs   AI Gateway   Notification
              │           │
              │     ┌─────┴─────┐
              │     ▼     ▼     ▼
              │   Spec  QA   Matcher ...
              │     │
              │     ▼
              │   Gemini API
              ▼
           Redis Queue
```

---

*This spec is the build blueprint. Start with Release 1 tables + APIs, then layer execution, then market.*
