"""
Document Chunk Model — RAG Search Index

This module defines the search index for Retrieval-Augmented Generation (RAG).
Each row represents one "chunk" of text extracted from a user's data that can
be retrieved when generating the AI briefing.

The table supports two search methods:
1. Vector search (semantic): Uses embeddings to find conceptually similar chunks
2. BM25 search (keyword): Uses full-text search to find exact keyword matches

Chunking strategy per entity type:
- Assignment: "Assignment: {title} for {course}, due {date}, {status}"
- Job: "Job Application: {role} at {company}, status: {status}"
- Expense: "Expense: ${amount} on {note}, {category}, {group}"
- Workout: "Workout: {type} for {duration}min, {notes}"

Each chunk tracks its source (entity_type + entity_id) for attribution
in the AI briefing response.
"""

import uuid
from sqlalchemy import Column, String, Text, Float, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy import ForeignKey, Computed
from app.database import Base
from app.models.base import TimestampMixin


class DocumentChunk(Base, TimestampMixin):
    """
    Search index chunk for RAG retrieval.

    Each row is one searchable text unit with:
    - content: The raw text (e.g., "Assignment: CS Final, due tomorrow")
    - entity_type: Where it came from (assignment, job, expense, workout)
    - entity_id: Which specific entity
    - user_id: Owner (for multi-user isolation)
    - embedding: Vector representation for semantic search (JSON text)
    - search_vector: Full-text search vector for BM25 keyword search

    The search_vector column is auto-maintained by PostgreSQL via a generated
    column expression. The embedding column is updated by the embedding pipeline
    on INSERT/UPDATE.

    For local development (SQLite), embeddings are stored as JSON text and
    cosine similarity is computed in Python. For production (Postgres with
    pgvector), the embedding column can be migrated to a vector type for
    SQL-level similarity queries.
    """
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    entity_type = Column(String, nullable=False, index=True)  # assignment, job, expense, workout
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    content = Column(Text, nullable=False)  # The text to search over
    embedding = Column(Text, nullable=True)  # JSON-serialized vector (e.g., "[0.1, 0.2, ...]")
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
