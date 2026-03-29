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

class JobUpdate(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    status: Optional[JobStatus] = None
    followup_date: Optional[date] = None
    notes: Optional[str] = None

class JobResponse(BaseModel):
    id: UUID
    user_id: UUID
    company: str
    role: str
    applied_date: date
    status: JobStatus
    followup_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True