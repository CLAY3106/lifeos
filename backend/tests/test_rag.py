"""
RAG Search Tests — Keyword SQL Shape and Tokenization

The PostgreSQL keyword path cannot run on SQLite (no tsvector), so these tests
use a fake session to inspect the generated SQL and parameters. The SQLite
fallback and the RRF fusion are exercised indirectly by the AI briefing tests.

The important regression here: keyword terms must be OR-ed, not AND-ed. A
briefing query spans several signals, and no single chunk contains every word
from all of them.
"""

import uuid

from app.services.rag import _keyword_search, _keyword_terms


class _FakeDialect:
    name = "postgresql"


class _FakeBind:
    dialect = _FakeDialect()


class _FakeResult:
    def fetchall(self):
        return []


class _FakeSession:
    """Captures the raw SQL and params instead of executing them."""

    def __init__(self):
        self.executed = []

    def get_bind(self):
        return _FakeBind()

    def execute(self, statement, params):
        self.executed.append((str(statement), params))
        return _FakeResult()


def test_keyword_terms_normalizes_and_caps():
    terms = _keyword_terms("Overdue: CS Final Project (assignment)")
    assert terms == ["overdue", "cs", "final", "project", "assignment"]

    long_query = " ".join(f"term{i}" for i in range(30))
    assert len(_keyword_terms(long_query)) == 16


def test_keyword_search_uses_or_semantics():
    db = _FakeSession()

    _keyword_search(db, uuid.uuid4(), "overdue cs final project", None, 10)

    sql, params = db.executed[0]
    assert "plainto_tsquery" in sql
    # OR, not AND: every term is a separate tsquery joined with `||`.
    assert "||" in sql
    assert "search_vector @@ q.query" in sql
    assert params["t0"] == "overdue"
    assert params["t3"] == "project"
    assert params["lim"] == 10


def test_keyword_search_ignores_empty_queries():
    db = _FakeSession()

    result = _keyword_search(db, uuid.uuid4(), "!!! ???", None, 10)

    assert result == []
    assert db.executed == []
