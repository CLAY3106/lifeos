"""add experiments tables for ab testing

Creates the storage for deterministic A/B tests:

- experiments          configuration (key, variants, primary metric, status)
- experiment_exposures one row per user per experiment (idempotent denominator)
- experiment_events    immutable conversion events (numerator source)

The unique constraint on (experiment_id, user_id) is the core idempotency
guarantee: reloading a page must not inflate an experiment's exposure count.

Revision ID: f2a4c6d8e0b1
Revises: d61103f54e33
Create Date: 2026-11-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f2a4c6d8e0b1'
down_revision: Union[str, Sequence[str], None] = 'd61103f54e33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

experiment_status = sa.Enum(
    'draft', 'running', 'paused', 'completed', name='experimentstatus'
)


def upgrade() -> None:
    """Create experiment configuration, exposures, and events."""
    op.create_table(
        'experiments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'status',
            experiment_status,
            nullable=False,
            server_default='draft',
        ),
        sa.Column('variants', sa.JSON(), nullable=False),
        sa.Column('primary_metric', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_experiments_key', 'experiments', ['key'], unique=True
    )

    op.create_table(
        'experiment_exposures',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'experiment_id', postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('variant', sa.String(), nullable=False),
        sa.Column('first_exposed_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ['experiment_id'], ['experiments.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'experiment_id',
            'user_id',
            name='uq_experiment_exposure_user',
        ),
    )
    op.create_index(
        'ix_experiment_exposures_experiment_id',
        'experiment_exposures',
        ['experiment_id'],
    )
    op.create_index(
        'ix_experiment_exposures_user_id',
        'experiment_exposures',
        ['user_id'],
    )

    op.create_table(
        'experiment_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'experiment_id', postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('variant', sa.String(), nullable=False),
        sa.Column('event_name', sa.String(), nullable=False),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('event_metadata', sa.JSON(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ['experiment_id'], ['experiments.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_experiment_events_experiment_id',
        'experiment_events',
        ['experiment_id'],
    )
    op.create_index(
        'ix_experiment_events_user_id',
        'experiment_events',
        ['user_id'],
    )
    op.create_index(
        'ix_experiment_events_experiment_metric',
        'experiment_events',
        ['experiment_id', 'event_name'],
    )


def downgrade() -> None:
    """Drop events, exposures, experiments, and the status enum."""
    op.drop_index(
        'ix_experiment_events_experiment_metric',
        table_name='experiment_events',
    )
    op.drop_index(
        'ix_experiment_events_user_id', table_name='experiment_events'
    )
    op.drop_index(
        'ix_experiment_events_experiment_id', table_name='experiment_events'
    )
    op.drop_table('experiment_events')

    op.drop_index(
        'ix_experiment_exposures_user_id',
        table_name='experiment_exposures',
    )
    op.drop_index(
        'ix_experiment_exposures_experiment_id',
        table_name='experiment_exposures',
    )
    op.drop_table('experiment_exposures')

    op.drop_index('ix_experiments_key', table_name='experiments')
    op.drop_table('experiments')

    experiment_status.drop(op.get_bind(), checkfirst=True)
