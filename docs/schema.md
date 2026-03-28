# Database Schema

## Overview
7 tables. All tables have `created_at` and `updated_at` timestamps.
All tables except `users` have a `user_id` foreign key.
All primary keys are UUIDs.

---

## Tables

### users
| Column | Type | Notes |
|--------|------|-------|
| id     | UUID | PK    |
| email  | VARCHAR | unique, not null |
| hashed_password | VARCHAR | not null |
| name | VARCHAR | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### user_settings
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| weekly_capacity_hours | FLOAT | default 40 |
| monthly_budget | DECIMAL | default 200 |
| created_at | TIMESTAMP | |

### assignments
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| title | VARCHAR | not null |
| course | VARCHAR | |
| due_date | TIMESTAMP | not null |
| estimated_hours | FLOAT | default 1.0 — used for weekly load calculation |
| status | ENUM | pending, done, overdue |
| deleted_at | TIMESTAMP | soft delete — filter WHERE deleted_at IS NULL |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### job_applications
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| company | VARCHAR | not null |
| role | VARCHAR | not null |
| applied_date | DATE | not null |
| status | ENUM | applied, interview, offer, rejected |
| followup_date | DATE | auto-set to applied_date + 7 days |
| notes | TEXT | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### workouts
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| type | VARCHAR | e.g. gym, run, yoga |
| duration_mins | INT | not null |
| notes | TEXT | |
| logged_at | TIMESTAMP | default now() |
| created_at | TIMESTAMP | |

### expenses
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| amount | DECIMAL | not null |
| category | ENUM | food, transport, study, fitness, other |
| note | TEXT | |
| spent_at | TIMESTAMP | default now() |
| created_at | TIMESTAMP | |

### ai_insights
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| type | ENUM | daily, weekly |
| content | TEXT | the generated briefing text |
| generated_at | TIMESTAMP | used to check if cache is stale |

---

## Design decisions

- **UUIDs as PKs** — safe to expose in URLs, don't leak row counts
- **Soft deletes on assignments** — deleted_at instead of hard delete, user data is never permanently lost
- **estimated_hours on assignments** — enables weekly load calculation for the AI context builder
- **ai_insights cached** — generated once per day, served from DB on subsequent loads
- **followup_date auto-set** — applied_date + 7 days, reduces friction when logging a job application
- **user_settings separate table** — settings queried frequently by AI context builder, cleaner than extra columns on users