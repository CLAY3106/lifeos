import uuid
from datetime import timedelta
from sqlalchemy.orm import Session
from app.models.job import JobApplication, JobStatus
from app.models.user import User
from app.schemas.job import JobCreate, JobUpdate


def create_job(db: Session, user: User, data: JobCreate) -> JobApplication:
    job = JobApplication(
        id=uuid.uuid4(),
        user_id=user.id,
        company=data.company,
        role=data.role,
        applied_date=data.applied_date,
        followup_date=data.applied_date + timedelta(days=7),
        notes=data.notes,
        location=data.location,
        job_description=data.job_description,
        application_url=data.application_url,
        deadline=data.deadline
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, user: User, job_id: uuid.UUID) -> JobApplication:
    job = db.query(JobApplication).filter(
        JobApplication.id == job_id,
        JobApplication.user_id == user.id
    ).first()
    if not job:
        raise ValueError("Job application not found")
    return job


def update_job(db: Session, user: User, job_id: uuid.UUID, data: JobUpdate) -> JobApplication:
    job = get_job(db, user, job_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)
    return job


def update_job_status(db: Session, user: User, job_id: uuid.UUID, status: JobStatus) -> JobApplication:
    job = get_job(db, user, job_id)
    job.status = status
    db.commit()
    db.refresh(job)
    return job
