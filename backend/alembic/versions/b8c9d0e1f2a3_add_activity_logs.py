"""add activity_logs table

Revision ID: b8c9d0e1f2a3
Revises: f7a1b2c3d4e5
Create Date: 2026-09-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "b8c9d0e1f2a3"
down_revision = "f7a1b2c3d4e5"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "activity_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String, nullable=False),
        sa.Column("entity_type", sa.String, nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("details", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_activity_logs_user_id", "activity_logs", ["user_id"])
    op.create_index("ix_activity_logs_created_at", "activity_logs", ["created_at"])

def downgrade():
    op.drop_table("activity_logs")
