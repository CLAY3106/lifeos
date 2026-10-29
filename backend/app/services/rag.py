"""
RAG Service — Chunking, Ingestion, and Hybrid Search

Pipeline:
    Entity -> chunk_*() -> get_embedding() -> document_chunks
    Query  -> hybrid_search() -> top-k chunks -> AI briefing context

Search combines two independent signals:
1. Vector search (semantic): cosine similarity between the query embedding
   and each chunk embedding. Finds conceptually related text even when the
   words differ ("final exam" ~ "midterm").
2. BM25-style keyword search: PostgreSQL full-text ranking (ts_rank_cd) over
   the generated search_vector column. Finds exact terms, names, and numbers
   that embeddings tend to blur.

The two ranked lists are merged with Reciprocal Rank Fusion (RRF):
    score(chunk) = sum over lists of 1 / (k + rank)
RRF needs no score normalization and is robust when the two search methods
produce scores on completely different scales.
"""

import json
import math
import re
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.services.embedding import get_embedding, get_embeddings_batch


# ---------------------------------------------------------------------------
# Chunking — turn one entity into one searchable text unit
# ---------------------------------------------------------------------------

def chunk_assignment(assignment) -> str:
    course_part = f" for {assignment.course}" if assignment.course else ""
    return (
        f"Assignment: {assignment.title}{course_part}, "
        f"due {assignment.due_date.strftime('%b %d')}, "
        f"status: {assignment.status.value}, "
        f"estimated {assignment.estimated_hours}h"
    )


def chunk_expense(expense) -> str:
    return (
        f"Expense: ${expense.amount:.2f} spend on {expense.note if expense.note else 'None'}, "
        f"{expense.category.value}, "
        f"{expense.group_override.value if expense.group_override else 'None'}, "
        f"spent at {expense.spent_at.strftime('%b %d') if expense.spent_at else 'None'}"
    )


def chunk_job(job) -> str:
    location_part = f", {job.location}" if job.location else ""
    notes_part = f", {job.notes}" if job.notes else ""
    return (
        f"Job Application: {job.role} at {job.company}, "
        f"applied {job.applied_date.strftime('%b %d')}, "
        f"status: {job.status.value}{location_part}{notes_part}"
    )


def chunk_workout(workout) -> str:
    notes_part = f", {workout.notes}" if workout.notes else ""
    return (
        f"Workout: {workout.type} for {workout.duration_mins}min{notes_part}"
    )


# ---------------------------------------------------------------------------
# Ingestion — embed chunks and store them in document_chunks
# ---------------------------------------------------------------------------

def ingest_entity(db: Session, user_id, entity_type: str, entity_id, text_content: str):
    """
    Embed a single chunk and store it in document_chunks.

    If a chunk already exists for this (user, entity_type, entity_id), it is
    updated in place. This is what keeps the index fresh after an edit.
    """
    existing = db.query(DocumentChunk).filter(
        DocumentChunk.user_id == user_id,
        DocumentChunk.entity_type == entity_type,
        DocumentChunk.entity_id == entity_id,
    ).first()

    embedding = get_embedding(text_content)
    embedding_json = json.dumps(embedding) if embedding else None

    if existing:
        existing.content = text_content
        existing.embedding = embedding_json
        existing.updated_at = datetime.now(timezone.utc)
    else:
        db.add(DocumentChunk(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            content=text_content,
            embedding=embedding_json,
        ))

    db.commit()


def ingest_all(db: Session, user) -> int:
    """
    Rebuild the entire search index for a user.

    Collects every chunk first, embeds them in batches (one API call per 100
    chunks instead of one call per entity), then replaces the user's rows in a
    single pass. Returns the number of chunks indexed.
    """
    from app.models.assignment import Assignment
    from app.models.job import JobApplication
    from app.models.expense import Expense
    from app.models.workout import Workout

    # 1. Collect (entity_type, entity_id, text) tuples.
    items: list[tuple[str, object, str]] = []

    assignments = db.query(Assignment).filter(
        Assignment.user_id == user.id,
        Assignment.deleted_at.is_(None),
    ).all()
    items += [("assignment", a.id, chunk_assignment(a)) for a in assignments]

    jobs = db.query(JobApplication).filter(JobApplication.user_id == user.id).all()
    items += [("job", j.id, chunk_job(j)) for j in jobs]

    expenses = db.query(Expense).filter(Expense.user_id == user.id).all()
    items += [("expense", e.id, chunk_expense(e)) for e in expenses]

    workouts = db.query(Workout).filter(Workout.user_id == user.id).all()
    items += [("workout", w.id, chunk_workout(w)) for w in workouts]

    # 2. Embed in batches. OpenAI accepts up to 2048 inputs per request;
    #    100 keeps payloads small and failures cheap.
    vectors: list[list[float]] = []
    batch_size = 100
    for start in range(0, len(items), batch_size):
        batch = items[start:start + batch_size]
        batch_vectors = get_embeddings_batch([item[2] for item in batch])

        # Defensive: a failed batch may return [] or the wrong length.
        if len(batch_vectors) != len(batch):
            batch_vectors = [[] for _ in batch]

        vectors.extend(batch_vectors)

    # 3. Replace the user's index. Delete-then-insert keeps the rebuild atomic
    #    from the application's point of view: no stale duplicates survive.
    db.query(DocumentChunk).filter(DocumentChunk.user_id == user.id).delete()
    db.flush()

    for (entity_type, entity_id, content), vector in zip(items, vectors):
        db.add(DocumentChunk(
            user_id=user.id,
            entity_type=entity_type,
            entity_id=entity_id,
            content=content,
            embedding=json.dumps(vector) if vector else None,
        ))

    db.commit()
    return len(items)


# ---------------------------------------------------------------------------
# Search — vector + keyword, fused with Reciprocal Rank Fusion
# ---------------------------------------------------------------------------

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity in [-1, 1]. Returns 0.0 for unusable vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _vector_search(
    db: Session,
    user_id,
    query_embedding: list[float],
    entity_types: Optional[list[str]],
    candidate_limit: int,
) -> list[tuple[DocumentChunk, float]]:
    """
    Rank the user's chunks by cosine similarity to the query embedding.

    Embeddings are stored as JSON text (portable across SQLite and Postgres),
    so similarity is computed in Python. For a personal index of hundreds of
    chunks this is microseconds; pgvector would be the next step at scale.
    """
    query = db.query(DocumentChunk).filter(
        DocumentChunk.user_id == user_id,
        DocumentChunk.embedding.isnot(None),
    )
    if entity_types:
        query = query.filter(DocumentChunk.entity_type.in_(entity_types))

    scored: list[tuple[DocumentChunk, float]] = []
    for chunk in query.limit(1000).all():
        try:
            vector = json.loads(chunk.embedding)
        except (TypeError, ValueError):
            continue
        scored.append((chunk, _cosine_similarity(query_embedding, vector)))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:candidate_limit]


def _keyword_search_fallback(
    db: Session,
    user_id,
    query_text: str,
    entity_types: Optional[list[str]],
    candidate_limit: int,
) -> list[tuple[DocumentChunk, float]]:
    """
    Naive keyword scoring for databases without tsvector (SQLite in tests).

    Scores by the fraction of query terms present in the chunk. This exists so
    the same code path is exercised in tests; production uses PostgreSQL FTS.
    """
    terms = [t for t in re.findall(r"[a-z0-9]+", query_text.lower()) if len(t) > 1]
    if not terms:
        return []

    query = db.query(DocumentChunk).filter(DocumentChunk.user_id == user_id)
    if entity_types:
        query = query.filter(DocumentChunk.entity_type.in_(entity_types))

    scored: list[tuple[DocumentChunk, float]] = []
    for chunk in query.limit(1000).all():
        haystack = chunk.content.lower()
        matches = sum(1 for term in terms if term in haystack)
        if matches:
            scored.append((chunk, matches / len(terms)))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:candidate_limit]


def _keyword_search(
    db: Session,
    user_id,
    query_text: str,
    entity_types: Optional[list[str]],
    candidate_limit: int,
) -> list[tuple[DocumentChunk, float]]:
    """
    Rank chunks with PostgreSQL full-text search (ts_rank_cd).

    `plainto_tsquery` treats the input as plain text, so arbitrary user input
    (quotes, punctuation, operators) can never produce a syntax error.
    """
    if db.get_bind().dialect.name != "postgresql":
        return _keyword_search_fallback(db, user_id, query_text, entity_types, candidate_limit)

    sql = (
        "select id, ts_rank_cd(search_vector, plainto_tsquery('english', :q)) as rank "
        "from document_chunks "
        "where user_id = :uid "
        "and search_vector @@ plainto_tsquery('english', :q)"
    )
    params = {"q": query_text, "uid": user_id, "lim": candidate_limit}

    if entity_types:
        sql += " and entity_type in :types"
        params["types"] = entity_types

    sql += " order by rank desc limit :lim"

    statement = text(sql)
    if entity_types:
        statement = statement.bindparams(bindparam("types", expanding=True))

    rows = db.execute(statement, params).fetchall()
    if not rows:
        return []

    ids = [row[0] for row in rows]
    chunks = {
        chunk.id: chunk
        for chunk in db.query(DocumentChunk).filter(DocumentChunk.id.in_(ids)).all()
    }

    return [(chunks[row[0]], float(row[1])) for row in rows if row[0] in chunks]


def hybrid_search(
    db: Session,
    user_id,
    query_text: str,
    limit: int = 8,
    candidate_limit: int = 20,
    entity_types: Optional[list[str]] = None,
    rrf_k: int = 60,
) -> list[dict]:
    """
    Retrieve the most relevant chunks for a query.

    Args:
        db: Database session.
        user_id: Owner of the index (tenant isolation).
        query_text: Natural-language query, e.g. "what is due this week".
        limit: Number of chunks to return.
        candidate_limit: How many results each search method contributes.
        entity_types: Optional filter, e.g. ["assignment", "job"].
        rrf_k: RRF constant; 60 is the standard value from the literature.

    Returns:
        Ranked list of dicts with content, source attribution, and scores.
        Empty list if the index is empty or every search path fails.
    """
    # Vector search needs an embedding of the query. If OpenAI is unavailable,
    # degrade to keyword-only instead of failing the whole request.
    query_embedding = get_embedding(query_text)
    vector_results = (
        _vector_search(db, user_id, query_embedding, entity_types, candidate_limit)
        if query_embedding else []
    )
    keyword_results = _keyword_search(
        db, user_id, query_text, entity_types, candidate_limit
    )

    if not vector_results and not keyword_results:
        return []

    # Reciprocal Rank Fusion — merge ranked lists without score normalization.
    rrf_scores: dict = {}
    chunks_by_id: dict = {}
    vector_scores: dict = {}
    keyword_scores: dict = {}

    for rank, (chunk, score) in enumerate(vector_results, start=1):
        rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + 1.0 / (rrf_k + rank)
        chunks_by_id[chunk.id] = chunk
        vector_scores[chunk.id] = score

    for rank, (chunk, score) in enumerate(keyword_results, start=1):
        rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + 1.0 / (rrf_k + rank)
        chunks_by_id[chunk.id] = chunk
        keyword_scores[chunk.id] = score

    ranked = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)[:limit]

    return [
        {
            "id": str(chunk_id),
            "entity_type": chunks_by_id[chunk_id].entity_type,
            "entity_id": str(chunks_by_id[chunk_id].entity_id),
            "content": chunks_by_id[chunk_id].content,
            "score": round(score, 6),
            "vector_score": (
                round(vector_scores[chunk_id], 4)
                if chunk_id in vector_scores else None
            ),
            "keyword_score": (
                round(keyword_scores[chunk_id], 4)
                if chunk_id in keyword_scores else None
            ),
        }
        for chunk_id, score in ranked
    ]
