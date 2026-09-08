from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.activity_log import ActivityLogResponse
from app.dependencies import get_current_user
from app.models.user import User
from app.services import activity_log_service
from typing import List

router = APIRouter(prefix="/activity", tags=["activity"])

@router.get("", response_model=List[ActivityLogResponse])
def get_activities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return activity_log_service.get_recent_activities(db, current_user.id)
