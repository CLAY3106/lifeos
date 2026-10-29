"""
RAG Schemas — Request/Response Validation

Defines the API contract for retrieval endpoints:
1. RagSearchRequest: query text + optional filters
2. RagSearchResult: one retrieved chunk with source attribution and scores
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class RagSearchRequest(BaseModel):
    """Search query with optional result limit and entity filter."""

    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(default=8, ge=1, le=50)
    entity_types: Optional[List[str]] = None


class RagSearchResult(BaseModel):
    """A single retrieved chunk, traceable back to its source entity."""

    id: str
    entity_type: str
    entity_id: str
    content: str
    score: float
    vector_score: Optional[float] = None
    keyword_score: Optional[float] = None
