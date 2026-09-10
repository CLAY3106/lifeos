from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime
from typing import Optional
from app.models.job import JobStatus

class JobCreate(BaseModel):
    company: str
    role: str
    applied_date: date
    notes: Optional[str] = None
    location: Optional[str] = None
    job_description: Optional[str] = None
    application_url: Optional[str] = None
    deadline: Optional[date] = None

class JobUpdate(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    status: Optional[JobStatus] = None
    followup_date: Optional[date] = None
    notes: Optional[str] = None
    location: Optional[str] = None
    job_description: Optional[str] = None
    application_url: Optional[str] = None
    deadline: Optional[date] = None

class JobResponse(BaseModel):
    id: UUID
    user_id: UUID
    company: str
    role: str
    applied_date: date
    status: JobStatus
    followup_date: Optional[date] = None
    notes: Optional[str] = None
    location: Optional[str] = None
    job_description: Optional[str] = None
    application_url: Optional[str] = None
    deadline: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class JobStatusHistoryResponse(BaseModel):
    id: UUID
    job_id: UUID
    user_id: UUID
    from_status: JobStatus
    to_status: JobStatus
    changed_at: datetime

    class Config:
        from_attributes = True