"""Add routine_id to workouts

Revision ID: f7a1b2c3d4e5
Revises: a98ff630f586
Create Date: 2026-09-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "f7a1b2c3d4e5"
down_revision = "a98ff630f586"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workouts",
        sa.Column("routine_id", UUID(as_uuid=True), sa.ForeignKey("routines.id", ondelete="SET NULL"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workouts", "routine_id")
