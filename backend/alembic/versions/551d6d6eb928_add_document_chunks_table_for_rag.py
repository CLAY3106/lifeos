"""add document_chunks table for rag

Revision ID: 551d6d6eb928
Revises: d0e1f2a3b4c5
Create Date: 2026-09-11 20:39:00.412921

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '551d6d6eb928'
down_revision: Union[str, Sequence[str], None] = 'd0e1f2a3b4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_document_chunks_user_id', 'document_chunks', ['user_id'])
    op.create_index('ix_document_chunks_entity_type', 'document_chunks', ['entity_type'])
    op.create_index('ix_document_chunks_entity_id', 'document_chunks', ['entity_id'])


def downgrade() -> None:
    op.drop_table('document_chunks')
