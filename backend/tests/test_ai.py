"""
AI Briefing Tests — RAG Grounding and Graceful Degradation

These tests cover the contract that makes the briefing trustworthy:

1. Retrieved records are actually injected into the prompt (grounding).
2. A retrieval outage degrades specificity, not availability (fail-open).
3. An Anthropic outage falls back to deterministic scoring instead of a 500.
4. The embedding circuit breaker stops hammering a provider that is down.

The fake Anthropic client records every prompt, so we assert on what the model
would have seen rather than on the model's own output.
"""

import json
import uuid
from datetime import date, datetime, timezone, timedelta

import anthropic
import httpx
import pytest

from app.models.assignment import Assignment, AssignmentStatus
from app.models.document_chunk import DocumentChunk
from app.models.job import JobApplication, JobStatus
from app.routers import ai as ai_router
from app.services import embedding
from app.services.scoring import score_signals


class _FakeUsage:
    input_tokens = 120
    output_tokens = 60


class _FakeBlock:
    type = "text"
    text = json.dumps({
        "priorities": [
            {"title": "Submit DSA assignment", "reason": "It is due tomorrow."},
            {"title": "Follow up with the recruiter", "reason": "The follow-up is overdue."},
            {"title": "Log a workout", "reason": "Consistency is slipping."},
        ],
        "summary": "Focus on the DSA deadline first.",
    })


class _FakeMessage:
    usage = _FakeUsage()
    content = [_FakeBlock()]


class _FakeMessages:
    """Records each request and returns a fixed, valid briefing."""

    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeMessage()


class _FakeClient:
    def __init__(self):
        self.messages = _FakeMessages()


@pytest.fixture
def fake_ai(monkeypatch):
    """Replace the Anthropic client and keep retrieval keyword-only."""
    client = _FakeClient()
    monkeypatch.setattr(ai_router, "client", client)
    # Never hit OpenAI in tests: an empty query embedding forces the
    # keyword-search path, which runs against SQLite.
    monkeypatch.setattr("app.services.rag.get_embedding", lambda text: [])
    return client


@pytest.fixture
def indexed_assignment(db_session, demo_user):
    """One assignment plus its index chunk, without calling OpenAI."""
    assignment = Assignment(
        id=uuid.uuid4(),
        user_id=demo_user.id,
        title="DSA Assignment",
        course="CS201",
        due_date=datetime.now(timezone.utc) + timedelta(days=1),
        estimated_hours=5,
        status=AssignmentStatus.pending,
    )
    db_session.add(assignment)
    db_session.add(DocumentChunk(
        user_id=demo_user.id,
        entity_type="assignment",
        entity_id=assignment.id,
        content=(
            "Assignment: DSA Assignment for CS201, due Nov 05, "
            "status: pending, estimated 5.0h"
        ),
    ))
    db_session.commit()
    return assignment


def test_briefing_grounds_prompt_in_retrieved_records(
    client, demo_user, auth_headers, fake_ai, indexed_assignment
):
    response = client.post("/ai/briefing", **auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["priorities"][0]["title"] == "Submit DSA assignment"
    assert data["cached"] is False

    # Retrieval metadata reports what grounded the generation.
    assert data["retrieval"]["chunks"] >= 1
    assert "assignment" in data["retrieval"]["sources"]

    # The model saw the retrieved row, not just aggregate counts.
    prompt = fake_ai.messages.calls[0]["messages"][0]["content"]
    assert "DSA Assignment" in prompt
    assert "retrieved_records" in prompt
    assert "Grounding rules" in prompt


def test_briefing_survives_retrieval_failure(
    client, demo_user, auth_headers, fake_ai, monkeypatch
):
    def unavailable(*args, **kwargs):
        raise RuntimeError("index unavailable")

    monkeypatch.setattr("app.services.context_builder.hybrid_search", unavailable)

    response = client.post("/ai/briefing", **auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["retrieval"]["chunks"] == 0
    assert data["retrieval"]["sources"] == []
    # The AI still generated a briefing from the aggregate context.
    assert len(data["priorities"]) == 3


def test_briefing_falls_back_when_anthropic_fails(
    client, demo_user, auth_headers, fake_ai, monkeypatch
):
    def fail(**kwargs):
        raise anthropic.APIConnectionError(
            request=httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        )

    monkeypatch.setattr(fake_ai.messages, "create", fail)

    response = client.post("/ai/briefing", **auth_headers)

    assert response.status_code == 200
    data = response.json()
    # Deterministic fallback shape: scores present, no retrieval metadata.
    assert data["cached"] is False
    assert data["retrieval"] is None
    assert len(data["priorities"]) == 3
    assert "scores" in data


def test_briefing_uses_fallback_without_ai_client(
    client, demo_user, auth_headers, monkeypatch
):
    monkeypatch.setattr(ai_router, "client", None)

    response = client.post("/ai/briefing", **auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["retrieval"] is None
    assert len(data["priorities"]) == 3
    assert data["priorities"][0]["domain"] in {
        "assignment", "job", "fitness", "finance", "tension", "general"
    }


def _overdue_job(demo_user):
    """A job whose follow-up date (a DATE column) has already passed."""
    today = datetime.now(timezone.utc).date()
    return JobApplication(
        id=uuid.uuid4(),
        user_id=demo_user.id,
        company="Acme",
        role="SWE Intern",
        applied_date=today - timedelta(days=10),
        followup_date=today - timedelta(days=3),
        status=JobStatus.applied,
    )


def test_score_signals_handles_date_followup(db_session, demo_user):
    """
    Regression: followup_date is a Date, not a DateTime.

    Calling .replace(tzinfo=...) on a date raises TypeError, which 500'd the
    briefing in production whenever a follow-up was overdue.
    """
    db_session.add(_overdue_job(demo_user))
    db_session.commit()

    signals = score_signals(db_session, demo_user)

    job_signals = [s for s in signals if s.domain == "job"]
    assert len(job_signals) == 1
    assert job_signals[0].title == "Follow up: SWE Intern at Acme"
    assert job_signals[0].meta["days_since_applied"] == 3


def test_briefing_handles_overdue_followup_date(
    client, demo_user, auth_headers, fake_ai, db_session
):
    db_session.add(_overdue_job(demo_user))
    db_session.commit()

    response = client.post("/ai/briefing", **auth_headers)

    assert response.status_code == 200
    prompt = fake_ai.messages.calls[0]["messages"][0]["content"]
    assert "Follow up: SWE Intern at Acme" in prompt


def test_embedding_circuit_breaker_stops_repeated_calls(monkeypatch):
    calls = []

    class _FailingEmbeddings:
        def create(self, **kwargs):
            calls.append(kwargs)
            raise RuntimeError("network down")

    class _FailingClient:
        embeddings = _FailingEmbeddings()

    monkeypatch.setattr(embedding, "_get_client", lambda: _FailingClient())
    embedding._reset_circuit()

    try:
        assert embedding.get_embedding("first query") == []
        assert len(calls) == 1

        # Breaker is open: the next call returns immediately, no API attempt.
        assert embedding.get_embedding("second query") == []
        assert len(calls) == 1

        # Batch calls degrade to one empty vector per input.
        assert embedding.get_embeddings_batch(["a", "b"]) == [[], []]
        assert len(calls) == 1
    finally:
        embedding._reset_circuit()
