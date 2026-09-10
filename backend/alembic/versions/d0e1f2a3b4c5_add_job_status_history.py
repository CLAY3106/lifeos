"""add job_status_history

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-09-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'd0e1f2a3b4c5'
down_revision = 'c9d0e1f2a3b4'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'job_status_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_applications.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('from_status', sa.Enum('applied', 'oa', 'interview_scheduled', 'offer', 'rejected', 'dropped', name='jobstatus'), nullable=False),
        sa.Column('to_status', sa.Enum('applied', 'oa', 'interview_scheduled', 'offer', 'rejected', 'dropped', name='jobstatus'), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_job_status_history_job_id', 'job_status_history', ['job_id'])
    op.create_index('ix_job_status_history_user_id', 'job_status_history', ['user_id'])

def downgrade() -> None:
    op.drop_index('ix_job_status_history_user_id')
    op.drop_index('ix_job_status_history_job_id')
    op.drop_table('job_status_history')
