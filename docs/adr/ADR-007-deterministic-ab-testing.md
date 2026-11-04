# ADR-007: Deterministic A/B testing with exposure-based analysis

**Status:** Accepted  
**Date:** Sprint 2

## Context

LifeOS makes product decisions — how the briefing is presented, which
shortcuts exist, how much the AI says — that are easy to argue about and hard
to settle with intuition. We wanted a way to run a real experiment and read a
defensible result without adding a third-party feature-flag service.

The constraints were:

1. **Deterministic** — the same user must see the same variant across reloads,
   deploys, and devices. A random number stored in a cookie is not enough.
2. **Auditable** — every priority and every conversion should be explainable
   from rows in the database.
3. **Statistically honest** — the denominator must be users who actually saw
   the variant, and the numerator must be users who converted, not raw events.
4. **Dependency-free** — the app already runs on a free tier; a statistics
   service or experimentation SaaS is not in the budget.

## Decision

### Deterministic bucketing

```
bucket = SHA-256(f"{experiment_key}:{user_id}") % 10_000
variant = first variant whose cumulative normalized weight > bucket
```

SHA-256 is used instead of Python's built-in `hash()` because built-in hashing
is randomized per process — assignments would change on every deploy. Including
the experiment key in the hash gives each experiment an independent assignment:
a user can be in control for one test and treatment for another.

Weights are normalized rather than assumed to sum to 100, so a 33/33/34 split
works without special-casing. A zero-weight variant is never assigned.

### Three tables

| Table | Purpose | Key constraint |
|---|---|---|
| `experiments` | Configuration: key, variants, primary metric, status | unique `key` |
| `experiment_exposures` | First time a user saw a variant | unique `(experiment_id, user_id)` |
| `experiment_events` | Immutable conversion events | none — users can convert repeatedly |

The unique exposure constraint is the idempotency guarantee. Reloading the
dashboard, React re-rendering, or SWR revalidating cannot inflate the
denominator. If two concurrent first requests race, the loser catches
`IntegrityError`, rolls back, and reads the winner's row.

### Exposure on evaluation

`GET /experiments/{key}` both evaluates the user's variant and records their
first exposure. This is an intentional side effect. Exposure means "the user
was shown the experiment surface," and the evaluation call is the moment that
happens. A separate exposure request would let the client forget to send it and
silently shrink the denominator. The write is idempotent.

This is an **intent-to-treat** design: everyone who saw the surface counts,
including users who ignored the treatment. That is the conservative choice.

### Server-side variant resolution

The client sends an event name and metadata; it never sends its variant. The
server resolves the variant from the exposure table. A modified request cannot
claim to be in the other arm. If an event arrives before the assignment call
(a race), the server creates the exposure first so the event is still
attributable.

### Statistics

Results compare each treatment arm to the first configured variant (control)
with a two-sided two-proportion z-test:

- Pooled standard error for the test statistic, because the null hypothesis is
  that both arms share one true rate.
- Unpooled standard error for the 95% confidence interval, because we are
  estimating the size of the difference.
- Two-sided p-value computed as `erfc(|z| / sqrt(2))` — no scipy dependency.
- `lift` is relative to control; `absolute_lift` is the percentage-point
  difference.
- Results count **distinct converted users**, not events. Completing three
  assignments is still one converted user.
- Only events at or after the user's first exposure are counted.
- A sample-size flag warns when any arm has fewer than 30 exposures.

### First experiment: `briefing_quick_complete`

| | |
|---|---|
| Control | The normal briefing: priorities + summary |
| Treatment | The briefing plus one-click **Mark done** actions for the top scored assignments |
| Primary metric | `quick_action_completed` |
| Hypothesis | Removing navigation friction between "what to do" and "do it" increases completed assignments |

Quick actions are derived from the same deterministic assignment scores as the
briefing priorities. The experiment tests the shortcut, not a second
recommendation system.

## Consequences

- ✅ Assignments are stable, reproducible, and independent per experiment.
- ✅ Exposure counts are idempotent; conversion counts are unique users.
- ✅ Every result is traceable to exposure and event rows.
- ✅ The framework has no external dependency and no per-user cost.
- ✅ The treatment is a real product change, not a cosmetic button color.
- ❌ The demo has one user, so results are necessarily preliminary until more
  users enroll. The response says so instead of pretending otherwise.
- ❌ No sequential testing or early-stopping correction. Peeking at a running
  experiment inflates false positives; the sample-size warning is a guardrail,
  not a solution.
- ❌ No multiple-comparison correction across arms. The current experiment has
  one treatment arm; adding more would need a correction.
- ❌ No sample-ratio-mismatch check. A production system should compare the
  observed split to the configured weights and alert on drift.
- ❌ A production system would likely use an experimentation platform for
  targeting, audit logs, and sequential analysis. Building this one was the
  point: the mechanics are now visible and debuggable.
