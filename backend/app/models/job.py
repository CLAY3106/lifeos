"""
Job Models — Application Tracking and Event Sourcing

This module defines the data models for job application tracking:
1. JobStatus — Enum of possible application statuses
2. VALID_TRANSITIONS — State machine definition for status changes
3. JobApplication — Main model for job applications
4. JobStatusHistory — Event sourcing table for status changes

The state machine is linear:
applied → oa → interview_scheduled → offer

You can drop out at any stage (→ rejected or → dropped).
Rejected and dropped are terminal (no outgoing transitions).

This is what you tell interviewers: "state machine with event sourcing."
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Date, Text, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from app.database import Base
from app.models.base import TimestampMixin
import enum


class JobStatus(enum.Enum):
    """
    Possible statuses for a job application.
    
    The pipeline is:
    1. applied — You submitted the application
    2. oa — Online assessment (coding test, take-home, etc.)
    3. interview_scheduled — You have an interview booked
    4. offer — You received an offer
    
    Terminal states (no outgoing transitions):
    - rejected — You were rejected (or rejected an offer)
    - dropped — You withdrew from the process
    """
    applied = "applied"
    oa = "oa"
    interview_scheduled = "interview_scheduled"
    offer = "offer"
    rejected = "rejected"
    dropped = "dropped"


# Valid transitions: which statuses can transition to which
# This is the state machine definition — the core of event sourcing
VALID_TRANSITIONS: dict[JobStatus, list[JobStatus]] = {
    JobStatus.applied: [JobStatus.oa, JobStatus.rejected, JobStatus.dropped],
    JobStatus.oa: [JobStatus.interview_scheduled, JobStatus.rejected, JobStatus.dropped],
    JobStatus.interview_scheduled: [JobStatus.offer, JobStatus.rejected, JobStatus.dropped],
    JobStatus.offer: [JobStatus.rejected, JobStatus.dropped],
    JobStatus.rejected: [],  # terminal — no outgoing transitions
    JobStatus.dropped: [],   # terminal — no outgoing transitions
}


class JobApplication(Base, TimestampMixin):
    """
    Main model for job applications.
    
    Each row represents one job application with:
    - Company and role info
    - Application date and current status
    - Follow-up date for career tracking
    - Optional notes, location, job description, and application URL
    """
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
    """
    Event sourcing table — records every status change.
    
    This is the "event sourcing" part of the thesis. Instead of just storing
    the current status, we store the history of all changes. This allows us to:
    
    1. Reconstruct the full timeline of a job application
    2. Calculate time-in-stage metrics
    3. Answer questions like "How long did this candidate spend in each stage?"
    
    Each row represents one status change:
    - from_status: The previous status
    - to_status: The new status
    - changed_at: When the change happened
    
    Example:
    | job_id | from_status | to_status | changed_at |
    |--------|-------------|-----------|------------|
    | abc123 | applied     | oa        | Day 5      |
    | abc123 | oa          | interview | Day 10     |
    
    This gives you the full journey: applied → oa → interview
    """
    __tablename__ = "job_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("job_applications.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    from_status = Column(Enum(JobStatus), nullable=False)
    to_status = Column(Enum(JobStatus), nullable=False)
    changed_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
