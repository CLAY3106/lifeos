from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class ActivityLogResponse(BaseModel):
    id: UUID
    action: str
    entity_type: str
    entity_id: Optional[UUID] = None
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
