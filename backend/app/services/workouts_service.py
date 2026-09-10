"""
Workouts Service — CRUD for Fitness Tracking

This module handles workout logging including:
1. Creating workout sessions
2. Activity logging for all changes

Workouts are the core of the fitness domain in the AI briefing.
They drive the "days since last workout" scoring.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.workout import Workout
from app.models.user import User
from app.schemas.workout import WorkoutCreate
from app.services.activity_log_service import log_activity


def create_workout(db: Session, user: User, data: WorkoutCreate) -> Workout:
    """
    Log a new workout session.
    
    Sets default values for:
    - logged_at: Current UTC time (if not provided)
    - routine_id: Optional link to a routine
    
    The logged_at field is used for "days since last workout"
    calculations in the AI briefing.
    """
    workout = Workout(
        id=uuid.uuid4(),
        user_id=user.id,
        routine_id=data.routine_id,
        type=data.type,
        duration_mins=data.duration_mins,
        notes=data.notes,
        logged_at=data.logged_at or datetime.now(timezone.utc)
    )
    db.add(workout)
    db.commit()
    db.refresh(workout)
    log_activity(db, user.id, "Logged workout", "workout", workout.id, f"{data.type} for {data.duration_mins} min")
    return workout
