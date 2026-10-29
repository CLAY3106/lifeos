"""add tsvector to document_chunks for bm25

Adds a generated tsvector column and a GIN index to document_chunks so
PostgreSQL can run fast full-text (BM25-style) keyword search alongside
vector similarity search.

The column is generated and stored by PostgreSQL:

    search_vector = to_tsvector('english', content)

Why a generated column?
- It is always in sync with `content` — no application code can forget to update it.
- It is computed once at write time, not on every search.
- The GIN index makes keyword lookups logarithmic instead of a table scan.

Why is this column NOT declared on the SQLAlchemy model?
- Tests run on SQLite, which has no `tsvector` type. Keeping the column
  unmapped lets `Base.metadata.create_all()` work on SQLite while the real
  Postgres schema gets the column through this migration.
- Search code queries it with raw SQL only when the dialect is PostgreSQL.

Revision ID: d61103f54e33
Revises: 551d6d6eb928
Create Date: 2026-10-29 21:08:00.000039

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd61103f54e33'
down_revision: Union[str, Sequence[str], None] = '551d6d6eb928'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add generated tsvector column + GIN index (PostgreSQL only)."""
    bind = op.get_bind()

    # SQLite (used by the test suite) has no tsvector type. Skip gracefully so
    # migrations remain runnable in any environment.
    if bind.dialect.name != "postgresql":
        return

    # Generated + STORED: PostgreSQL computes and persists the vector whenever
    # `content` changes. The two-argument to_tsvector form with a constant
    # config ('english') is immutable, which generated columns require.
    op.execute(
        """
        ALTER TABLE document_chunks
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (to_tsvector('english', content)) STORED
        """
    )

    # GIN is the index type designed for full-text search vectors.
    op.execute(
        """
        CREATE INDEX ix_document_chunks_search_vector
        ON document_chunks
        USING GIN (search_vector)
        """
    )


def downgrade() -> None:
    """Remove the GIN index and generated column (PostgreSQL only)."""
    bind = op.get_bind()

    if bind.dialect.name != "postgresql":
        return

    op.execute("DROP INDEX IF EXISTS ix_document_chunks_search_vector")
    op.execute("ALTER TABLE document_chunks DROP COLUMN IF EXISTS search_vector")
