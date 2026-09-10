"""
Workouts Router — CRUD for Fitness Tracking

This module handles workout logging endpoints:
1. POST / — Log a new workout
2. GET / — List all workouts (sorted by date, newest first)
3. DELETE /:id — Hard delete a workout

Workouts are sorted by logged_at (newest first) to show
the most recent activity at the top.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.workout import Workout
from app.schemas.workout import WorkoutCreate, WorkoutResponse
from app.dependencies import get_current_user
from app.models.user import User
from app.services import workouts_service
from typing import List
import uuid

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.post("", response_model=WorkoutResponse)
def create_workout(
    data: WorkoutCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Log a new workout session.
    
    Sets default values for:
    - logged_at: Current UTC time (if not provided)
    - routine_id: Optional link to a routine
    """
    return workouts_service.create_workout(db, current_user, data)


@router.get("", response_model=List[WorkoutResponse])
def get_workouts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all workouts for the current user.
    
    Sorted by logged_at (newest first) to show
    the most recent activity at the top.
    """
    return db.query(Workout).filter(
        Workout.user_id == current_user.id
    ).order_by(Workout.logged_at.desc()).all()


@router.delete("/{workout_id}")
def delete_workout(
    workout_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Hard delete a workout.
    
    Unlike assignments, workouts are hard-deleted because
    there's no need to preserve deleted workout history.
    """
    workout = db.query(Workout).filter(
        Workout.id == workout_id,
        Workout.user_id == current_user.id
    ).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    
    db.delete(workout)
    db.commit()
    return {"message": "Workout deleted"}
