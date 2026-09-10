"""
Workout Schemas — Request/Response Validation

This module defines Pydantic models for workout operations:
1. WorkoutCreate: Log a new workout
2. WorkoutResponse: Return workout data

These schemas validate incoming requests and serialize responses,
ensuring type safety and consistent API contracts.
"""

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class WorkoutCreate(BaseModel):
    """
    Schema for logging a new workout.
    
    Required fields:
    - type: Workout type (e.g., "strength", "cardio")
    - duration_mins: How long (in minutes)
    
    Optional fields:
    - notes: Additional notes
    - logged_at: When it happened (default: now)
    - routine_id: Link to a routine template
    """
    type: str
    duration_mins: int
    notes: Optional[str] = None
    logged_at: Optional[datetime] = None
    routine_id: Optional[UUID] = None


class WorkoutResponse(BaseModel):
    """
    Schema for returning workout data.
    
    Includes:
    - All workout fields
    - id: Workout UUID
    - user_id: Owner UUID
    - created_at: Creation timestamp
    
    Config: from_attributes = True allows creating from SQLAlchemy models.
    """
    id: UUID
    user_id: UUID
    routine_id: Optional[UUID] = None
    type: str
    duration_mins: int
    notes: Optional[str] = None
    logged_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True  # Allow creating from SQLAlchemy model
