"""expand job status and job detail fields

Revision ID: c24bfb007a72
Revises: 16e3ee97bb5b
Create Date: 2026-08-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c24bfb007a72'
down_revision: Union[str, Sequence[str], None] = '16e3ee97bb5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('job_applications', 'status', type_=sa.String(), postgresql_using='status::text')
    op.execute("DROP TYPE jobstatus")
    new_jobstatus = sa.Enum('applied', 'oa', 'interview_scheduled', 'offer', 'rejected', 'dropped', name='jobstatus')
    new_jobstatus.create(op.get_bind())
    op.execute("UPDATE job_applications SET status = 'interview_scheduled' WHERE status = 'interview'")
    op.alter_column('job_applications', 'status', type_=new_jobstatus, postgresql_using='status::jobstatus')

    op.add_column('job_applications', sa.Column('location', sa.String(), nullable=True))
    op.add_column('job_applications', sa.Column('job_description', sa.Text(), nullable=True))
    op.add_column('job_applications', sa.Column('application_url', sa.String(), nullable=True))
    op.add_column('job_applications', sa.Column('deadline', sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('job_applications', 'deadline')
    op.drop_column('job_applications', 'application_url')
    op.drop_column('job_applications', 'job_description')
    op.drop_column('job_applications', 'location')

    op.alter_column('job_applications', 'status', type_=sa.String(), postgresql_using='status::text')
    op.execute("DROP TYPE jobstatus")
    op.execute("UPDATE job_applications SET status = 'interview' WHERE status = 'interview_scheduled'")
    op.execute("UPDATE job_applications SET status = 'rejected' WHERE status = 'dropped'")
    op.execute("UPDATE job_applications SET status = 'applied' WHERE status = 'oa'")
    old_jobstatus = sa.Enum('applied', 'interview', 'offer', 'rejected', name='jobstatus')
    old_jobstatus.create(op.get_bind())
    op.alter_column('job_applications', 'status', type_=old_jobstatus, postgresql_using='status::jobstatus')
