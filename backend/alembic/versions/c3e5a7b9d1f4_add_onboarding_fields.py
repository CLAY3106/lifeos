"""add onboarding_completed_at and active_modules to users

Adds two onboarding fields to the users table:

- onboarding_completed_at nullable timestamp, set when the user finishes
  the onboarding flow (NULL means the flow still needs to run).
- active_modules JSON list of enabled module keys, NOT NULL. Existing rows
  get the full default set via the server_default literal and a backfill
  UPDATE so no row is left NULL on either Postgres or SQLite.

sa.JSON is used instead of postgresql.JSONB so the migration stays portable
to the SQLite test database.

Revision ID: c3e5a7b9d1f4
Revises: f2a4c6d8e0b1
Create Date: 2026-11-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3e5a7b9d1f4'
down_revision: Union[str, Sequence[str], None] = 'f2a4c6d8e0b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Same value as app.models.user.DEFAULT_ACTIVE_MODULES. A plain string
# server_default renders identically on Postgres and SQLite.
DEFAULT_ACTIVE_MODULES = '["academics", "jobs", "fitness", "finance"]'


def upgrade() -> None:
    """Add onboarding_completed_at and active_modules to users."""
    op.add_column(
        'users',
        sa.Column(
            'onboarding_completed_at', sa.DateTime(), nullable=True
        ),
    )
    op.add_column(
        'users',
        sa.Column(
            'active_modules',
            sa.JSON(),
            nullable=False,
            server_default=DEFAULT_ACTIVE_MODULES,
        ),
    )

    # Backfill belt and braces: the NOT NULL plus server_default already
    # covers existing rows, but this keeps the data correct on databases
    # that apply defaults only to new inserts.
    op.execute(
        "UPDATE users SET active_modules = "
        "'[\"academics\", \"jobs\", \"fitness\", \"finance\"]' "
        "WHERE active_modules IS NULL"
    )


def downgrade() -> None:
    """Drop the onboarding columns from users."""
    op.drop_column('users', 'active_modules')
    op.drop_column('users', 'onboarding_completed_at')
