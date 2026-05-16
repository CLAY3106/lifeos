# LifeOS Changelog

A running log of engineering decisions, problems encountered, and how they were resolved. Useful for interviews — every entry is a talking point.

---

## Week 1 — Initial Build (March 27-29, 2026)

### Day 1 — Design & Planning
- Designed 6-table database schema (users, assignments, job_applications, workouts, expenses, ai_insights)
- Wrote 9 user stories with acceptance criteria, filed as GitHub Issues
- Wrote ADR-001 through ADR-004 documenting key architecture decisions
- Scaffolded monorepo — `frontend/` (Next.js), `backend/` (FastAPI), `docker-compose.yml`
- Docker Compose boots Postgres + API locally with health checks

### Day 2 — Backend Core
- Built FastAPI with SQLAlchemy models, Alembic migrations, JWT auth, bcrypt password hashing
- All CRUD endpoints for 4 modules + `/dashboard` aggregate endpoint
- JWT stored in `httpOnly` cookie — prevents JavaScript access
- Soft deletes on assignments (`deleted_at`) — never hard delete deadlines
- 15+ pytest tests

**Problem:** Wrong virtual environment (`comp-vision-football`) kept activating instead of the project venv.
**Fix:** Always `cd backend && .\.venv\Scripts\Activate.ps1` before running Python commands.

**Problem:** `bcrypt` version incompatibility with `passlib` — `ValueError: password cannot be longer than 72 bytes`.
**Fix:** Pinned `bcrypt==4.0.1` in `requirements.txt`.

**Problem:** Job schema `created_at` typed as `date` instead of `datetime` — Pydantic validation error.
**Fix:** Changed to `datetime` in `schemas/job.py`.

### Day 3 — Frontend
- Next.js 14 with App Router, TypeScript, TailwindCSS, SWR, Axios
- All 5 pages: Dashboard, Assignments, Jobs, Fitness, Finance
- Sidebar navigation with `(app)` route group for shared layout
- Auth middleware redirects unauthenticated users to `/auth/login`
- SWR auto-refreshes dashboard every 30 seconds

**Problem:** Two sidebars rendering — old `layout.tsx` left in `dashboard/` folder after moving to `(app)/`.
**Fix:** Deleted the duplicate layout file.

**Problem:** CORS blocking frontend from calling backend — different ports (`localhost:3000` vs `localhost:8000`).
**Fix:** Added `CORSMiddleware` to FastAPI with `allow_origins=["http://localhost:3000"]` and `allow_credentials=True`.

**Problem:** Auth middleware not working — Turbopack incompatibility.
**Fix:** Removed `--turbopack` flag from `next dev` command.

**Problem:** Middleware causing redirect loops — `startsWith("/auth")` too broad.
**Fix:** Switched to explicit `PUBLIC_PATHS` array with `Array.some()` check.

### Day 4 — AI Layer
- Built `context_builder.py` — queries all 5 tables, computes ~600 tokens of structured signals
- Signals: `weekly_load_hours`, `load_percent`, `overdue_count`, `overdue_followups`, `days_since_workout`, `budget_percent`
- Claude Haiku generates 2-3 sentence cross-domain morning briefing
- Response cached in `ai_insights` table for 6 hours — no duplicate LLM calls
- Rate limiting: 10 AI calls/user/day via `slowapi`
- AI briefing card wired to dashboard with Refresh button

**Problem:** Anthropic API key accidentally committed to `docker-compose.yml`.
**Fix:** GitHub push protection caught it. Removed via `git commit --amend --force-push`. Moved to `.env` file (added to `.gitignore`).

### Day 5 — AWS Deployment + CI/CD
- Created IAM user with least-privilege permissions
- Deployed PostgreSQL to AWS RDS (`db.t4g.micro`, free tier, `us-east-1`)
- Deployed FastAPI to AWS Elastic Beanstalk (Docker, `t3.micro`, `us-east-1`)
- Frontend deployed to Vercel (auto-deploys on push to main)
- GitHub Actions CI/CD: `pytest` → `eb deploy` → `vercel --prod` on push to main

**Problem:** EB deployment failed — `EXPOSE` directive missing from Dockerfile.
**Fix:** Added `EXPOSE 8000` to Dockerfile.

**Problem:** `.elasticbeanstalk/config.yml` not committed — CI/CD couldn't find EB config.
**Fix:** Force-added with `git add -f backend/.elasticbeanstalk/config.yml`.

**Problem:** `alembic.ini` uses `db` hostname (Docker internal) but local runs need `localhost`.
**Fix:** `alembic.ini` uses `localhost`. Docker Compose sets `DATABASE_URL` with `db` hostname via environment variable.

---

## Post-Launch Fixes (May 2026)

### Infrastructure Migration — AWS EB → Render.com

**Root problem:** AWS Elastic Beanstalk free tier does not support HTTPS. Adding HTTPS requires an Application Load Balancer (~$18/month).

**Why this matters:** Vercel serves the frontend over HTTPS. Browsers enforce Mixed Content policy — HTTPS pages cannot make requests to HTTP endpoints. This blocked all API calls from the live frontend.

**Decision:** Migrate backend to Render.com which provides free HTTPS with Docker support.

**Consequence:** Lost the AWS EB story for the live demo. Preserved all AWS knowledge (IAM, RDS, security groups, VPCs, CloudWatch) as interview talking points. In production with a budget, the correct AWS setup is EB + ALB + ACM certificate.

---

### Database Migration — AWS RDS → Render PostgreSQL

**Problem:** After migrating API to Render (Oregon, US West), RDS was in `us-east-2` (Ohio). Cross-region database connections timed out despite correct security group rules and public accessibility.

**Root cause:** Likely VPC Network ACL restrictions on outbound traffic from unknown sources, combined with cross-region latency causing connection timeouts before the pool timeout kicked in.

**Attempted fixes:**
- Added EB security group to RDS inbound rules
- Added `0.0.0.0/0` to RDS inbound rules
- Set RDS to publicly accessible
- Added connection pooling (`pool_pre_ping`, `pool_recycle`, `pool_timeout`)
- Added `connect_timeout=10` to SQLAlchemy engine

**Decision:** Migrate to Render PostgreSQL. Both API and database on Render's internal network — zero networking configuration needed.

---

### Alembic Migration Fix

**Problem:** `entrypoint.sh` runs `alembic upgrade head` on startup, but Alembic's `configparser` treats `%` as a special interpolation character. URL-encoded password characters like `%21` (for `!`) caused `ValueError: invalid interpolation syntax`.

**Fix 1 (wrong):** URL-encoded the `%` as `%%` in `env.py`.
**Fix 2 (correct):** Changed RDS password to one without special characters.

**Additional fix:** Updated `alembic/env.py` to read `DATABASE_URL` from environment variable instead of `alembic.ini` — allows the same codebase to work locally (reads from `alembic.ini`) and in production (reads from environment).

---

### Cross-Domain Cookie Fix

**Problem:** Frontend on `lifeos-lac.vercel.app` and backend on `lifeos-zggd.onrender.com` are different domains. Cookies set by the backend weren't being sent by the browser on subsequent requests — `SameSite=lax` blocks cross-site cookies.

**Fix 1 (partial):** Changed cookie to `SameSite=none; Secure=True`. Cookie was set but still not sent on API requests because the browser scoped it to the Render domain, not Vercel.

**Fix 2 (complete):** Added Vercel rewrites in `next.config.ts` to proxy all `/api/*` requests through Vercel to Render. Now the browser thinks it's talking to `lifeos-lac.vercel.app` for all requests — same domain, no cross-domain cookie restrictions.

```typescript
async rewrites() {
  return [{
    source: '/api/:path*',
    destination: 'https://lifeos-zggd.onrender.com/:path*',
  }]
}
```

Updated `api.ts` to use `/api` as the base URL in production and `http://localhost:8000` in development.

**Additional fix:** Auth middleware was intercepting `/api/*` requests and redirecting them to `/auth/login`. Added `/api` to `PUBLIC_PATHS` in `middleware.ts`.

---

### CI/CD Fix

**Problem:** `amondnet/vercel-action@v25` outdated — Vercel CLI required v47.2.2 or later.

**Fix:** Replaced the Vercel GitHub Action with direct CLI installation:
```yaml
- name: Install Vercel CLI
  run: npm install -g vercel@latest
- name: Deploy to Vercel
  run: vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
```

---

## Current Architecture (May 2026)

```
Frontend:  Vercel (https://lifeos-lac.vercel.app)
Backend:   Render.com (https://lifeos-zggd.onrender.com)
Database:  Render PostgreSQL
CI/CD:     GitHub Actions → Render + Vercel
```

## AWS Resources (Cleaned Up)

- ✅ Elastic Beanstalk environment terminated
- ✅ RDS instance deleted
- ✅ IAM user retained (useful for future projects)
- ✅ CloudWatch log groups retained

---

## Lessons Learned

1. **HTTPS is non-negotiable for live demos.** Plan for it from day one. Free tier hosting that includes HTTPS (Render, Railway, Fly.io) saves significant debugging time.

2. **Cross-domain cookies are hard.** Same-site restrictions, Secure requirements, and domain scoping make cross-origin auth complicated. A reverse proxy (Vercel rewrites) is the cleanest solution.

3. **Special characters in passwords break things.** URL encoding, `configparser` interpolation, and shell escaping all treat `!`, `%`, `@` differently. Use alphanumeric-only passwords for infrastructure credentials.

4. **Virtual environment discipline matters.** Using the wrong venv caused multiple confusing errors. Always verify the active venv before running Python commands.

5. **Commit secrets are permanent.** GitHub push protection caught an API key in `docker-compose.yml`. Even after removing it via `--amend`, the key should be rotated. Never commit secrets.

6. **Pre-aggregate before sending to LLM.** Sending raw database rows to Claude is expensive and noisy. Computing structured signals in Python first (`context_builder.py`) made the prompt deterministic, fast, and cheap to test.
