"""add expense group override

Revision ID: 7646349af3a2
Revises: 295741a7a85e
Create Date: 2026-08-26 00:00:03.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7646349af3a2'
down_revision: Union[str, Sequence[str], None] = '295741a7a85e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    budget_group_enum = sa.Enum('needs', 'wants', 'savings', name='budgetgroup')
    budget_group_enum.create(op.get_bind())
    op.add_column('expenses', sa.Column('group_override', budget_group_enum, nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('expenses', 'group_override')
    op.execute("DROP TYPE budgetgroup")
