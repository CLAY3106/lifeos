import uuid
from sqlalchemy.orm import Session
from app.models.routine import Routine, RoutineItem
from app.models.user import User
from app.schemas.routine import RoutineCreate, RoutineUpdate


def create_routine(db: Session, user: User, data: RoutineCreate) -> Routine:
    routine = Routine(
        id=uuid.uuid4(),
        user_id=user.id,
        name=data.name,
    )
    db.add(routine)
    db.flush()

    for item_data in data.items:
        item = RoutineItem(
            id=uuid.uuid4(),
            routine_id=routine.id,
            exercise_name=item_data.exercise_name,
            sets=item_data.sets,
            reps=item_data.reps,
            duration_mins=item_data.duration_mins,
            day_of_week=item_data.day_of_week,
            order_index=item_data.order_index,
        )
        db.add(item)

    db.commit()
    db.refresh(routine)
    return routine


def get_routine(db: Session, user: User, routine_id: uuid.UUID) -> Routine:
    routine = db.query(Routine).filter(
        Routine.id == routine_id,
        Routine.user_id == user.id,
    ).first()
    if not routine:
        raise ValueError("Routine not found")
    return routine


def update_routine(db: Session, user: User, routine_id: uuid.UUID, data: RoutineUpdate) -> Routine:
    routine = get_routine(db, user, routine_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(routine, field, value)

    db.commit()
    db.refresh(routine)
    return routine


def delete_routine(db: Session, user: User, routine_id: uuid.UUID) -> None:
    routine = get_routine(db, user, routine_id)
    db.delete(routine)
    db.commit()
