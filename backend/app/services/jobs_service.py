"""
Jobs Service — CRUD, Status Updates, and Event Sourcing

This module handles job application management including:
1. Creating job applications with auto-set follow-up date
2. Reading job applications
3. Updating job applications (general fields)
4. Updating job status with event sourcing (records every change)

Key concepts:
- VALID_TRANSITIONS: State machine definition for status changes
- JobStatusHistory: Event sourcing table that records every status change
- Soft validation: Logs warning for invalid transitions but allows them anyway
"""

import uuid
import logging
from datetime import timedelta
from sqlalchemy.orm import Session
from app.models.job import JobApplication, JobStatus, JobStatusHistory, VALID_TRANSITIONS
from app.models.user import User
from app.schemas.job import JobCreate, JobUpdate
from app.services.activity_log_service import log_activity

logger = logging.getLogger(__name__)


def create_job(db: Session, user: User, data: JobCreate) -> JobApplication:
    """
    Create a new job application.
    
    Automatically sets follow-up date to 7 days after application date.
    This is a reasonable default for following up on applications.
    """
    job = JobApplication(
        id=uuid.uuid4(),
        user_id=user.id,
        company=data.company,
        role=data.role,
        applied_date=data.applied_date,
        followup_date=data.applied_date + timedelta(days=7),  # Auto-set follow-up
        notes=data.notes,
        location=data.location,
        job_description=data.job_description,
        application_url=data.application_url,
        deadline=data.deadline
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    log_activity(db, user.id, "Added job application", "job", job.id, f"{data.role} at {data.company}")
    return job


def get_job(db: Session, user: User, job_id: uuid.UUID) -> JobApplication:
    """
    Get a job application by ID.
    
    Raises ValueError if not found (converted to 404 by the router).
    """
    job = db.query(JobApplication).filter(
        JobApplication.id == job_id,
        JobApplication.user_id == user.id
    ).first()
    if not job:
        raise ValueError("Job application not found")
    return job


def update_job(db: Session, user: User, job_id: uuid.UUID, data: JobUpdate) -> JobApplication:
    """
    Update a job application's general fields (not status).
    
    Uses Pydantic's model_dump(exclude_unset=True) to only update
    fields that were actually provided in the request.
    """
    job = get_job(db, user, job_id)

    # Dynamically set only the fields that were provided
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)
    return job


def update_job_status(db: Session, user: User, job_id: uuid.UUID, status: JobStatus) -> JobApplication:
    """
    Update job status with event sourcing.
    
    This is the core of the state machine implementation:
    1. Get the current job and its status
    2. Soft-validate the transition (log warning if invalid, but allow it)
    3. Record the transition in JobStatusHistory (event sourcing)
    4. Update the job's status
    
    The soft validation means:
    - Valid transitions are allowed (e.g., applied → oa)
    - Invalid transitions are logged as warnings but still applied
    - This is a design choice: allow flexibility while tracking everything
    
    The event sourcing means:
    - Every status change creates a row in job_status_history
    - You can reconstruct the full timeline of the application
    - This powers analytics like "time-in-stage" metrics
    """
    job = get_job(db, user, job_id)
    old_status = job.status

    # Soft validation: log warning but allow update anyway
    # This is a design choice — allow flexibility while tracking everything
    if old_status != status and status not in VALID_TRANSITIONS.get(old_status, []):
        logger.warning(
            f"Invalid transition: {old_status.value} -> {status.value} for job {job_id}"
        )

    # Record the transition in event history (only if status actually changed)
    if old_status != status:
        history = JobStatusHistory(
            id=uuid.uuid4(),
            job_id=job.id,
            user_id=user.id,
            from_status=old_status,
            to_status=status,
        )
        db.add(history)

    # Update the job's current status
    job.status = status
    db.commit()
    db.refresh(job)
    log_activity(db, user.id, f"Updated job to {status.value}", "job", job.id)
    return job
