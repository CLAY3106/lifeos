# ADR-002: Multi-user auth from day 1

**Status:** Accepted  
**Date:** Day 1

## Context

The app could be built as a single-user tool first to ship faster — no auth, no `user_id` on tables, just one hardcoded user. However, demo viewers and interviewers may want to create their own accounts and see the app with their own data, not a shared seed account.

The question is: add auth now or bolt it on later?

## Decision

Add **JWT authentication and `user_id` foreign keys on every table from day 1**.

Implementation:
- `python-jose` for JWT token generation and validation
- `passlib[bcrypt]` for password hashing
- `get_current_user` FastAPI dependency injected into every protected route
- `httpOnly` cookie for storing the token on the client
- Access token only, 7-day expiry (no refresh token rotation — see Consequences)

This adds approximately 30 minutes of setup on Day 2 but eliminates a painful schema migration later.

Alternatives considered:
- **Single-user, no auth** — rejected because interviewers demoing the app would share one account, polluting each other's data and making the demo awkward

## Consequences

- ✅ Interviewers and demo viewers can each create their own account
- ✅ All data is user-scoped from the start — no retrofit needed
- ✅ JWT + bcrypt is industry-standard — good talking point in interviews
- ❌ Slightly more setup on Day 2
- ❌ No refresh token rotation — conscious tradeoff for simplicity on a personal app. Post-MVP: add refresh token rotation.
