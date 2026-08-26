import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.workout import Workout
from app.models.user import User
from app.schemas.workout import WorkoutCreate


def create_workout(db: Session, user: User, data: WorkoutCreate) -> Workout:
    workout = Workout(
        id=uuid.uuid4(),
        user_id=user.id,
        type=data.type,
        duration_mins=data.duration_mins,
        notes=data.notes,
        logged_at=data.logged_at or datetime.now(timezone.utc)
    )
    db.add(workout)
    db.commit()
    db.refresh(workout)
    return workout
