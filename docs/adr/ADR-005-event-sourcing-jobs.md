# ADR-005: Event sourcing for job application status changes

**Status:** Accepted  
**Date:** Week 1

## Context

Job applications go through a multi-stage pipeline: Applied → OA → Interview → Offer (or Rejected/Dropped). Users need to see the *history* of how an application progressed — when they applied, when they heard back, when the interview was scheduled.

A simple `status` column on the `job_applications` table only stores the *current* state. When the status changes, the previous value is overwritten and lost. This makes it impossible to:

1. Show a timeline of status changes on the application detail page
2. Calculate metrics like "average time from applied to interview"
3. Debug issues ("when did this status change? did I miss a follow-up?")
4. Support the A/B testing framework (measure time-to-first-action)

## Decision

Add a `job_status_history` table that records every status change as an immutable event. Each row captures:

- `job_id` — which application
- `from_status` — previous status (nullable for initial creation)
- `to_status` — new status
- `changed_at` — timestamp of the change
- `notes` — optional context (e.g., "HR called to schedule")

The `status` column on `job_applications` still exists as a *materialized view* of the latest state — it's updated on every status change for fast reads, but the source of truth is the history table.

### Soft validation

Invalid transitions (e.g., Applied → Offer, skipping intermediate stages) are **logged as warnings** but **not blocked**. Rationale:

- Users may legitimately skip stages (e.g., a company goes straight from applied to offer)
- Blocking transitions creates friction in a personal tool
- The warning in logs provides observability without enforcing strict rules

## Consequences

- ✅ Full audit trail of every status change — visible on the application detail page
- ✅ Enables time-based metrics (time in each stage, time to first response)
- ✅ Supports A/B testing: measure how long it takes users to take first action
- ✅ Event sourcing pattern is a common interview talking point — demonstrates understanding of immutable data models
- ❌ Adds one extra table and a slightly more complex update flow (two writes instead of one)
- ❌ History rows are append-only — if a status is corrected, both the old and new events remain (this is intentional for audit purposes)
