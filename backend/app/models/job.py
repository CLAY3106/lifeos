import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Date, Text, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from app.database import Base
from app.models.base import TimestampMixin
import enum

class JobStatus(enum.Enum):
    applied = "applied"
    oa = "oa"
    interview_scheduled = "interview_scheduled"
    offer = "offer"
    rejected = "rejected"
    dropped = "dropped"

# Valid transitions: which statuses can transition to which
# The pipeline is linear: applied -> oa -> interview -> offer
# You can drop out at any stage. Rejected and dropped are terminal.
VALID_TRANSITIONS: dict[JobStatus, list[JobStatus]] = {
    JobStatus.applied: [JobStatus.oa, JobStatus.rejected, JobStatus.dropped],
    JobStatus.oa: [JobStatus.interview_scheduled, JobStatus.rejected, JobStatus.dropped],
    JobStatus.interview_scheduled: [JobStatus.offer, JobStatus.rejected, JobStatus.dropped],
    JobStatus.offer: [JobStatus.rejected, JobStatus.dropped],
    JobStatus.rejected: [],  # terminal
    JobStatus.dropped: [],   # terminal
}

class JobApplication(Base, TimestampMixin):
    __tablename__ = "job_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)
    applied_date = Column(Date, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.applied)
    followup_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    job_description = Column(Text, nullable=True)
    application_url = Column(String, nullable=True)
    deadline = Column(Date, nullable=True)

class JobStatusHistory(Base):
    __tablename__ = "job_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("job_applications.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    from_status = Column(Enum(JobStatus), nullable=False)
    to_status = Column(Enum(JobStatus), nullable=False)
    changed_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))