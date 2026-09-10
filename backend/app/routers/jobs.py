"""
Jobs Router — CRUD, Status Updates, and Event Sourcing

Endpoints:
- POST /jobs — Create a new job application
- GET /jobs — List all job applications
- GET /jobs/:id — Get a specific job application
- GET /jobs/:id/history — Get status change history (event sourcing)
- PATCH /jobs/:id — Update a job application
- DELETE /jobs/:id — Delete a job application

The history endpoint powers the frontend timeline view and
provides the "event sourcing" feature for the thesis.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.job import JobApplication, JobStatusHistory
from app.schemas.job import JobCreate, JobUpdate, JobResponse, JobStatusHistoryResponse
from app.dependencies import get_current_user
from app.models.user import User
from app.services import jobs_service
from typing import List
import uuid

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse)
def create_job(
    data: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new job application. Follow-up date is auto-set to 7 days after application."""
    return jobs_service.create_job(db, current_user, data)


@router.get("", response_model=List[JobResponse])
def get_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all job applications for the current user, ordered by application date (newest first)."""
    return db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id
    ).order_by(JobApplication.applied_date.desc()).all()


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific job application by ID."""
    try:
        return jobs_service.get_job(db, current_user, job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{job_id}/history", response_model=List[JobStatusHistoryResponse])
def get_job_history(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get status change history for a job application (event sourcing).
    
    Returns all status changes ordered by timestamp, allowing you to:
    - Reconstruct the full timeline of the application
    - Calculate time-in-stage metrics
    - Display a visual timeline in the frontend
    """
    history = db.query(JobStatusHistory).filter(
        JobStatusHistory.job_id == job_id,
        JobStatusHistory.user_id == current_user.id
    ).order_by(JobStatusHistory.changed_at).all()
    return history


@router.patch("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: uuid.UUID,
    data: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a job application's general fields (not status)."""
    try:
        return jobs_service.update_job(db, current_user, job_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{job_id}")
def delete_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a job application by ID."""
    job = db.query(JobApplication).filter(
        JobApplication.id == job_id,
        JobApplication.user_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job application not found")
    
    db.delete(job)
    db.commit()
    return {"message": "Job application deleted"}
