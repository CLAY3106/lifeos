#!/usr/bin/env bash
# Creates the labels and Sprint 1 issues on GitHub. Run once from the repo root.
# Requires: gh CLI, logged in (gh auth login).
set -euo pipefail

gh label create sprint     --color 1D76DB --description "Ready for the agent team" 2>/dev/null || true
gh label create p0         --color B60205 --description "Do first"                  2>/dev/null || true
gh label create p1         --color FBCA04 --description "Do next"                   2>/dev/null || true
gh label create blocked    --color 000000 --description "Agents skip this"          2>/dev/null || true
gh label create needs-son  --color 5319E7 --description "Waiting on Son"            2>/dev/null || true

gh issue create --label sprint --label p0 --title "CI: run backend and frontend tests on every push and PR" --body "Owner: devops.
Make GitHub Actions run backend lint, type check, and pytest, plus frontend type check, lint, tests, and build, on every push and pull request. Failing checks must block merge. Cache dependencies.
Done when: a PR shows all checks, and a deliberately failing test turns the check red."

gh issue create --label sprint --label p0 --title "Tests: Reciprocal Rank Fusion and hybrid search ranking" --body "Owner: qa (backend if code must change to be testable).
Unit tests for RRF with k=60: ordering when lists agree, disagree, and overlap partly; ties; empty lists; one empty list. Keyword fallback path on SQLite. Mock embeddings, no OpenAI calls.
Done when: tests pass offline and cover every branch of the fusion function."

gh issue create --label sprint --label p0 --title "Tests: deterministic scoring service" --body "Owner: qa.
Cover the rubric: overdue 50 + 5/day capped at 100, due in 24h = 90, 3d = 70, 7d = 40, job follow-up = 60, no workout 5d = 50, 3d = 30, budget over 95% = 85, over 80% = 55. Cross-domain tension detection (deadline collisions, weekly overload over 80%). Fallback mode when Claude is unavailable returns exactly 3 priorities.
Done when: every rubric rule has at least one test, including boundaries."

gh issue create --label sprint --label p1 --title "Tests: auth and ownership checks" --body "Owner: qa, reviewed by security.
JWT in httpOnly cookies: login, logout, expired token, missing token. For each module, a user cannot read or modify another user's records (expect 403 or 404).
Done when: every data endpoint has an ownership test."

gh issue create --label sprint --label p1 --title "Tests: budget period aggregates and event-sourced job history" --body "Owner: qa.
Budget: 50/30/20 group mapping, group_override, month boundaries via the period bounds helper, empty months. Jobs: every status change appends an event, history is immutable, current status equals the latest event.
Done when: both areas are covered including month-boundary edge cases."

echo "Sprint 1 created. Review the issues on GitHub and adjust before the first agent run."
