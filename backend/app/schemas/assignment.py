"""
Assignment Schemas — Request/Response Validation

This module defines Pydantic models for assignment operations:
1. AssignmentCreate: Create a new assignment
2. AssignmentUpdate: Update an existing assignment
3. AssignmentResponse: Return assignment data

These schemas validate incoming requests and serialize responses,
ensuring type safety and consistent API contracts.
"""

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.assignment import AssignmentStatus


class AssignmentCreate(BaseModel):
    """
    Schema for creating a new assignment.
    
    Required fields:
    - title: Assignment name
    - due_date: When it's due
    
    Optional fields:
    - course: Course name (e.g., "CS 101")
    - estimated_hours: Time estimate (default: 1.0)
    """
    title: str
    course: Optional[str] = None
    due_date: datetime
    estimated_hours: float = 1.0


class AssignmentUpdate(BaseModel):
    """
    Schema for updating an existing assignment.
    
    All fields are optional — only provided fields are updated.
    This allows partial updates (e.g., just changing status).
    """
    title: Optional[str] = None
    course: Optional[str] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    status: Optional[AssignmentStatus] = None


class AssignmentResponse(BaseModel):
    """
    Schema for returning assignment data.
    
    Includes:
    - All assignment fields
    - id: Assignment UUID
    - user_id: Owner UUID
    - created_at: Creation timestamp
    
    Config: from_attributes = True allows creating from SQLAlchemy models.
    """
    id: UUID
    user_id: UUID
    title: str
    course: Optional[str] = None
    due_date: datetime
    estimated_hours: float
    status: AssignmentStatus
    created_at: datetime

    class Config:
        from_attributes = True  # Allow creating from SQLAlchemy model
