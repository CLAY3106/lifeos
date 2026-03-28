# ADR-001: FastAPI over Django / Express

**Status:** Accepted  
**Date:** Day 1

## Context

The backend needs to serve a REST API across four data modules (academics, jobs, fitness, finance) plus an AI layer. Python is the preferred language due to prior experience in data engineering. The project must be fully buildable by one developer in approximately two days, so developer speed and minimal boilerplate are critical constraints.

## Decision

Use **FastAPI**.

- Async by default — aligns with the AI layer which involves slow external LLM calls
- Auto-generates Swagger UI at `/docs` — useful for demos and manual testing during development
- Pydantic validation is built-in — request/response schemas come for free
- Significantly lighter than Django — no ORM, admin, or auth opinions baked in

Alternatives considered:
- **Django REST Framework** — rejected due to heavier boilerplate and slower setup for a personal-scale app
- **Express (Node.js)** — rejected to keep the stack in Python, consistent with the AI/data engineering background

## Consequences

- ✅ Fast to scaffold — no generated boilerplate to fight
- ✅ Swagger UI ships automatically — useful for the demo and for sharing the API with interviewers
- ✅ Pydantic schemas double as input validation and API documentation
- ❌ No built-in admin panel — acceptable since this is a personal app, not a CMS
- ❌ Smaller ecosystem than Django — no concern at this scale
