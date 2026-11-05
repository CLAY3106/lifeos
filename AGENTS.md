# LifeOS: rules for every agent

LifeOS is Son Le's full-stack personal productivity app. Son is the Product Manager and the only human reviewer. Agents propose, Son decides.

## Stack
- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS v4, SWR + Axios, Chart.js, React Hook Form + Zod v4. Deployed on Vercel (reverse-proxy rewrites handle cross-origin cookies).
- Backend: FastAPI (Python 3.11), SQLAlchemy + Alembic, JWT in httpOnly cookies, slowapi rate limiting, structlog. Deployed on Render.
- Database: PostgreSQL 15 on Render. All primary keys are UUIDs. Soft delete on assignments. Tests may use SQLite, so code must stay portable.
- AI: Claude Haiku for briefings, OpenAI text-embedding-3-small for RAG. Hybrid search fuses vector similarity and keyword rank with Reciprocal Rank Fusion (k=60). A deterministic scoring service powers priorities when Claude is unavailable.
- Infra: Docker + Docker Compose, GitHub Actions CI/CD.

## Modules
Academic planner, job hunt tracker (with event-sourced audit trail), workout log, finance tracker (50/30/20 envelope budgeting), AI daily briefing, activity log. Each module is grounded in a behavioral psychology principle (Zeigarnik Effect, Endowed Progress, Mental Accounting, Paradox of Choice). Do not remove those behaviors without a ticket that says so.

## How work flows
1. Work comes only from GitHub Issues labeled `sprint`. No issue, no work. Never invent features.
2. One issue, one branch: `agent/<issue-number>-<short-slug>`. Branch from an up-to-date `main`.
3. Small commits with clear messages: `feat:`, `fix:`, `test:`, `docs:`, `ci:`, `chore:`. Reference the issue number.
4. Open a pull request with `gh pr create`. The PR body says: what changed, why, how it was tested, risks, and the issue it closes.
5. Son reviews and merges. Agents never merge, never push to `main`, never force-push, never delete branches they did not create.

## Ownership (one owner per area)
- database: SQLAlchemy models and all Alembic migrations. Nobody else writes migrations.
- backend: FastAPI routers, services, schemas, backend business logic.
- frontend: Next.js pages, components, hooks, API client code.
- uiux: design specs in `docs/design/`, styling and accessibility fixes in frontend components.
- qa: tests in `backend/tests/` and frontend test files. QA may read everything.
- security: read-only reviewer. Writes findings, never edits code.
- devops: `.github/workflows/`, Dockerfiles, Compose files, deploy config.
If a task needs a change in someone else's area, hand it to that agent or note it in the PR. Do not reach across.

## API contract
Backend and frontend agree on the contract before coding. The FastAPI OpenAPI schema is the contract. Any change to request or response shapes must be called out in the PR under "Contract change".

## Definition of done
- Tests added or updated for the change, and the full suite passes locally.
- Lint and type checks pass.
- Security reviewer ran on the diff with no unresolved High findings.
- No secrets, keys, tokens, or personal data in code, logs, fixtures, or commits.
- PR opened with the template above.

## Hard limits
- Never commit `.env` files or credentials. Use environment variables and `.env.example`.
- Never run destructive database commands against anything but a local or test database.
- Never call paid APIs (Anthropic, OpenAI) in tests. Mock them.
- Never deploy. Deploys happen from `main` through CI after Son merges.
- Stop and write a note instead of guessing when an issue is ambiguous.
- No em dashes in docs, comments, commit messages, or PR text.

## Daily report
The scrum-lead writes `docs/reports/YYYY-MM-DD.md` after each run: issues worked, PRs opened, test results, security findings, blockers, and questions for Son.
