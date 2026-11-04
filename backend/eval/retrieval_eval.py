"""
Retrieval eval for the LifeOS RAG pipeline.

Loads a fixed, labeled dataset (eval/dataset.py) into a throwaway user, builds
the index with the real ingestion code, then scores three retrievers on the
same queries:

    vector   cosine similarity over embeddings only
    keyword  PostgreSQL ts_rank_cd (or the SQLite fallback) only
    hybrid   both, fused with Reciprocal Rank Fusion (what production uses)

Metrics (all at k, default 5):
    recall@k  share of the relevant items that appear in the top k
    MRR@k     1 / rank of the first relevant item (0 if none in the top k)
    hit@1     the top result is relevant

Usage (from backend/):
    # Real numbers: real embeddings + PostgreSQL full-text search
    DATABASE_URL=postgresql+psycopg://... OPENAI_API_KEY=sk-... \\
        python -m eval.retrieval_eval

    # Offline smoke run: fake hashed bag-of-words embedder, no API key
    python -m eval.retrieval_eval --embedder fake

Run it against a local or scratch database. It creates one user, inserts the
dataset, and deletes everything it created when it finishes.
"""

import argparse
import json
import os
import statistics
import sys
import time
import uuid
from pathlib import Path

# The auth module refuses to import without a secret. The eval never issues
# tokens, so a placeholder is safe here.
os.environ.setdefault("JWT_SECRET", "eval-only-not-a-real-secret")

from app.database import SessionLocal, engine
import app.models.routine  # noqa: F401  (registers the table workouts.routine_id points at)
from app.models.assignment import Assignment, AssignmentStatus
from app.models.document_chunk import DocumentChunk
from app.models.expense import BudgetGroup, Expense, ExpenseCategory
from app.models.job import JobApplication, JobStatus
from app.models.user import User
from app.models.workout import Workout
from app.services import rag
from app.services.auth import hash_password
from eval.dataset import ASSIGNMENTS, EXPENSES, JOBS, QUERIES, WORKOUTS

RESULTS_DIR = Path(__file__).parent / "results"


# ---------------------------------------------------------------------------
# Embedders
# ---------------------------------------------------------------------------

def _fake_embed(text: str) -> list[float]:
    import hashlib
    import math
    import re

    vec = [0.0] * 256
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        vec[int(hashlib.md5(token.encode()).hexdigest(), 16) % 256] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def install_embedder(kind: str) -> dict:
    """
    Patch rag's embedding functions and count API usage.

    Query embeddings are cached so vector-only and hybrid see the exact same
    query vector (and the API is called once per query, not twice).
    """
    stats = {"calls": 0, "texts": 0, "chars": 0}

    if kind == "fake":
        single, batch = _fake_embed, lambda texts: [_fake_embed(t) for t in texts]
    else:
        from app.services.embedding import get_embedding, get_embeddings_batch
        single, batch = get_embedding, get_embeddings_batch

    cache: dict[str, list[float]] = {}

    def counted_single(text: str) -> list[float]:
        if text not in cache:
            stats["calls"] += 1
            stats["texts"] += 1
            stats["chars"] += len(text)
            cache[text] = single(text)
        return cache[text]

    def counted_batch(texts: list[str]) -> list[list[float]]:
        stats["calls"] += 1
        stats["texts"] += len(texts)
        stats["chars"] += sum(len(t) for t in texts)
        return batch(texts)

    rag.get_embedding = counted_single
    rag.get_embeddings_batch = counted_batch
    return stats


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

def load_dataset(db, user) -> dict:
    """Insert the dataset for `user`. Returns {entity_id: dataset_key}."""
    key_by_id = {}

    def add(key, obj):
        obj.id = uuid.uuid4()
        db.add(obj)
        key_by_id[obj.id] = key

    for key, a in ASSIGNMENTS.items():
        add(key, Assignment(user_id=user.id, title=a["title"], course=a["course"],
                            due_date=a["due"], estimated_hours=a["hours"],
                            status=AssignmentStatus(a["status"])))
    for key, j in JOBS.items():
        add(key, JobApplication(user_id=user.id, company=j["company"], role=j["role"],
                                applied_date=j["applied"], status=JobStatus(j["status"]),
                                location=j["location"], notes=j["notes"]))
    for key, e in EXPENSES.items():
        add(key, Expense(user_id=user.id, amount=e["amount"], category=ExpenseCategory(e["category"]),
                         note=e["note"], spent_at=e["spent"], group_override=BudgetGroup(e["group"])))
    for key, w in WORKOUTS.items():
        add(key, Workout(user_id=user.id, type=w["type"], duration_mins=w["mins"], notes=w["notes"]))

    db.commit()
    return key_by_id


def validate_dataset():
    keys = set(ASSIGNMENTS) | set(JOBS) | set(EXPENSES) | set(WORKOUTS)
    for q in QUERIES:
        missing = set(q["relevant"]) - keys
        if missing:
            sys.exit(f"Query {q['q']!r} references unknown keys: {missing}")


# ---------------------------------------------------------------------------
# Retrievers and metrics
# ---------------------------------------------------------------------------

def retrieve(db, user_id, mode: str, query: str, k: int) -> list:
    """Return the top-k entity_ids for one retriever."""
    if mode == "vector":
        emb = rag.get_embedding(query)
        pairs = rag._vector_search(db, user_id, emb, None, k) if emb else []
        return [chunk.entity_id for chunk, _ in pairs]
    if mode == "keyword":
        pairs = rag._keyword_search(db, user_id, query, None, k)
        return [chunk.entity_id for chunk, _ in pairs]
    results = rag.hybrid_search(db, user_id, query, limit=k)
    return [uuid.UUID(r["entity_id"]) for r in results]


def score(ranked_keys: list[str], relevant: list[str], k: int) -> dict:
    top = ranked_keys[:k]
    rel = set(relevant)
    first = next((i for i, key in enumerate(top, start=1) if key in rel), None)
    return {
        "recall": len(rel & set(top)) / len(rel),
        "mrr": 1.0 / first if first else 0.0,
        "hit1": 1.0 if top and top[0] in rel else 0.0,
    }


def summarize(rows: list[dict]) -> dict:
    return {m: round(statistics.mean(r[m] for r in rows), 3) for m in ("recall", "mrr", "hit1")}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

MODES = ("vector", "keyword", "hybrid")
TYPES = ("lexical", "semantic", "mixed")


def run(embedder: str, k: int) -> dict:
    validate_dataset()
    stats = install_embedder(embedder)
    dialect = engine.dialect.name

    db = SessionLocal()
    user = User(id=uuid.uuid4(), email=f"eval-{uuid.uuid4().hex[:8]}@lifeos.eval",
                hashed_password=hash_password("eval-only"), name="Eval",
                monthly_budget=800, weekly_capacity_hours=40)
    db.add(user)
    db.commit()

    try:
        key_by_id = load_dataset(db, user)

        t0 = time.perf_counter()
        n_chunks = rag.ingest_all(db, user)
        ingest_s = time.perf_counter() - t0

        per_query = []
        latencies = {m: [] for m in MODES}
        for q in QUERIES:
            row = {"query": q["q"], "type": q["type"], "relevant": q["relevant"]}
            for mode in MODES:
                t = time.perf_counter()
                ids = retrieve(db, user.id, mode, q["q"], k)
                latencies[mode].append((time.perf_counter() - t) * 1000)
                keys = [key_by_id.get(i, "?") for i in ids]
                row[mode] = {"top": keys, **score(keys, q["relevant"], k)}
            per_query.append(row)
    finally:
        db.rollback()
        db.query(DocumentChunk).filter(DocumentChunk.user_id == user.id).delete()
        for model in (Assignment, JobApplication, Expense, Workout):
            db.query(model).filter(model.user_id == user.id).delete()
        db.query(User).filter(User.id == user.id).delete()
        db.commit()
        db.close()

    summary = {
        mode: {
            "all": summarize([r[mode] for r in per_query]),
            **{t: summarize([r[mode] for r in per_query if r["type"] == t]) for t in TYPES},
            "p50_ms": round(statistics.median(latencies[mode]), 1),
        }
        for mode in MODES
    }

    return {
        "config": {"embedder": embedder, "database": dialect, "k": k,
                   "queries": len(QUERIES), "chunks": n_chunks,
                   "ingest_seconds": round(ingest_s, 2)},
        "embedding_usage": stats,
        "summary": summary,
        "per_query": per_query,
    }


def to_markdown(result: dict) -> str:
    c, s, k = result["config"], result["summary"], result["config"]["k"]
    lines = [
        f"# Retrieval eval: {c['embedder']} embeddings, {c['database']}",
        "",
        f"{c['queries']} labeled queries over {c['chunks']} chunks. k = {k}.",
        "",
        f"| Retriever | Recall@{k} | MRR@{k} | Hit@1 | p50 latency |",
        "|---|---|---|---|---|",
    ]
    for mode in MODES:
        a = s[mode]["all"]
        lines.append(f"| {mode} | {a['recall']:.3f} | {a['mrr']:.3f} | {a['hit1']:.3f} | {s[mode]['p50_ms']} ms |")

    lines += ["", f"## Recall@{k} by query type", "",
              "| Retriever | " + " | ".join(TYPES) + " |",
              "|---|" + "---|" * len(TYPES)]
    for mode in MODES:
        lines.append(f"| {mode} | " + " | ".join(f"{s[mode][t]['recall']:.3f}" for t in TYPES) + " |")

    misses = [r for r in result["per_query"] if r["hybrid"]["recall"] < 1.0]
    lines += ["", f"## Hybrid misses ({len(misses)} of {c['queries']} queries)", ""]
    if misses:
        lines += ["| Query | Type | Expected | Hybrid top results |", "|---|---|---|---|"]
        for r in misses:
            lines.append(f"| {r['query']} | {r['type']} | {', '.join(r['relevant'])} | {', '.join(r['hybrid']['top'])} |")
    else:
        lines.append("None.")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--embedder", choices=["openai", "fake"], default="openai")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--no-save", action="store_true", help="print only, don't write results/")
    args = parser.parse_args()

    result = run(args.embedder, args.k)
    md = to_markdown(result)
    print(md)

    if not args.no_save:
        RESULTS_DIR.mkdir(exist_ok=True)
        name = f"{args.embedder}_{result['config']['database']}"
        (RESULTS_DIR / f"{name}.json").write_text(json.dumps(result, indent=2, default=str))
        (RESULTS_DIR / f"{name}.md").write_text(md)
        print(f"Saved to {RESULTS_DIR}/{name}.md and .json")


if __name__ == "__main__":
    main()
