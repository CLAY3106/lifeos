from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class WorkoutCreate(BaseModel):
    type: str
    duration_mins: int
    notes: Optional[str] = None
    logged_at: Optional[datetime] = None

class WorkoutResponse(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    duration_mins: int
    notes: Optional[str] = None
    logged_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True