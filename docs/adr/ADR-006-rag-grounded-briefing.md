# ADR-006: Ground the AI briefing in retrieved records (RAG)

**Status:** Accepted  
**Date:** Sprint 1

## Context

The daily briefing originally sent Claude only *aggregates*: counts of upcoming
assignments, days since a workout, budget percentage. That is enough to say
"you have a busy week", but not enough to say *which* assignment is at risk or
*which* company needs a follow-up. Asked for specifics, the model could only
guess — and a plausible-sounding invention is worse than no briefing at all.

Sending the model every row is not the answer either:

1. **Token cost and latency** grow with the user's history, most of which is
   irrelevant to today.
2. **Lost-in-the-middle** — models attend less reliably to long contexts; the
   relevant row gets buried among old expenses.
3. **No traceability** — there is no way to explain why a priority appeared.

The system already had two ingredients: a deterministic scorer that decides
what matters today, and a `document_chunks` index with hybrid search.

## Decision

Build the briefing context in **two layers**:

1. **Aggregates** — the existing counts, totals, and percentages. Always
   available, cheap, and deterministic.
2. **Retrieved records** — the chunks most relevant to today's top scored
   signals, included verbatim with their entity type.

### The scorer writes the query

A daily briefing has no user query. Rather than invent one, the top three
`ScoredSignal` titles become the retrieval query:

```
"Due soon: DSA Assignment (assignment) Follow up: SWE Intern at Google (job)"
```

This creates a clean division of responsibility:

| Layer | Decides |
|---|---|
| `scoring.py` | *what* matters (urgency, weights, cross-domain tensions) |
| `rag.py` | *which evidence* supports it (vector + BM25, fused with RRF) |
| Claude | *how* to phrase it (tone, ordering, summary) |

Every priority is therefore traceable: score → query → chunk → sentence.

### Grounding contract

The prompt includes explicit rules: use `retrieved_records` for specifics,
never invent records or numbers, and stay general when retrieval is empty.
The context is serialized as JSON (not a Python dict repr) so the model sees a
stable structure.

### Fail-open by design

Retrieval is an enhancement, not a dependency:

- OpenAI unavailable → `hybrid_search` degrades to keyword-only.
- Retrieval raises → `build_context` logs and returns `[]`.
- Anthropic unavailable → the route falls back to deterministic scoring.
- Repeated embedding failures → a circuit breaker skips calls for a cooldown
  (15 minutes for billing/auth failures, 60 seconds for transient errors).

The briefing never 500s because an AI provider is down.

### Observable output

The API response includes retrieval metadata:

```json
"retrieval": {
  "chunks": 8,
  "query": "Due soon: DSA Assignment (assignment) ...",
  "sources": ["assignment", "job"]
}
```

This makes grounding visible in the product and debuggable in production
without exposing the raw prompt.

## Consequences

- ✅ Priorities cite real titles, companies, amounts, and dates.
- ✅ Every priority can be traced back to a score and a source chunk.
- ✅ Provider outages degrade quality, not availability.
- ✅ Retrieval quality can be measured (`chunks`, `sources`, keyword vs hybrid).
- ❌ The briefing is only as good as the index. Chunks must be refreshed when
  entities change; a stale index yields stale evidence.
- ❌ Retrieval currently runs keyword-only until OpenAI embeddings are
  backfilled. The code path is identical; only the semantic half is missing.
- ❌ The 6-hour insight cache means retrieval metadata describes the moment of
  generation, not the moment of viewing.
