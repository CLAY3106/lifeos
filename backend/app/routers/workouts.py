from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.workout import Workout
from app.schemas.workout import WorkoutCreate, WorkoutResponse
from app.dependencies import get_current_user
from app.models.user import User
from typing import List
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/workouts", tags=["workouts"])

@router.post("", response_model=WorkoutResponse)
def create_workout(
    data: WorkoutCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workout = Workout(
        id=uuid.uuid4(),
        user_id=current_user.id,
        type=data.type,
        duration_mins=data.duration_mins,
        notes=data.notes,
        logged_at=data.logged_at or datetime.now(timezone.utc)
    )
    db.add(workout)
    db.commit()
    db.refresh(workout)
    return workout

@router.get("", response_model=List[WorkoutResponse])
def get_workouts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Workout).filter(
        Workout.user_id == current_user.id
    ).order_by(Workout.logged_at.desc()).all()

@router.delete("/{workout_id}")
def delete_workout(
    workout_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workout = db.query(Workout).filter(
        Workout.id == workout_id,
        Workout.user_id == current_user.id
    ).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    
    db.delete(workout)
    db.commit()
    return {"message": "Workout deleted"}