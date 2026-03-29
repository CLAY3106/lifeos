# LifeOS Frontend

Next.js 14 frontend for LifeOS — a personal command center across academics, job hunting, fitness, and finance.

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript |
| Styling | TailwindCSS |
| Data Fetching | SWR |
| HTTP Client | Axios |
| Forms | React Hook Form |

## Project Structure

```
frontend/
└── src/
    ├── app/
    │   ├── (app)/                  # Protected pages with sidebar layout
    │   │   ├── layout.tsx          # Shared layout — sidebar + main content
    │   │   ├── dashboard/
    │   │   │   └── page.tsx        # 4 summary cards, upcoming assignments
    │   │   ├── assignments/
    │   │   │   └── page.tsx        # Add, list, update status, soft delete
    │   │   ├── jobs/
    │   │   │   └── page.tsx        # Kanban board — Applied, Interview, Offer, Rejected
    │   │   ├── fitness/
    │   │   │   └── page.tsx        # Log workouts, list by date
    │   │   └── finance/
    │   │       └── page.tsx        # Add expenses, monthly total
    │   ├── auth/
    │   │   ├── login/
    │   │   │   └── page.tsx        # Login form
    │   │   └── register/
    │   │       └── page.tsx        # Register form
    │   ├── layout.tsx              # Root layout — fonts, globals
    │   ├── page.tsx                # Redirects to /dashboard
    │   └── globals.css
    ├── components/
    │   └── Sidebar.tsx             # Navigation sidebar with logout
    └── lib/
        └── api.ts                  # Axios client with credentials + base URL
```

## Pages

### Dashboard `/dashboard`
- 4 summary cards — Assignments, Jobs, Fitness, Finance
- Weekly load progress bar (turns red at 80% capacity)
- Budget progress bar (amber at 80%, red at 100%)
- Upcoming assignments list
- Auto-refreshes every 30 seconds via SWR

### Assignments `/assignments`
- Add form — title, course, due date, estimated hours
- List sorted by due date
- Status dropdown — Pending, Done, Overdue
- Soft delete (data preserved in database)

### Jobs `/jobs`
- Add form — company, role, applied date
- Kanban board with 4 columns — Applied, Interview, Offer, Rejected
- Drag status via dropdown
- Follow-up date auto-set to applied date + 7 days

### Fitness `/fitness`
- Quick-add form — type + duration (2 fields only)
- List sorted newest first
- Press Enter to submit

### Finance `/finance`
- Quick-add form — amount, category dropdown, optional note
- Monthly total display
- List sorted newest first
- Categories: Food, Transport, Study, Fitness, Other

## Local Development

```bash
# Install dependencies
npm install

# Run dev server
npm run dev
```

App available at `http://localhost:3000`

Make sure the backend is running first:
```bash
# From root lifeos/ folder
docker compose up -d
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000` |

Create a `.env.local` file in the `frontend/` folder:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

On Vercel this is set to the AWS Elastic Beanstalk URL.

## Key Design Decisions

**SWR for data fetching** — all pages use SWR with `mutate()` for instant UI updates after add/delete. Dashboard uses `refreshInterval: 30000` for passive background refresh.

**`withCredentials: true` on Axios** — required for the JWT cookie to be sent cross-origin between `localhost:3000` and `localhost:8000`.

**Route groups `(app)`** — groups all protected pages under one shared layout with the sidebar, without affecting the URL structure.

**Redirect on home** — `app/page.tsx` redirects to `/dashboard` so the app always opens on the main screen.
