from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from app.models.routine import RoutineDayOfWeek


class RoutineItemCreate(BaseModel):
    exercise_name: str
    sets: Optional[int] = None
    reps: Optional[int] = None
    duration_mins: Optional[int] = None
    day_of_week: Optional[RoutineDayOfWeek] = None
    order_index: int = 0


class RoutineItemUpdate(BaseModel):
    exercise_name: Optional[str] = None
    sets: Optional[int] = None
    reps: Optional[int] = None
    duration_mins: Optional[int] = None
    day_of_week: Optional[RoutineDayOfWeek] = None
    order_index: Optional[int] = None


class RoutineItemResponse(BaseModel):
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
        from_attributes = True


class RoutineCreate(BaseModel):
    name: str
    items: List[RoutineItemCreate] = []


class RoutineUpdate(BaseModel):
    name: Optional[str] = None


class RoutineResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    items: List[RoutineItemResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True
