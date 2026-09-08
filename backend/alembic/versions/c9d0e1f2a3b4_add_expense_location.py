"""add location to expenses

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-09-04
"""
from alembic import op
import sqlalchemy as sa

revision = "c9d0e1f2a3b4"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("expenses", sa.Column("location", sa.String, nullable=True))

def downgrade():
    op.drop_column("expenses", "location")
