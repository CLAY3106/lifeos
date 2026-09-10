"""
Job Schemas — Pydantic Models for Request/Response Validation

This module defines the Pydantic schemas for job-related API endpoints:
1. JobCreate — Request body for creating a job application
2. JobUpdate — Request body for updating a job application
3. JobResponse — Response body for job application data
4. JobStatusHistoryResponse — Response body for status change history

These schemas handle:
- Input validation (required fields, optional fields)
- Output serialization (converting SQLAlchemy models to JSON)
- Type safety (ensuring correct types for all fields)
"""

from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime
from typing import Optional
from app.models.job import JobStatus


class JobCreate(BaseModel):
    """
    Request body for creating a job application.
    
    Required fields:
    - company: Company name
    - role: Job role/position
    - applied_date: When you applied
    
    Optional fields:
    - notes: Any notes about the application
    - location: Job location (remote, hybrid, on-site)
    - job_description: Full job description
    - application_url: Link to the application
    - deadline: Application deadline (if any)
    """
    company: str
    role: str
    applied_date: date
    notes: Optional[str] = None
    location: Optional[str] = None
    job_description: Optional[str] = None
    application_url: Optional[str] = None
    deadline: Optional[date] = None


class JobUpdate(BaseModel):
    """
    Request body for updating a job application.
    
    All fields are optional — only provided fields are updated.
    Status updates should use PATCH /jobs/:id/status instead.
    """
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
    """
    Response body for job application data.
    
    Includes all fields from the database, plus:
    - created_at: When the record was created
    - updated_at: When the record was last updated (nullable)
    """
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
        from_attributes = True  # Allows conversion from SQLAlchemy models


class JobStatusHistoryResponse(BaseModel):
    """
    Response body for status change history (event sourcing).
    
    Each entry represents one status change:
    - from_status: The previous status
    - to_status: The new status
    - changed_at: When the change happened
    
    This powers the frontend timeline view and provides
    the "event sourcing" feature for the thesis.
    """
    id: UUID
    job_id: UUID
    user_id: UUID
    from_status: JobStatus
    to_status: JobStatus
    changed_at: datetime

    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models
