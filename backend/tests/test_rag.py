"""
Tests for the RAG pipeline: chunking, ingestion, and hybrid search.

The OpenAI embedding calls are replaced with a deterministic fake embedder
(hashed bag-of-words), so these tests need no API key and never hit the
network. Tests run on SQLite, which exercises the keyword-search fallback;
the PostgreSQL ts_rank_cd path is covered by the retrieval eval instead.
"""

import hashlib
import math
import re
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.assignment import Assignment, AssignmentStatus
from app.models.document_chunk import DocumentChunk
from app.models.expense import BudgetGroup, Expense, ExpenseCategory
from app.models.job import JobApplication, JobStatus
from app.models.user import User
from app.models.workout import Workout
from app.services import rag
from app.services.auth import hash_password

DIM = 64


def fake_embed(text: str) -> list[float]:
    """Hashed bag-of-words vector. Texts sharing words get similar vectors."""
    vec = [0.0] * DIM
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        bucket = int(hashlib.md5(token.encode()).hexdigest(), 16) % DIM
        vec[bucket] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


@pytest.fixture(autouse=True)
def fake_embeddings(monkeypatch):
    monkeypatch.setattr(rag, "get_embedding", fake_embed)
    monkeypatch.setattr(rag, "get_embeddings_batch", lambda texts: [fake_embed(t) for t in texts])


def _make_user(db, email):
    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hash_password("pw123456"),
        name="U",
        monthly_budget=300,
        weekly_capacity_hours=40,
    )
    db.add(user)
    db.commit()
    return user


def _seed(db, user):
    now = datetime.now(timezone.utc)
    db.add_all([
        Assignment(user_id=user.id, title="Linear Algebra Problem Set 7", course="MATH 240",
                   due_date=now + timedelta(days=2), estimated_hours=3,
                   status=AssignmentStatus.pending),
        Assignment(user_id=user.id, title="Operating Systems Lab", course="COMP 315",
                   due_date=now + timedelta(days=5), estimated_hours=4,
                   status=AssignmentStatus.pending),
        Assignment(user_id=user.id, title="Deleted essay", course="ENGL 101",
                   due_date=now, deleted_at=now),
        JobApplication(user_id=user.id, company="Stripe", role="Software Engineer Intern",
                       applied_date=date.today(), status=JobStatus.oa,
                       notes="online assessment due Friday"),
        Expense(user_id=user.id, amount=12.5, category=ExpenseCategory.food,
                note="ramen dinner", spent_at=now, group_override=BudgetGroup.wants),
        Workout(user_id=user.id, type="cardio", duration_mins=30, notes="5k run"),
    ])
    db.commit()


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def test_chunk_formats_include_searchable_fields(db_session, demo_user):
    _seed(db_session, demo_user)
    job = db_session.query(JobApplication).filter_by(user_id=demo_user.id).one()
    expense = db_session.query(Expense).filter_by(user_id=demo_user.id).one()
    workout = db_session.query(Workout).filter_by(user_id=demo_user.id).one()

    job_text = rag.chunk_job(job)
    assert "Stripe" in job_text and "status: oa" in job_text and "online assessment" in job_text
    assert rag.chunk_expense(expense).startswith("Expense: $12.50")
    assert "ramen dinner" in rag.chunk_expense(expense)
    assert rag.chunk_workout(workout) == "Workout: cardio for 30min, 5k run"


def test_chunk_assignment_without_course(db_session, demo_user):
    a = Assignment(user_id=demo_user.id, title="Read chapter 3",
                   due_date=datetime(2026, 11, 20), estimated_hours=1.0,
                   status=AssignmentStatus.pending)
    assert rag.chunk_assignment(a) == (
        "Assignment: Read chapter 3, due Nov 20, status: pending, estimated 1.0h"
    )


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------

def test_ingest_all_indexes_every_entity_and_skips_soft_deleted(db_session, demo_user):
    _seed(db_session, demo_user)
    count = rag.ingest_all(db_session, demo_user)

    assert count == 5  # 2 live assignments + job + expense + workout
    chunks = db_session.query(DocumentChunk).filter_by(user_id=demo_user.id).all()
    assert len(chunks) == 5
    assert not any("Deleted essay" in c.content for c in chunks)
    assert all(c.embedding for c in chunks)


def test_ingest_all_is_idempotent(db_session, demo_user):
    _seed(db_session, demo_user)
    rag.ingest_all(db_session, demo_user)
    rag.ingest_all(db_session, demo_user)
    assert db_session.query(DocumentChunk).filter_by(user_id=demo_user.id).count() == 5


def test_ingest_all_survives_embedding_outage(db_session, demo_user, monkeypatch):
    """A failed batch stores chunks without embeddings instead of crashing."""
    _seed(db_session, demo_user)
    monkeypatch.setattr(rag, "get_embeddings_batch", lambda texts: [])
    assert rag.ingest_all(db_session, demo_user) == 5
    chunks = db_session.query(DocumentChunk).filter_by(user_id=demo_user.id).all()
    assert all(c.embedding is None for c in chunks)


def test_ingest_entity_updates_in_place(db_session, demo_user):
    entity_id = uuid.uuid4()
    rag.ingest_entity(db_session, demo_user.id, "workout", entity_id, "Workout: push for 45min")
    rag.ingest_entity(db_session, demo_user.id, "workout", entity_id, "Workout: pull for 50min")
    rows = db_session.query(DocumentChunk).filter_by(entity_id=entity_id).all()
    assert len(rows) == 1
    assert rows[0].content == "Workout: pull for 50min"


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def test_search_finds_relevant_chunk_first(db_session, demo_user):
    _seed(db_session, demo_user)
    rag.ingest_all(db_session, demo_user)
    results = rag.hybrid_search(db_session, demo_user.id, "Stripe online assessment")
    assert results
    assert results[0]["entity_type"] == "job"
    assert "Stripe" in results[0]["content"]


def test_search_is_scoped_to_the_user(db_session, demo_user):
    other = _make_user(db_session, "other@lifeos.app")
    _seed(db_session, other)
    rag.ingest_all(db_session, other)

    assert rag.hybrid_search(db_session, demo_user.id, "Stripe online assessment") == []


def test_search_respects_entity_type_filter(db_session, demo_user):
    _seed(db_session, demo_user)
    rag.ingest_all(db_session, demo_user)
    results = rag.hybrid_search(db_session, demo_user.id, "due", entity_types=["assignment"])
    assert results
    assert {r["entity_type"] for r in results} == {"assignment"}


def test_search_degrades_to_keyword_only_without_embeddings(db_session, demo_user, monkeypatch):
    _seed(db_session, demo_user)
    rag.ingest_all(db_session, demo_user)
    monkeypatch.setattr(rag, "get_embedding", lambda text: [])

    results = rag.hybrid_search(db_session, demo_user.id, "ramen dinner")
    assert results[0]["entity_type"] == "expense"
    assert results[0]["vector_score"] is None
    assert results[0]["keyword_score"] is not None


def test_search_on_empty_index_returns_empty(db_session, demo_user):
    assert rag.hybrid_search(db_session, demo_user.id, "anything at all") == []


def test_rrf_rewards_agreement_between_lists(db_session, demo_user, monkeypatch):
    """A chunk ranked by both searches must beat chunks ranked by only one."""
    ids = [uuid.uuid4() for _ in range(3)]
    chunks = [
        DocumentChunk(id=i, user_id=demo_user.id, entity_type="job", entity_id=uuid.uuid4(),
                      content=f"chunk {n}")
        for n, i in enumerate(ids)
    ]
    a, b, c = chunks
    # a: rank 1 in vector only. b: rank 1 in keyword only. c: rank 2 in both.
    monkeypatch.setattr(rag, "_vector_search", lambda *args, **kw: [(a, 0.9), (c, 0.8)])
    monkeypatch.setattr(rag, "_keyword_search", lambda *args, **kw: [(b, 0.9), (c, 0.8)])

    results = rag.hybrid_search(db_session, demo_user.id, "q", rrf_k=60)
    assert results[0]["id"] == str(c.id)
    assert results[0]["score"] == pytest.approx(2 / 62, abs=1e-6)
    assert {r["id"] for r in results[1:]} == {str(a.id), str(b.id)}


def test_search_respects_limit(db_session, demo_user):
    _seed(db_session, demo_user)
    rag.ingest_all(db_session, demo_user)
    assert len(rag.hybrid_search(db_session, demo_user.id, "due status", limit=2)) == 2


@pytest.mark.parametrize("a,b,expected", [
    ([1.0, 0.0], [1.0, 0.0], 1.0),
    ([1.0, 0.0], [0.0, 1.0], 0.0),
    ([1.0, 0.0], [-1.0, 0.0], -1.0),
    ([], [1.0], 0.0),
    ([1.0, 2.0], [1.0], 0.0),
    ([0.0, 0.0], [1.0, 1.0], 0.0),
])
def test_cosine_similarity_edge_cases(a, b, expected):
    assert rag._cosine_similarity(a, b) == pytest.approx(expected)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def test_rag_endpoints_require_auth(client):
    assert client.post("/rag/search", json={"query": "x"}).status_code == 401
    assert client.post("/rag/ingest").status_code == 401


def test_rag_ingest_then_search_via_api(client, db_session, demo_user, auth_headers):
    _seed(db_session, demo_user)
    ingest = client.post("/rag/ingest", **auth_headers)
    assert ingest.status_code == 200
    assert ingest.json()["chunks_indexed"] == 5

    search = client.post("/rag/search", json={"query": "linear algebra", "limit": 3}, **auth_headers)
    assert search.status_code == 200
    body = search.json()
    assert 1 <= len(body) <= 3
    assert "Linear Algebra" in body[0]["content"]
