# LifeOS Backend

FastAPI REST API for LifeOS — a personal command center across academics, job hunting, fitness, and finance.

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Database | PostgreSQL 15 |
| ORM | SQLAlchemy + Alembic |
| Auth | JWT (python-jose) + bcrypt |
| Containerization | Docker + Docker Compose |

## Project Structure

```
backend/
├── app/
│   ├── main.py              # Entry point — registers all routers
│   ├── database.py          # SQLAlchemy engine + session + Base
│   ├── dependencies.py      # get_current_user — JWT auth guard
│   ├── models/
│   │   ├── base.py          # TimestampMixin (created_at, updated_at)
│   │   ├── user.py
│   │   ├── assignment.py
│   │   ├── job.py
│   │   ├── workout.py
│   │   ├── expense.py
│   │   └── ai_insight.py
│   ├── schemas/
│   │   ├── user.py
│   │   ├── assignment.py
│   │   ├── job.py
│   │   ├── workout.py
│   │   └── expense.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── assignments.py
│   │   ├── jobs.py
│   │   ├── workouts.py
│   │   ├── expenses.py
│   │   └── dashboard.py
│   └── services/
│       └── auth.py          # Password hashing, JWT creation/decode
├── alembic/                 # Migration history
├── alembic.ini
├── Dockerfile
└── requirements.txt
```

## Database Schema

Six tables, all with UUID primary keys and created_at / updated_at timestamps.

```
users            — id, email, hashed_password, name, monthly_budget, weekly_capacity_hours
assignments      — id, user_id, title, course, due_date, estimated_hours, status, deleted_at
job_applications — id, user_id, company, role, applied_date, status, followup_date, notes
workouts         — id, user_id, type, duration_mins, notes, logged_at
expenses         — id, user_id, amount, category, note, spent_at
ai_insights      — id, user_id, type, content, generated_at
```

## API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Create account, sets JWT cookie |
| POST | `/auth/login` | Login, sets JWT cookie |
| POST | `/auth/logout` | Clears JWT cookie |
| GET | `/auth/me` | Returns current user |

### Assignments
| Method | Endpoint | Description |
|---|---|---|
| POST | `/assignments` | Create assignment |
| GET | `/assignments` | List all, sorted by due date |
| PATCH | `/assignments/{id}` | Update fields |
| DELETE | `/assignments/{id}` | Soft delete |

### Jobs
| Method | Endpoint | Description |
|---|---|---|
| POST | `/jobs` | Create application, auto-sets followup +7 days |
| GET | `/jobs` | List all applications |
| PATCH | `/jobs/{id}` | Update status or notes |
| DELETE | `/jobs/{id}` | Hard delete |

### Workouts
| Method | Endpoint | Description |
|---|---|---|
| POST | `/workouts` | Log a workout |
| GET | `/workouts` | List all, newest first |
| DELETE | `/workouts/{id}` | Hard delete |

### Expenses
| Method | Endpoint | Description |
|---|---|---|
| POST | `/expenses` | Add an expense |
| GET | `/expenses` | List all, newest first |
| DELETE | `/expenses/{id}` | Hard delete |

### Dashboard
| Method | Endpoint | Description |
|---|---|---|
| GET | `/dashboard` | Aggregate summary across all 4 modules |

## Local Development

```bash
# From root lifeos/ folder — boots Postgres + API
docker compose up --build

# Swagger UI
http://localhost:8000/docs

# Run migrations
cd backend
alembic upgrade head
```

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Postgres connection string |
| `JWT_SECRET` | Secret key for signing JWT tokens |
