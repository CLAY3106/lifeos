# LifeOS

A personal command center for the overloaded college student. One dashboard that holds academic deadlines, job applications, fitness logs, and spending — with an AI layer that reasons across all four domains and warns you before things fall apart.

Built as a portfolio project to demonstrate full-stack, cloud, and AI engineering skills — incorporating psychological design principles (Paradox of Choice, Endowed Progress, Zeigarnik Effect, Mental Accounting) to reduce decision fatigue and drive follow-through.

> "I built LifeOS because I had a terrible trimester where everything fell apart at once — academics, job search, fitness, and money. I wanted one place that could see across all of those domains and warn me before things got bad."

---

## Live Demo

- **App:** https://lifeos-lac.vercel.app
- **API:** https://lifeos-zggd.onrender.com/docs
- **Demo account:** `demo@lifeos.app` / `demo1234`

---

## What it does

| Module | Features | Psychology |
|---|---|---|
| Academic planner | Assignments, due dates, estimated hours, urgency sorting, weekly load bar, completion progress ring | **Zeigarnik Effect** — open/pending items sort first, done items fade |
| Job hunt tracker | Kanban pipeline — Applied → OA → Interview → Offer, pipeline progress circles | **Endowed Progress** — visual progress through hiring stages |
| Workout log | Quick-add sessions, routines with exercises, streak counter, weekly volume chart, link workouts to routines | — |
| Finance tracker | Envelope budgeting (50/30/20), transactions with search, location tracking, Chart.js breakdown | **Mental Accounting** — 50% needs / 30% wants / 20% savings |
| AI daily briefing | **RAG-grounded** cross-domain insight — deterministic scoring picks the top 3 priorities, hybrid retrieval supplies the evidence, Claude writes the phrasing. Shows retrieval sources and falls back to scoring if AI is down | **Paradox of Choice** — AI reduces 4 domains to 3 actionable items |
| Onboarding | 4-step setup wizard (pick your areas, set limits, quick-add items, first AI briefing), setup checklist on the dashboard, empty states on every page | **Endowed Progress**: the checklist starts partly complete |
| A/B testing | Deterministic SHA-256 bucketing, idempotent exposures, conversion events, and two-proportion z-test results. Live experiment `briefing_quick_complete` tests one-click assignment completion from the briefing | — |
| Activity log | Automatic tracking of workouts, expenses, assignments, job changes | — |
| Profile | View account info, budget settings, weekly capacity | — |

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4 | App Router, React 19 features, CSS-var-driven theme |
| Data Fetching | SWR + Axios | Client-side revalidation, automatic cache |
| Forms | React Hook Form + Zod v4 | Type-safe validation |
| Charts | Chart.js + react-chartjs-2 | Doughnut, bar charts for finance and fitness |
| Backend | FastAPI (Python 3.11) | Async, auto Swagger docs, Pydantic built-in |
| Database | PostgreSQL 18 on Neon (serverless) | Autoscaling compute, branching, generous free tier |
| ORM | SQLAlchemy + Alembic | Schema migrations, ORM queries |
| Auth | JWT (cookies) + bcrypt | Stateless, httpOnly cookies, SameSite=none |
| AI generation | Claude Haiku (Anthropic) | Cross-domain reasoning, cached in DB |
| Retrieval | OpenAI embeddings + PostgreSQL FTS, fused with RRF | Semantic + keyword search; degrades to keyword-only when embeddings are unavailable |
| Experimentation | SHA-256 bucketing + two-proportion z-test | Deterministic assignment, exposure-based denominators, no external service |
| Frontend hosting | Vercel | Zero config, auto-deploys, global CDN |
| Backend hosting | Render.com | Free HTTPS, Docker support, auto-deploys |
| CI/CD | GitHub Actions | Tests, lint, type-check and build on every push and PR; auto deploy on push to main |
| Containers | Docker + Docker Compose | Consistent local dev environment |

---

## Project Structure

```
lifeos/
├── .github/workflows/deploy.yml
├── docker-compose.yml
├── docs/
│   ├── schema.md
│   └── interview-prep-log.md
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   ├── alembic/                    # 9 migrations
│   └── app/
│       ├── main.py                 # Entry point, all routers, CORS, middleware
│       ├── database.py
│       ├── dependencies.py         # get_current_user JWT auth guard
│       ├── seed.py                 # Demo account seeder (runs on container start)
│       ├── models/
│       │   ├── user.py
│       │   ├── assignment.py
│       │   ├── job.py
│       │   ├── workout.py
│       │   ├── expense.py          # + location, group_override
│       │   ├── routine.py          # routines + routine_items
│       │   ├── ai_insight.py
│       │   ├── ai_usage_log.py
│       │   ├── experiment.py       # experiments + exposures + events
│       │   └── activity_log.py
│       ├── schemas/
│       │   ├── user.py             # UserCreate, UserResponse, UserUpdate
│       │   ├── assignment.py
│       │   ├── job.py
│       │   ├── workout.py
│       │   ├── expense.py          # + location in response
│       │   ├── routine.py
│       │   ├── experiment.py       # assignment, event, results contracts
│       │   └── activity_log.py
│       ├── routers/
│       │   ├── auth.py             # register, login, logout, me, patch me
│       │   ├── assignments.py      # CASE sort: pending → overdue → done
│       │   ├── jobs.py             # Kanban pipeline
│       │   ├── workouts.py
│       │   ├── expenses.py         # Returns {expenses, monthly_budget}
│       │   ├── routines.py         # CRUD + nested items
│       │   ├── dashboard.py
│       │   ├── ai.py               # JSON-structured briefing + quick actions
│       │   ├── rag.py              # POST /rag/ingest, POST /rag/search
│       │   ├── experiments.py      # assignment, events, results
│       │   └── activity.py         # GET /activity
│       └── services/
│           ├── auth.py
│           ├── scoring.py          # Deterministic urgency rubric
│           ├── embedding.py        # OpenAI vectors + circuit breaker
│           ├── rag.py              # Chunking, ingestion, hybrid search + RRF
│           ├── context_builder.py  # Aggregates + retrieved evidence
│           ├── experiments.py      # Bucketing, exposure, z-test
│           ├── assignments_service.py
│           ├── expenses_service.py
│           ├── workouts_service.py
│           ├── jobs_service.py
│           ├── routines_service.py
│           └── activity_log_service.py
└── frontend/
    └── src/
        ├── middleware.ts
        ├── app/
        │   ├── globals.css         # Notion-style tokens, dark mode
        │   ├── layout.tsx
        │   └── (app)/
        │       ├── layout.tsx      # Sidebar + Toaster
        │       ├── dashboard/      # AI priorities, charts, activity
        │       ├── assignments/    # Table + progress rings
        │       ├── jobs/           # Kanban board + pipeline progress
        │       ├── fitness/        # Chart.js weekly volume
        │       ├── finance/        # Envelopes + transactions
        │       ├── routines/       # Workout routines
        │       ├── profile/        # Read-only account info
        │       └── not-found.tsx   # Custom 404
        ├── components/
        │   ├── Sidebar.tsx
        │   ├── ThemeToggle.tsx     # Dark mode toggle
        │   ├── icons.tsx           # SVG icon components
        │   ├── primitives.tsx
        │   └── skeletons.tsx       # Loading skeletons
        └── lib/
            ├── api.ts              # Axios client
            └── useExperiment.ts    # Variant evaluation + conversion tracking
```

---

## Architecture

```
Browser (Vercel frontend)
      ↓ /api/* (Vercel rewrites proxy)
Render.com (FastAPI + Docker)
      ↓ SQLAlchemy ORM
Neon PostgreSQL (15 tables)

Briefing pipeline:
  scoring.py ──► top signals ──► retrieval query
                                      ↓
                     document_chunks (vector + BM25 → RRF)
                                      ↓
                     context_builder (aggregates + evidence)
                                      ↓
                     Claude ──► grounded priorities ──► ai_insights (6h cache)

Experiment pipeline:
  GET /experiments/:key ──► SHA-256 bucket ──► exposure (unique per user)
                                      ↓
                     variant ──► treatment UI ──► conversion event
                                      ↓
                     results ──► two-proportion z-test (lift, p-value, CI)

GitHub → GitHub Actions → Render deploy + Vercel deploy
```

**Why Vercel rewrites?**
The frontend (`lifeos-lac.vercel.app`) and backend (`lifeos-zggd.onrender.com`) are on different domains. Cross-domain cookies require `SameSite=none` but browsers still restrict them in some cases. Vercel rewrites proxy all `/api/*` requests through Vercel itself, making the browser think everything is on the same domain — no cross-domain cookie issues.

### A/B testing design

The framework separates three concerns:

1. **Assignment** — `SHA-256(experiment_key:user_id) % 10,000` selects a bucket. It is stable across deploys, devices, and reloads, and the experiment key makes assignments independent per test.
2. **Exposure** — a unique `(experiment_id, user_id)` row records the first time a user saw the variant. Reloads cannot inflate the denominator.
3. **Conversion** — immutable event rows. Results count distinct converted users and ignore events before exposure, so repeated actions do not inflate the numerator.

The results endpoint reports conversion rate, relative lift, absolute lift, a 95% confidence interval, a two-sided p-value from a two-proportion z-test, and a sample-size warning below 30 exposures per arm. See [ADR-007](docs/adr/ADR-007-deterministic-ab-testing.md) for the statistical choices and limitations.

The live experiment, `briefing_quick_complete`, tests whether one-click **Mark done** actions in the briefing increase completed assignments. Control users see the normal briefing; treatment users also see quick actions derived from the same deterministic scores.

---

## Database Schema

15 tables. All tables have `created_at` and `updated_at` timestamps. All tables except `users` and `experiments` have a `user_id` foreign key. All primary keys are UUIDs.

```
users                — id, email, hashed_password, name, monthly_budget, weekly_capacity_hours, onboarding_completed_at, active_modules
assignments          — id, user_id, title, course, due_date, estimated_hours, status, deleted_at
job_applications     — id, user_id, company, role, applied_date, status, followup_date, notes
job_status_history   — id, job_id, from_status, to_status, changed_at, notes
workouts             — id, user_id, routine_id (nullable FK), type, duration_mins, notes, logged_at
routines             — id, user_id, name
routine_items        — id, routine_id (FK cascade), exercise_name, sets, reps, duration_mins, day_of_week
expenses             — id, user_id, amount, category, note, location, spent_at, group_override
ai_insights          — id, user_id, type, content, generated_at
ai_usage_log         — id, user_id, endpoint, model, input_tokens, output_tokens, cost, latency
document_chunks      — id, user_id, entity_type, entity_id, content, embedding, search_vector
experiments          — id, key (unique), name, description, status, variants (JSON), primary_metric, started_at, ended_at
experiment_exposures — id, experiment_id, user_id, variant, first_exposed_at, UNIQUE(experiment_id, user_id)
experiment_events    — id, experiment_id, user_id, variant, event_name, value, event_metadata, occurred_at
activity_logs        — id, user_id, action, entity_type, entity_id, details, created_at
```

`document_chunks.search_vector` is a PostgreSQL generated `tsvector` column used by BM25 ranking. It is deliberately unmapped in SQLAlchemy so the SQLite test suite still works; search code references it only through raw SQL on PostgreSQL.

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Create account, sets JWT cookie |
| POST | `/auth/login` | Login, sets JWT cookie |
| POST | `/auth/logout` | Clears cookie |
| GET | `/auth/me` | Returns current user |
| PATCH | `/auth/me` | Update name, budget, capacity, password, active modules, onboarding completion |
| POST | `/onboarding/events` | Log an onboarding wizard event (started, step completed, skipped, completed, first briefing viewed) |

### Assignments
| Method | Endpoint | Description |
|---|---|---|
| POST | `/assignments` | Create assignment |
| GET | `/assignments` | List (sorted: pending → overdue → done) |
| PATCH | `/assignments/:id` | Update status/details |
| DELETE | `/assignments/:id` | Soft delete (sets deleted_at) |

### Jobs
| Method | Endpoint | Description |
|---|---|---|
| POST | `/jobs` | Create application |
| GET | `/jobs` | List all |
| GET | `/jobs/:id` | Get by ID |
| PATCH | `/jobs/:id` | Update status/details |
| DELETE | `/jobs/:id` | Hard delete |

### Workouts
| Method | Endpoint | Description |
|---|---|---|
| POST | `/workouts` | Log workout |
| GET | `/workouts` | List all |
| DELETE | `/workouts/:id` | Delete |

### Routines
| Method | Endpoint | Description |
|---|---|---|
| POST | `/routines` | Create routine |
| GET | `/routines` | List with items |
| GET | `/routines/:id` | Get by ID |
| PATCH | `/routines/:id` | Update |
| DELETE | `/routines/:id` | Delete |
| POST | `/routines/:id/items` | Add exercise to routine |
| DELETE | `/routines/:id/items/:item_id` | Remove exercise |

### Expenses
| Method | Endpoint | Description |
|---|---|---|
| POST | `/expenses` | Log expense |
| GET | `/expenses` | List (returns `{expenses, monthly_budget}`) |
| PATCH | `/expenses/:id` | Update |
| DELETE | `/expenses/:id` | Delete |

### Dashboard & AI
| Method | Endpoint | Description |
|---|---|---|
| GET | `/dashboard` | Aggregate summary across all modules |
| POST | `/ai/briefing` | RAG-grounded daily insight (priorities + summary + retrieval metadata) |
| POST | `/ai/weekly` | Weekly digest |
| POST | `/ai/refresh` | Force regenerate |

### RAG (retrieval index)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/rag/ingest` | Rebuild the authenticated user's search index |
| POST | `/rag/search` | Hybrid search (vector + BM25 → RRF); keyword-only if embeddings are unavailable |

### Experiments
| Method | Endpoint | Description |
|---|---|---|
| GET | `/experiments/:key` | Evaluate the current user's variant and record exposure (idempotent) |
| POST | `/experiments/:key/events` | Log a conversion event; variant is resolved server-side |
| GET | `/experiments/:key/results` | Exposure/conversion rates, lift, 95% CI, and p-value |

### Activity
| Method | Endpoint | Description |
|---|---|---|
| GET | `/activity` | Recent activity log |

---

## Local Development

### Prerequisites
- Docker Desktop
- Node.js 18+
- Python 3.11+

### Run locally

```bash
# Boot Postgres + API (auto-runs migrations + seeds demo user)
docker compose up --build

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |

### Run tests

```bash
cd backend
python -m pytest tests/ -v
```

---

## Retrieval & AI Quality

The AI layer is measured, not just shipped.

### Retrieval eval

`backend/eval/` holds a labeled benchmark: 30 queries over a fixed 36-item student dataset, split into **lexical** (exact names and codes), **semantic** (paraphrases with no shared words), and **mixed** queries. It scores vector-only, keyword-only, and hybrid (RRF) retrieval on recall@5, MRR@5, hit@1, and latency.

```bash
cd backend
# Real numbers: Postgres full-text search + OpenAI embeddings
DATABASE_URL=postgresql+psycopg://... OPENAI_API_KEY=sk-... python -m eval.retrieval_eval
# Offline smoke run, no API key
python -m eval.retrieval_eval --embedder fake
```

**What it caught:** keyword search used `plainto_tsquery`, which ANDs every word, so a natural question like "upcoming interviews" matched nothing unless one chunk contained both words. Switching to OR-ed lexemes (still ranked by `ts_rank_cd`) moved keyword-only results on Postgres:

| Keyword search | Recall@5 | Mixed queries | Exact-match queries |
|---|---|---|---|
| Before (AND) | 0.417 | 0.25 | 1.00 |
| After (OR) | 0.683 | 0.75 | 1.00 |

### Cost tracking

Every briefing logs input/output tokens, latency, and estimated USD cost to `ai_usage_log`. Prices live in one table (`app/services/ai_cost.py`); an earlier version priced Haiku 4.5 at old Claude 3 Haiku rates and under-reported cost 4x. A typical briefing (~900 tokens in, ≤300 out) costs about **$0.0024**. The 6-hour cache keeps normal use to about 4 paid calls per user per day (**~$0.29 per user per month**), and the cache-bypassing `/ai/refresh` is rate-limited to 10 calls per day per IP, so a client looping it can't drain the API budget. When the API is down or unconfigured, deterministic scoring produces the top-3 priorities at no cost.

### Tests

`backend/tests/test_rag.py` covers chunking, ingestion (soft-delete skip, idempotent rebuild, embedding outage), per-user isolation, entity filters, keyword-only degradation, and RRF ordering, using a fake embedder so CI needs no API key.

## Architecture Decision Records

Key technical decisions documented with full context and tradeoffs:

- [ADR-001](docs/adr/ADR-001-fastapi.md) — FastAPI over Django / Express
- [ADR-002](docs/adr/ADR-002-multi-user-auth.md) — Multi-user auth from day 1
- [ADR-003](docs/adr/ADR-003-cache-ai-responses.md) — Cache AI responses in database
- [ADR-004](docs/adr/ADR-004-vercel-aws-eb.md) — Vercel + AWS Elastic Beanstalk (original)
- [ADR-005](docs/adr/ADR-005-event-sourcing-jobs.md) — Event sourcing for job status changes
- [ADR-006](docs/adr/ADR-006-rag-grounded-briefing.md) — Ground the AI briefing in retrieved records
- [ADR-007](docs/adr/ADR-007-deterministic-ab-testing.md) — Deterministic A/B testing with exposure-based analysis

---

## Infrastructure Notes

Originally deployed to AWS (Elastic Beanstalk + RDS). Migrated to Render.com because:
- EB free tier does not support HTTPS — requires an Application Load Balancer (~$18/month)
- HTTPS is required for cross-origin cookies between Vercel (HTTPS) and the API
- Render provides free HTTPS with Docker support out of the box

AWS skills demonstrated during the project: IAM least-privilege, RDS PostgreSQL, security groups, VPC networking, CloudWatch logging, SSM Parameter Store, Elastic Beanstalk Docker deployment.

In a production environment with a budget, the correct AWS setup would be: EB + ALB + ACM certificate for HTTPS termination, with RDS in a private subnet accessible only from the EB security group.

---

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET` | Secret key for signing JWT tokens |
| `ANTHROPIC_API_KEY` | Claude API key |

---

## Post-MVP Roadmap

- Email / push notifications (SendGrid)
- Google Calendar sync (OAuth + GCal API)
- Recurring tasks (background jobs)
- Refresh token rotation
- Mobile app (React Native)
- Data export (CSV / PDF)
- Terraform / IaC

---

## Author

Son Le — Kalamazoo College 2028
[github.com/CLAY3106](https://github.com/CLAY3106) | Son.LeDinhTruong24@kzoo.edu
