"""
Routine Schemas — Request/Response Validation

This module defines Pydantic models for routine operations:
1. RoutineItemCreate: Create a routine item
2. RoutineItemUpdate: Update a routine item
3. RoutineItemResponse: Return routine item data
4. RoutineCreate: Create a routine with items
5. RoutineUpdate: Update a routine
6. RoutineResponse: Return routine data with items

These schemas validate incoming requests and serialize responses,
ensuring type safety and consistent API contracts.
"""

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from app.models.routine import RoutineDayOfWeek


class RoutineItemCreate(BaseModel):
    """
    Schema for creating a routine item.
    
    Required fields:
    - exercise_name: What exercise (e.g., "Bench Press")
    
    Optional fields:
    - sets: Number of sets
    - reps: Reps per set
    - duration_mins: Duration in minutes (for cardio)
    - day_of_week: Which day to do this exercise
    - order_index: Position in routine (default: 0)
    """
    exercise_name: str
    sets: Optional[int] = None
    reps: Optional[int] = None
    duration_mins: Optional[int] = None
    day_of_week: Optional[RoutineDayOfWeek] = None
    order_index: int = 0


class RoutineItemUpdate(BaseModel):
    """
    Schema for updating a routine item.
    
    All fields are optional — only provided fields are updated.
    """
    exercise_name: Optional[str] = None
    sets: Optional[int] = None
    reps: Optional[int] = None
    duration_mins: Optional[int] = None
    day_of_week: Optional[RoutineDayOfWeek] = None
    order_index: Optional[int] = None


class RoutineItemResponse(BaseModel):
    """
    Schema for returning routine item data.
    
    Includes all item fields plus id, routine_id, and created_at.
    
    Config: from_attributes = True allows creating from SQLAlchemy models.
    """
    id: UUID
    routine_id: UUID
    exercise_name: str
    sets: Optional[int] = None
    reps: Optional[int] = None
    duration_mins: Optional[int] = None
    day_of_week: Optional[RoutineDayOfWeek] = None
    order_index: int
    created_at: datetime

    class Config:
        from_attributes = True  # Allow creating from SQLAlchemy model


class RoutineCreate(BaseModel):
    """
    Schema for creating a routine with items.
    
    Required fields:
    - name: Routine name (e.g., "Push Day")
    
    Optional fields:
    - items: List of exercises to include
    """
    name: str
    items: List[RoutineItemCreate] = []


class RoutineUpdate(BaseModel):
    """
    Schema for updating a routine.
    
    All fields are optional — only provided fields are updated.
    """
    name: Optional[str] = None


class RoutineResponse(BaseModel):
    """
    Schema for returning routine data with items.
    
    Includes:
    - All routine fields
    - items: Nested list of exercises
    - id: Routine UUID
    - user_id: Owner UUID
    - created_at: Creation timestamp
    
    Config: from_attributes = True allows creating from SQLAlchemy models.
    """
    id: UUID
    user_id: UUID
    name: str
    items: List[RoutineItemResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True  # Allow creating from SQLAlchemy model
