"""
Reciprocal Rank Fusion (RRF) and Hybrid Search Unit Tests

Tests the pure math of RRF fusion, _cosine_similarity edge cases,
_keyword_terms tokenization, _keyword_search_fallback on SQLite, and the
output format contract of hybrid_search.

Design: items 1-8 mock _vector_search, _keyword_search, and get_embedding so
no database or network is needed. Items 9-11 use the SQLite db_session fixture
from conftest.py to exercise the real DB-backed paths.

RRF formula: score(chunk) = sum over lists of 1.0 / (k + rank)   k=60 default
"""

import math
import uuid
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.services.rag import (
    _cosine_similarity,
    _keyword_search_fallback,
    _keyword_terms,
    hybrid_search,
)
from app.models.document_chunk import DocumentChunk


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rrf(rank: int, k: int = 60) -> float:
    """Expected RRF contribution from a single ranked list."""
    return 1.0 / (k + rank)


def _make_chunk(entity_type="assignment", content="some content"):
    """
    Build a plain-namespace chunk object suitable for mock returns.

    hybrid_search accesses chunk.id, chunk.entity_type, chunk.entity_id, and
    chunk.content on the objects returned by _vector_search / _keyword_search.
    Using SimpleNamespace avoids the SQLAlchemy mapper initialisation that
    DocumentChunk.__new__() skips.
    """
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        entity_type=entity_type,
        entity_id=uuid.uuid4(),
        content=content,
        embedding=None,
    )


# Fake db session that satisfies hybrid_search's dialect check (SQLite).
class _FakeDialect:
    name = "sqlite"


class _FakeBind:
    dialect = _FakeDialect()


class _FakeSession:
    def get_bind(self):
        return _FakeBind()


_FAKE_DB = _FakeSession()

_MOCK_EMBEDDING = [0.1, 0.2, 0.3]


# ---------------------------------------------------------------------------
# 1. RRF math -- both lists agree (same items, same order)
# ---------------------------------------------------------------------------

class TestRRFBothListsAgree:
    """When vector and keyword return identical ranked lists the scores double."""

    def setup_method(self):
        self.chunk_a = _make_chunk(content="alpha content")
        self.chunk_b = _make_chunk(content="beta content")
        # Both lists: chunk_a rank 1, chunk_b rank 2
        self.vector_results = [(self.chunk_a, 0.9), (self.chunk_b, 0.8)]
        self.keyword_results = [(self.chunk_a, 0.9), (self.chunk_b, 0.5)]

    def test_scores_accumulate_from_both_lists(self):
        """chunk_a score = 1/(60+1) + 1/(60+1); chunk_b = 1/(60+2) + 1/(60+2)."""
        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search", return_value=self.vector_results),
            patch("app.services.rag._keyword_search", return_value=self.keyword_results),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query", limit=10)

        assert len(results) == 2

        expected_a = round(_rrf(1) + _rrf(1), 6)
        expected_b = round(_rrf(2) + _rrf(2), 6)

        result_a = next(r for r in results if r["id"] == str(self.chunk_a.id))
        result_b = next(r for r in results if r["id"] == str(self.chunk_b.id))

        assert result_a["score"] == expected_a
        assert result_b["score"] == expected_b

    def test_ranking_preserves_order_when_lists_agree(self):
        """chunk_a is #1 from both lists so must be #1 in merged output."""
        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search", return_value=self.vector_results),
            patch("app.services.rag._keyword_search", return_value=self.keyword_results),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query", limit=10)

        assert results[0]["id"] == str(self.chunk_a.id)
        assert results[1]["id"] == str(self.chunk_b.id)


# ---------------------------------------------------------------------------
# 2. RRF math -- completely disjoint lists
# ---------------------------------------------------------------------------

class TestRRFDisjointLists:
    """Items from vector-only or keyword-only each contribute once."""

    def setup_method(self):
        self.vec_chunk = _make_chunk(content="vector content")
        self.kw_chunk = _make_chunk(content="keyword content")
        # Completely disjoint -- different chunks
        self.vector_results = [(self.vec_chunk, 0.95)]
        self.keyword_results = [(self.kw_chunk, 0.80)]

    def test_each_item_scores_once(self):
        """vec_chunk score = 1/(60+1); kw_chunk score = 1/(60+1)."""
        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search", return_value=self.vector_results),
            patch("app.services.rag._keyword_search", return_value=self.keyword_results),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query", limit=10)

        assert len(results) == 2
        expected = round(_rrf(1), 6)
        for r in results:
            assert r["score"] == expected

    def test_rank1_beats_rank2_across_disjoint_lists(self):
        """
        rank-1 in one list (1/61) beats rank-2 in another (1/62).
        Setup: vec rank 1 at score 0.95; kw has two chunks, rank 1 and rank 2.
        """
        kw_rank1 = _make_chunk(content="kw first")
        kw_rank2 = _make_chunk(content="kw second")
        vec_rank1 = _make_chunk(content="vec first")

        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search", return_value=[(vec_rank1, 0.9)]),
            patch("app.services.rag._keyword_search",
                  return_value=[(kw_rank1, 0.8), (kw_rank2, 0.5)]),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query", limit=10)

        # Both vec_rank1 and kw_rank1 have score 1/61; kw_rank2 has 1/62.
        ids = [r["id"] for r in results]
        kw_rank2_idx = ids.index(str(kw_rank2.id))
        # kw_rank2 must be last (lowest score)
        assert kw_rank2_idx == len(results) - 1


# ---------------------------------------------------------------------------
# 3. RRF math -- partially overlapping lists
# ---------------------------------------------------------------------------

class TestRRFPartialOverlap:
    """Items in both lists accumulate scores; unique items score once."""

    def setup_method(self):
        self.shared = _make_chunk(content="shared chunk appears in both lists")
        self.vec_only = _make_chunk(content="vector only result")
        self.kw_only = _make_chunk(content="keyword only result")

        # shared is rank 1 in vector, rank 1 in keyword.
        # unique items are rank 2 in their respective list.
        self.vector_results = [(self.shared, 0.95), (self.vec_only, 0.70)]
        self.keyword_results = [(self.shared, 0.80), (self.kw_only, 0.55)]

    def test_shared_chunk_beats_unique_chunks_at_same_rank(self):
        """shared has 2*(1/61) while vec_only and kw_only each have 1/62."""
        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search", return_value=self.vector_results),
            patch("app.services.rag._keyword_search", return_value=self.keyword_results),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query", limit=10)

        assert len(results) == 3
        assert results[0]["id"] == str(self.shared.id)

        expected_shared = round(_rrf(1) + _rrf(1), 6)
        expected_unique = round(_rrf(2), 6)

        assert results[0]["score"] == expected_shared
        # The two unique items should both have the lower unique score
        for r in results[1:]:
            assert r["score"] == expected_unique

    def test_all_three_chunks_appear_in_results(self):
        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search", return_value=self.vector_results),
            patch("app.services.rag._keyword_search", return_value=self.keyword_results),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query", limit=10)

        ids = {r["id"] for r in results}
        assert str(self.shared.id) in ids
        assert str(self.vec_only.id) in ids
        assert str(self.kw_only.id) in ids


# ---------------------------------------------------------------------------
# 4. Ties -- items with equal RRF score
# ---------------------------------------------------------------------------

class TestRRFTies:
    """Items with equal score can appear in any order; count must be correct."""

    def test_tied_items_all_present(self):
        """
        Two chunks appear only in vector list at ranks 1 and 1 -- impossible
        (each has a unique rank), so we design a tie: chunk_x rank 2 in vector,
        chunk_y rank 2 in keyword. Both get score 1/(60+2). Both must appear.
        """
        chunk_x = _make_chunk(content="chunk x")
        chunk_y = _make_chunk(content="chunk y")
        top = _make_chunk(content="top chunk rank 1")

        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search",
                  return_value=[(top, 0.99), (chunk_x, 0.70)]),
            patch("app.services.rag._keyword_search",
                  return_value=[(top, 0.90), (chunk_y, 0.60)]),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query", limit=10)

        ids = {r["id"] for r in results}
        assert str(chunk_x.id) in ids
        assert str(chunk_y.id) in ids
        assert len(results) == 3

        # top must be first (double score)
        assert results[0]["id"] == str(top.id)

        # chunk_x and chunk_y both have score 1/(60+2)
        tied_scores = {r["score"] for r in results[1:]}
        assert len(tied_scores) == 1
        assert list(tied_scores)[0] == round(_rrf(2), 6)

    def test_tied_exact_score_count(self):
        """When three unique chunks all appear only in keyword at ranks 1,2,3."""
        c1 = _make_chunk(content="kw one")
        c2 = _make_chunk(content="kw two")
        c3 = _make_chunk(content="kw three")

        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search", return_value=[]),
            patch("app.services.rag._keyword_search",
                  return_value=[(c1, 0.9), (c2, 0.6), (c3, 0.3)]),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query", limit=10)

        assert len(results) == 3
        scores = [r["score"] for r in results]
        # Strictly descending
        assert scores[0] > scores[1] > scores[2]
        assert scores[0] == round(_rrf(1), 6)
        assert scores[1] == round(_rrf(2), 6)
        assert scores[2] == round(_rrf(3), 6)


# ---------------------------------------------------------------------------
# 5. Empty lists -- both empty
# ---------------------------------------------------------------------------

class TestEmptyLists:
    def test_both_empty_returns_empty_list(self):
        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search", return_value=[]),
            patch("app.services.rag._keyword_search", return_value=[]),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query")

        assert results == []

    # 6. Only vector results (keyword empty)
    def test_only_vector_results(self):
        """Results come from vector only; each score = 1/(60+rank)."""
        c1 = _make_chunk(content="vec one")
        c2 = _make_chunk(content="vec two")

        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search",
                  return_value=[(c1, 0.9), (c2, 0.7)]),
            patch("app.services.rag._keyword_search", return_value=[]),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query", limit=10)

        assert len(results) == 2
        assert results[0]["score"] == round(_rrf(1), 6)
        assert results[1]["score"] == round(_rrf(2), 6)
        assert results[0]["id"] == str(c1.id)
        # vector_score present, keyword_score absent
        assert results[0]["vector_score"] == round(0.9, 4)
        assert results[0]["keyword_score"] is None

    # 7. Only keyword results (get_embedding returns empty)
    def test_only_keyword_results_when_embedding_unavailable(self):
        """When get_embedding returns [], hybrid_search uses keyword only."""
        kw1 = _make_chunk(content="keyword only one")
        kw2 = _make_chunk(content="keyword only two")

        with (
            patch("app.services.rag.get_embedding", return_value=[]),
            patch("app.services.rag._keyword_search",
                  return_value=[(kw1, 0.8), (kw2, 0.4)]),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query", limit=10)

        assert len(results) == 2
        assert results[0]["score"] == round(_rrf(1), 6)
        assert results[1]["score"] == round(_rrf(2), 6)
        # keyword_score present, vector_score absent
        assert results[0]["keyword_score"] == round(0.8, 4)
        assert results[0]["vector_score"] is None

    def test_get_embedding_none_treated_as_empty(self):
        """If get_embedding returns None (mocked), no vector search runs."""
        kw1 = _make_chunk(content="keyword chunk")

        with (
            patch("app.services.rag.get_embedding", return_value=None),
            patch("app.services.rag._keyword_search",
                  return_value=[(kw1, 1.0)]),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query", limit=10)

        # Should still return keyword results
        assert len(results) == 1
        assert results[0]["id"] == str(kw1.id)
        assert results[0]["vector_score"] is None


# ---------------------------------------------------------------------------
# 8. _cosine_similarity edge cases
# ---------------------------------------------------------------------------

class TestCosineSimilarity:
    def test_both_zero_vectors_returns_zero(self):
        assert _cosine_similarity([0.0, 0.0], [0.0, 0.0]) == 0.0

    def test_different_length_vectors_returns_zero(self):
        assert _cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0]) == 0.0

    def test_empty_lists_returns_zero(self):
        assert _cosine_similarity([], []) == 0.0

    def test_one_empty_one_non_empty_returns_zero(self):
        assert _cosine_similarity([], [1.0, 2.0]) == 0.0
        assert _cosine_similarity([1.0, 2.0], []) == 0.0

    def test_perfect_similarity_same_vector(self):
        v = [1.0, 2.0, 3.0]
        result = _cosine_similarity(v, v)
        assert math.isclose(result, 1.0, rel_tol=1e-9)

    def test_orthogonal_vectors_returns_zero(self):
        # [1, 0] and [0, 1] are orthogonal: dot product = 0
        assert _cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0

    def test_opposite_vectors_returns_negative_one(self):
        # [1, 0] and [-1, 0]: cosine = -1
        result = _cosine_similarity([1.0, 0.0], [-1.0, 0.0])
        assert math.isclose(result, -1.0, rel_tol=1e-9)

    def test_known_similarity(self):
        # [3, 4] . [4, 3] = 12 + 12 = 24; |[3,4]| = 5; |[4,3]| = 5; sim = 24/25
        result = _cosine_similarity([3.0, 4.0], [4.0, 3.0])
        assert math.isclose(result, 24.0 / 25.0, rel_tol=1e-9)

    def test_one_zero_vector_returns_zero(self):
        assert _cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0
        assert _cosine_similarity([1.0, 2.0], [0.0, 0.0]) == 0.0


# ---------------------------------------------------------------------------
# 9. _keyword_terms tokenization
# ---------------------------------------------------------------------------

class TestKeywordTerms:
    def test_strips_punctuation_and_splits(self):
        terms = _keyword_terms("Hello, World! Foo-Bar.")
        assert "hello" in terms
        assert "world" in terms
        assert "foo" in terms
        assert "bar" in terms

    def test_lowercases_everything(self):
        terms = _keyword_terms("UPPER lower MiXeD")
        assert all(t == t.lower() for t in terms)

    def test_filters_single_character_terms(self):
        terms = _keyword_terms("a b c word")
        # 'a', 'b', 'c' are length 1 and should be excluded
        for t in terms:
            assert len(t) > 1

    def test_caps_at_16_terms(self):
        query = " ".join(f"term{i:02d}" for i in range(30))
        terms = _keyword_terms(query)
        assert len(terms) == 16

    def test_alphanumeric_only(self):
        terms = _keyword_terms("price: $99.99 for item!")
        # Only alphanumeric parts survive: "price", "99", "99", "for", "item"
        for t in terms:
            assert t.isalnum()

    def test_empty_string_returns_empty(self):
        assert _keyword_terms("") == []

    def test_only_punctuation_returns_empty(self):
        assert _keyword_terms("!!! ??? ---") == []

    def test_numbers_are_kept(self):
        terms = _keyword_terms("CS320 due 2026")
        assert "cs320" in terms
        assert "2026" in terms

    def test_mixed_alphanumeric_kept_as_one_token(self):
        # "CS320" contains letters and digits; it's one alphanumeric run
        terms = _keyword_terms("CS320")
        assert terms == ["cs320"]

    def test_default_limit_is_16(self):
        query = " ".join(f"word{i:02d}" for i in range(20))
        result = _keyword_terms(query)
        assert len(result) == 16

    def test_custom_limit_respected(self):
        query = " ".join(f"word{i:02d}" for i in range(10))
        result = _keyword_terms(query, limit=5)
        assert len(result) == 5


# ---------------------------------------------------------------------------
# 10. _keyword_search_fallback integration tests (SQLite via db_session)
# ---------------------------------------------------------------------------

class TestKeywordSearchFallback:
    """Uses the real SQLite db from conftest.py's db_session fixture."""

    def _create_chunk(self, db, user_id, content, entity_type="assignment"):
        chunk = DocumentChunk(
            id=uuid.uuid4(),
            user_id=user_id,
            entity_type=entity_type,
            entity_id=uuid.uuid4(),
            content=content,
        )
        db.add(chunk)
        db.flush()
        return chunk

    def test_returns_chunks_matching_query_terms(self, db_session, demo_user):
        self._create_chunk(db_session, demo_user.id, "CS Final Project due tomorrow")
        self._create_chunk(db_session, demo_user.id, "workout log for monday")
        db_session.commit()

        results = _keyword_search_fallback(
            db_session, demo_user.id, "CS Final", None, 10
        )
        contents = [chunk.content for chunk, _ in results]
        assert any("CS Final" in c for c in contents)

    def test_ignores_chunks_with_no_matching_terms(self, db_session, demo_user):
        self._create_chunk(db_session, demo_user.id, "workout log for monday")
        db_session.commit()

        results = _keyword_search_fallback(
            db_session, demo_user.id, "chemistry assignment", None, 10
        )
        # None of the chunks contain "chemistry" or "assignment"
        assert results == []

    def test_empty_query_returns_empty(self, db_session, demo_user):
        self._create_chunk(db_session, demo_user.id, "some content here")
        db_session.commit()

        results = _keyword_search_fallback(
            db_session, demo_user.id, "!!! ???", None, 10
        )
        assert results == []

    def test_respects_entity_types_filter(self, db_session, demo_user):
        self._create_chunk(
            db_session, demo_user.id, "workout running session", "workout"
        )
        self._create_chunk(
            db_session, demo_user.id, "workout assignment review", "assignment"
        )
        db_session.commit()

        results = _keyword_search_fallback(
            db_session, demo_user.id, "workout", ["workout"], 10
        )
        entity_types = {chunk.entity_type for chunk, _ in results}
        assert entity_types == {"workout"}

    def test_scores_by_fraction_of_terms_matched(self, db_session, demo_user):
        # Chunk A matches 2/2 terms (score 1.0)
        # Chunk B matches 1/2 terms (score 0.5)
        self._create_chunk(
            db_session, demo_user.id,
            "assignment final project submission"
        )
        self._create_chunk(
            db_session, demo_user.id,
            "assignment unrelated content"
        )
        db_session.commit()

        results = _keyword_search_fallback(
            db_session, demo_user.id, "final submission", None, 10
        )
        # First result should have higher or equal score
        assert len(results) >= 1
        if len(results) > 1:
            assert results[0][1] >= results[1][1]

    def test_scores_sorted_descending(self, db_session, demo_user):
        """Results must be sorted by score descending."""
        self._create_chunk(db_session, demo_user.id, "alpha beta gamma")
        self._create_chunk(db_session, demo_user.id, "alpha content only")
        self._create_chunk(db_session, demo_user.id, "unrelated entry")
        db_session.commit()

        results = _keyword_search_fallback(
            db_session, demo_user.id, "alpha beta gamma", None, 10
        )
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True)

    def test_respects_candidate_limit(self, db_session, demo_user):
        for i in range(5):
            self._create_chunk(
                db_session, demo_user.id, f"matching content number {i}"
            )
        db_session.commit()

        results = _keyword_search_fallback(
            db_session, demo_user.id, "matching content", None, 3
        )
        assert len(results) <= 3

    def test_user_isolation(self, db_session, demo_user):
        """Chunks from another user must not appear in results."""
        other_user_id = uuid.uuid4()
        self._create_chunk(db_session, other_user_id, "matching assignment due")
        self._create_chunk(db_session, demo_user.id, "unrelated entry here")
        db_session.commit()

        results = _keyword_search_fallback(
            db_session, demo_user.id, "matching assignment", None, 10
        )
        user_ids = {chunk.user_id for chunk, _ in results}
        # Should only contain demo_user chunks (or be empty if none match)
        for uid in user_ids:
            assert uid == demo_user.id


# ---------------------------------------------------------------------------
# 11. hybrid_search output format contract
# ---------------------------------------------------------------------------

class TestHybridSearchOutputFormat:
    """Verify the shape and rounding of every dict returned by hybrid_search."""

    def test_output_has_required_keys(self):
        chunk = _make_chunk(content="formatted output test")

        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search", return_value=[(chunk, 0.75)]),
            patch("app.services.rag._keyword_search", return_value=[]),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query")

        assert len(results) == 1
        r = results[0]
        required_keys = {"id", "entity_type", "entity_id", "content", "score",
                         "vector_score", "keyword_score"}
        assert required_keys == set(r.keys())

    def test_score_rounded_to_6_decimal_places(self):
        chunk = _make_chunk(content="rounding test")

        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search", return_value=[(chunk, 0.123456789)]),
            patch("app.services.rag._keyword_search", return_value=[]),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query")

        score = results[0]["score"]
        # Must be rounded to 6 decimal places
        assert score == round(score, 6)
        # Verify it has at most 6 significant decimal digits
        decimal_str = str(score).split(".")
        if len(decimal_str) > 1:
            assert len(decimal_str[1]) <= 6

    def test_vector_score_present_when_in_vector_results(self):
        chunk = _make_chunk(content="vector score test")

        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search", return_value=[(chunk, 0.8765)]),
            patch("app.services.rag._keyword_search", return_value=[]),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query")

        assert results[0]["vector_score"] == round(0.8765, 4)
        assert results[0]["keyword_score"] is None

    def test_keyword_score_present_when_in_keyword_results(self):
        chunk = _make_chunk(content="keyword score test")

        with (
            patch("app.services.rag.get_embedding", return_value=[]),
            patch("app.services.rag._keyword_search", return_value=[(chunk, 0.6543)]),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query")

        assert results[0]["keyword_score"] == round(0.6543, 4)
        assert results[0]["vector_score"] is None

    def test_both_scores_present_when_in_both_results(self):
        chunk = _make_chunk(content="both scores test")

        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search", return_value=[(chunk, 0.9)]),
            patch("app.services.rag._keyword_search", return_value=[(chunk, 0.7)]),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query")

        r = results[0]
        assert r["vector_score"] == round(0.9, 4)
        assert r["keyword_score"] == round(0.7, 4)

    def test_id_is_string(self):
        chunk = _make_chunk(content="id format test")

        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search", return_value=[(chunk, 0.5)]),
            patch("app.services.rag._keyword_search", return_value=[]),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query")

        assert isinstance(results[0]["id"], str)
        assert isinstance(results[0]["entity_id"], str)

    def test_entity_type_and_content_preserved(self):
        chunk = _make_chunk(entity_type="job", content="job application content")

        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search", return_value=[(chunk, 0.5)]),
            patch("app.services.rag._keyword_search", return_value=[]),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query")

        assert results[0]["entity_type"] == "job"
        assert results[0]["content"] == "job application content"

    def test_limit_caps_returned_results(self):
        chunks = [_make_chunk(content=f"chunk {i}") for i in range(10)]
        vec_results = [(c, 1.0 - i * 0.05) for i, c in enumerate(chunks)]

        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search", return_value=vec_results),
            patch("app.services.rag._keyword_search", return_value=[]),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query", limit=5)

        assert len(results) == 5

    def test_results_sorted_by_score_descending(self):
        """Results must be ordered highest score first."""
        chunks = [_make_chunk(content=f"chunk {i}") for i in range(5)]
        vec_results = [(c, 1.0 - i * 0.1) for i, c in enumerate(chunks)]

        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search", return_value=vec_results),
            patch("app.services.rag._keyword_search", return_value=[]),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query", limit=10)

        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_custom_rrf_k_changes_scores(self):
        """Passing rrf_k=10 should change the scores compared to default k=60."""
        chunk = _make_chunk(content="custom k test")

        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search", return_value=[(chunk, 0.9)]),
            patch("app.services.rag._keyword_search", return_value=[]),
        ):
            results_k60 = hybrid_search(_FAKE_DB, uuid.uuid4(), "query", rrf_k=60)
            results_k10 = hybrid_search(_FAKE_DB, uuid.uuid4(), "query", rrf_k=10)

        expected_k60 = round(1.0 / (60 + 1), 6)
        expected_k10 = round(1.0 / (10 + 1), 6)

        assert results_k60[0]["score"] == expected_k60
        assert results_k10[0]["score"] == expected_k10
        assert results_k60[0]["score"] != results_k10[0]["score"]


# ---------------------------------------------------------------------------
# Extra: RRF math correctness -- exact formula verification
# ---------------------------------------------------------------------------

class TestRRFExactFormula:
    """Verify the exact RRF formula values to 6 decimal places."""

    def test_rrf_formula_rank_1_k60(self):
        """Single item at rank 1, k=60: score = 1/61."""
        chunk = _make_chunk(content="rank 1 item")

        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search", return_value=[(chunk, 0.9)]),
            patch("app.services.rag._keyword_search", return_value=[]),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query", rrf_k=60)

        assert results[0]["score"] == round(1.0 / 61.0, 6)

    def test_rrf_formula_rank_1_both_lists(self):
        """Item at rank 1 in both lists, k=60: score = 2/61."""
        chunk = _make_chunk(content="rank 1 both")

        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search", return_value=[(chunk, 0.9)]),
            patch("app.services.rag._keyword_search", return_value=[(chunk, 0.8)]),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query", rrf_k=60)

        assert results[0]["score"] == round(2.0 / 61.0, 6)

    def test_rrf_formula_descending_ranks(self):
        """Items at ranks 1,2,3 produce scores 1/61, 1/62, 1/63."""
        c1 = _make_chunk(content="rank 1")
        c2 = _make_chunk(content="rank 2")
        c3 = _make_chunk(content="rank 3")

        with (
            patch("app.services.rag.get_embedding", return_value=_MOCK_EMBEDDING),
            patch("app.services.rag._vector_search",
                  return_value=[(c1, 0.9), (c2, 0.7), (c3, 0.5)]),
            patch("app.services.rag._keyword_search", return_value=[]),
        ):
            results = hybrid_search(_FAKE_DB, uuid.uuid4(), "query", limit=10)

        assert results[0]["score"] == round(1.0 / 61.0, 6)
        assert results[1]["score"] == round(1.0 / 62.0, 6)
        assert results[2]["score"] == round(1.0 / 63.0, 6)
