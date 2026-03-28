from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.job import JobApplication
from app.schemas.job import JobCreate, JobUpdate, JobResponse
from app.dependencies import get_current_user
from app.models.user import User
from typing import List
from datetime import timedelta
import uuid

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("", response_model=JobResponse)
def create_job(
    data: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = JobApplication(
        id=uuid.uuid4(),
        user_id=current_user.id,
        company=data.company,
        role=data.role,
        applied_date=data.applied_date,
        followup_date=data.applied_date + timedelta(days=7),
        notes=data.notes
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.get("", response_model=List[JobResponse])
def get_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id
    ).order_by(JobApplication.applied_date.desc()).all()

@router.patch("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: uuid.UUID,
    data: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(JobApplication).filter(
        JobApplication.id == job_id,
        JobApplication.user_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job application not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(job, field, value)
    
    db.commit()
    db.refresh(job)
    return job

@router.delete("/{job_id}")
def delete_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(JobApplication).filter(
        JobApplication.id == job_id,
        JobApplication.user_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job application not found")
    
    db.delete(job)
    db.commit()
    return {"message": "Job application deleted"}