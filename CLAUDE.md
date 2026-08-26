# LifeOS

Personal command center across academics, job hunting, fitness, and finance.

## Stack

- **Frontend**: Next.js 16 (App Router) + React 19, in `frontend/`. Tailwind v4 (CSS-var-driven theme, see below). Data fetching via SWR + axios (`frontend/src/lib/api.ts`).
- **Backend**: FastAPI in `backend/app/`, SQLAlchemy + Alembic, JWT auth via cookies, rate limiting via slowapi, structured logging via structlog.
- **DB**: Postgres 15. `docker-compose.yml` runs a local `db` + `api` container. Root `.env` also has a Neon cloud `DATABASE_URL` — that's unused by the docker `api` service (which hardcodes its own local `DATABASE_URL`), but is there for running the backend outside Docker if needed.

## Running locally

See `.claude/skills/run/SKILL.md` for the full recipe. Short version:

```bash
docker compose up -d db api        # postgres + FastAPI on :8000, auto-migrates + seeds demo user
cd frontend && npm run dev         # Next dev server on :3000
```

Log in with the **"Try as guest"** button on `/auth/login` (seeds `demo@lifeos.app` / `demo1234` with sample assignments, jobs, workouts, expenses).

Swagger docs: http://localhost:8000/docs

## Design system (frontend)

`frontend/src/app/globals.css` defines a Notion-style token set (light + dark, following `prefers-color-scheme`):
`--background`, `--surface`, `--surface-hover`, `--foreground`, `--muted`, `--muted-2`, `--rule`, `--accent`, `--danger`, and six `--callout-*` tones (gray/red/yellow/green/blue/purple) used for banner/callout backgrounds.

Page content wrappers follow a `max-w-{3xl|5xl} mx-auto px-16 py-16` pattern (the shared `<main>` in `(app)/layout.tsx` intentionally carries **no** padding — each page owns its own, so a new page must add `px-16 py-16` itself or it'll render flush against the viewport edge).

## Backend structure

- `app/routers/` — one router per resource: `auth`, `assignments`, `jobs`, `workouts`, `expenses`, `dashboard`, `ai`.
- `app/models/` — SQLAlchemy models, one per table (`user`, `assignment`, `job`, `workout`, `expense`, `ai_insight`).
- `app/seed.py` — idempotent demo-account seeder, run on every container start via `entrypoint.sh`.
- Migrations: `cd backend && alembic upgrade head` (auto-run by `entrypoint.sh` in Docker too).

## Gotchas

- Next.js dev-mode indicator is pinned to `bottom-right` in `next.config.ts` — it used to collide visually with the sidebar's "Sign out" button in the default bottom-left position.
- `frontend/next.config.ts` rewrites `/api/:path*` to a deployed Render backend — irrelevant for local dev (axios talks directly to `localhost:8000` when `NODE_ENV !== "production"`).
