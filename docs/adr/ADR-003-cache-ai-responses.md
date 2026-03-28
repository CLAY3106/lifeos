# ADR-003: Cache AI responses in database

**Status:** Accepted  
**Date:** Day 1

## Context

The dashboard loads an AI-generated daily briefing that reasons across all four data modules. Calling the LLM on every page load has two problems:

1. **Latency** — LLM calls take 1–3 seconds, making the dashboard feel slow
2. **Cost** — at scale, generating a new response on every load would be expensive. Even during development, unnecessary calls add up quickly

The briefing is a *daily* summary — its content does not meaningfully change minute-to-minute. There is no user value in regenerating it on every visit.

## Decision

Generate the daily briefing **once per day**, store the result in the `ai_insights` table, and serve the cached version on all subsequent loads.

Cache logic:
- On `/ai/briefing` request, check `ai_insights` for a record generated today
- If found and age < 6 hours: return cached response immediately (no LLM call)
- If stale or missing: call the LLM, store the result, return it
- Expose a `POST /ai/refresh` endpoint so the user can force-regenerate manually
- Rate limit: 10 AI calls per user per day (via `slowapi`)

## Consequences

- ✅ Dashboard loads instantly after the first daily briefing is generated
- ✅ LLM costs are bounded — at most one call per user per day under normal usage
- ✅ Rate limiting prevents runaway API spend
- ❌ Cached response may be up to 6 hours stale — acceptable for a daily briefing. The insight is valid for the whole day.
- ❌ User must manually refresh to get an updated briefing after adding significant new data
