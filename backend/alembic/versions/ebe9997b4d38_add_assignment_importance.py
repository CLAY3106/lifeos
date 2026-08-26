"""add assignment importance

Revision ID: ebe9997b4d38
Revises: c24bfb007a72
Create Date: 2026-08-26 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ebe9997b4d38'
down_revision: Union[str, Sequence[str], None] = 'c24bfb007a72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    importance_enum = sa.Enum('low', 'high', name='assignmentimportance')
    importance_enum.create(op.get_bind())
    op.add_column(
        'assignments',
        sa.Column('importance', importance_enum, nullable=False, server_default='low')
    )
    op.add_column(
        'assignments',
        sa.Column('importance_set_manually', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('assignments', 'importance_set_manually')
    op.drop_column('assignments', 'importance')
    op.execute("DROP TYPE assignmentimportance")
