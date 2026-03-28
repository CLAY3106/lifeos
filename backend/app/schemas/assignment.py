from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.assignment import AssignmentStatus

class AssignmentCreate(BaseModel):
    title: str
    course: Optional[str] = None
    due_date: datetime
    estimated_hours: float = 1.0

class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    course: Optional[str] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    status: Optional[AssignmentStatus] = None

class AssignmentResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    course: Optional[str] = None
    due_date: datetime
    estimated_hours: float
    status: AssignmentStatus
    created_at: datetime

    class Config:
        from_attributes = True