"""
RAG Router — Retrieval-Augmented Generation Endpoints

Provides endpoints for:
1. POST /rag/ingest  — Rebuild the search index for the logged-in user
2. POST /rag/search  — Hybrid (vector + keyword) search over that index
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.rag import RagSearchRequest, RagSearchResult
from app.services.rag import hybrid_search, ingest_all

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/ingest")
def ingest(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Rebuild the RAG search index for the logged-in user.

    Re-chunks and re-embeds all assignments, jobs, expenses, and workouts,
    replacing any existing index rows for this user.

    Returns the number of chunks indexed.
    """
    count = ingest_all(db, current_user)
    return {"status": "ok", "chunks_indexed": count}


@router.post("/search", response_model=list[RagSearchResult])
def search(
    payload: RagSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search the user's index with hybrid retrieval.

    Runs vector (semantic) and keyword (BM25-style) search in parallel, then
    fuses the ranked lists with Reciprocal Rank Fusion. Always scoped to the
    authenticated user.
    """
    return hybrid_search(
        db,
        current_user.id,
        payload.query,
        limit=payload.limit,
        entity_types=payload.entity_types,
    )
