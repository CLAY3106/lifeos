import uuid
from sqlalchemy import Column, String, Date, Text, Enum
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