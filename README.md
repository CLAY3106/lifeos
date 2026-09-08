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
| AI daily briefing | Cross-domain insight — top 3 priorities (numbered cards), summary toggle, flags overload, notices tensions | **Paradox of Choice** — AI reduces 4 domains to 3 actionable items |
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
| Database | PostgreSQL 15 on Render | Reliable, free tier, same network as API |
| ORM | SQLAlchemy + Alembic | Schema migrations, ORM queries |
| Auth | JWT (cookies) + bcrypt | Stateless, httpOnly cookies, SameSite=none |
| AI | Claude (Anthropic) | Cross-domain reasoning, cached in DB |
| Frontend hosting | Vercel | Zero config, auto-deploys, global CDN |
| Backend hosting | Render.com | Free HTTPS, Docker support, auto-deploys |
| CI/CD | GitHub Actions | Auto deploy on push to main |
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
│       │   └── activity_log.py
│       ├── schemas/
│       │   ├── user.py             # UserCreate, UserResponse, UserUpdate
│       │   ├── assignment.py
│       │   ├── job.py
│       │   ├── workout.py
│       │   ├── expense.py          # + location in response
│       │   ├── routine.py
│       │   └── activity_log.py
│       ├── routers/
│       │   ├── auth.py             # register, login, logout, me, patch me
│       │   ├── assignments.py      # CASE sort: pending → overdue → done
│       │   ├── jobs.py             # Kanban pipeline
│       │   ├── workouts.py
│       │   ├── expenses.py         # Returns {expenses, monthly_budget}
│       │   ├── routines.py         # CRUD + nested items
│       │   ├── dashboard.py
│       │   ├── ai.py               # JSON-structured briefing
│       │   └── activity.py         # GET /activity
│       └── services/
│           ├── auth.py
│           ├── context_builder.py  # AI signal aggregation
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
            └── api.ts              # Axios client
```

---

## Architecture

```
Browser (Vercel frontend)
      ↓ /api/* (Vercel rewrites proxy)
Render.com (FastAPI + Docker)
      ↓ SQLAlchemy ORM
Render PostgreSQL (9 tables)

FastAPI → Anthropic Claude (cached in ai_insights table)
GitHub  → GitHub Actions → Render deploy + Vercel deploy
```

**Why Vercel rewrites?**
The frontend (`lifeos-lac.vercel.app`) and backend (`lifeos-zggd.onrender.com`) are on different domains. Cross-domain cookies require `SameSite=none` but browsers still restrict them in some cases. Vercel rewrites proxy all `/api/*` requests through Vercel itself, making the browser think everything is on the same domain — no cross-domain cookie issues.

---

## Database Schema

9 tables. All tables have `created_at` and `updated_at` timestamps. All tables except `users` have a `user_id` foreign key. All primary keys are UUIDs.

```
users              — id, email, hashed_password, name, monthly_budget, weekly_capacity_hours
assignments        — id, user_id, title, course, due_date, estimated_hours, status, deleted_at
job_applications   — id, user_id, company, role, applied_date, status, followup_date, notes
workouts           — id, user_id, routine_id (nullable FK), type, duration_mins, notes, logged_at
routines           — id, user_id, name
routine_items      — id, routine_id (FK cascade), exercise_name, sets, reps, duration_mins, day_of_week
expenses           — id, user_id, amount, category, note, location, spent_at, group_override
ai_insights        — id, user_id, type, content, generated_at
activity_logs      — id, user_id, action, entity_type, entity_id, details, created_at
```

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Create account, sets JWT cookie |
| POST | `/auth/login` | Login, sets JWT cookie |
| POST | `/auth/logout` | Clears cookie |
| GET | `/auth/me` | Returns current user |
| PATCH | `/auth/me` | Update name, budget, capacity, password |

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
| POST | `/ai/briefing` | AI daily insight (JSON-structured: priorities + summary) |
| POST | `/ai/weekly` | Weekly digest |
| POST | `/ai/refresh` | Force regenerate |

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

## Architecture Decision Records

Key technical decisions documented with full context and tradeoffs:

- [ADR-001](docs/adr/ADR-001-fastapi.md) — FastAPI over Django / Express
- [ADR-002](docs/adr/ADR-002-multi-user-auth.md) — Multi-user auth from day 1
- [ADR-003](docs/adr/ADR-003-cache-ai-responses.md) — Cache AI responses in database
- [ADR-004](docs/adr/ADR-004-vercel-aws-eb.md) — Vercel + AWS Elastic Beanstalk (original)

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
