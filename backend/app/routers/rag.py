"""
RAG Router — Retrieval-Augmented Generation Endpoints

Provides endpoints for:
1. /rag/ingest  — Rebuild the search index for the logged-in user
2. /rag/search  — Query the search index (vector + keyword hybrid)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.document_chunk import DocumentChunk
from app.services.rag import ingest_all

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/ingest")
def ingest(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rebuild the RAG search index for the logged-in user.

    Clears all existing chunks for this user, then re-chunks and
    re-embeds all assignments, jobs, expenses, and workouts.

    Returns the number of chunks indexed.
    """
    ingest_all(db, current_user)

    count = db.query(DocumentChunk).filter(
        DocumentChunk.user_id == current_user.id
    ).count()

    return {"status": "ok", "chunks_indexed": count}
