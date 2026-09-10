"""
Routines Service — CRUD for Workout Routines

This module handles routine management including:
1. Creating routines with nested items
2. Reading routines
3. Updating routines
4. Deleting routines

Routines are templates for workouts — they define a set of exercises
with sets, reps, and duration that can be reused across workouts.
"""

import uuid
from sqlalchemy.orm import Session
from app.models.routine import Routine, RoutineItem
from app.models.user import User
from app.schemas.routine import RoutineCreate, RoutineUpdate


def create_routine(db: Session, user: User, data: RoutineCreate) -> Routine:
    """
    Create a new routine with nested items.
    
    This function:
    1. Creates the routine
    2. Flushes to get the routine ID
    3. Creates all routine items with the routine ID
    4. Commits everything in one transaction
    
    The flush() call is needed to get the routine ID before creating items,
    but it doesn't commit the transaction yet.
    """
    routine = Routine(
        id=uuid.uuid4(),
        user_id=user.id,
        name=data.name,
    )
    db.add(routine)
    db.flush()  # Get the routine ID without committing

    # Create all routine items
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
    """
    Get a routine by ID.
    
    Raises ValueError if not found (converted to 404 by the router).
    """
    routine = db.query(Routine).filter(
        Routine.id == routine_id,
        Routine.user_id == user.id,
    ).first()
    if not routine:
        raise ValueError("Routine not found")
    return routine


def update_routine(db: Session, user: User, routine_id: uuid.UUID, data: RoutineUpdate) -> Routine:
    """
    Update a routine's fields. Only updates fields that are explicitly set.
    
    Note: This doesn't update nested items — use separate endpoints for that.
    """
    routine = get_routine(db, user, routine_id)

    # Dynamically set only the fields that were provided
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(routine, field, value)

    db.commit()
    db.refresh(routine)
    return routine


def delete_routine(db: Session, user: User, routine_id: uuid.UUID) -> None:
    """
    Delete a routine and all its items.
    
    The cascade delete on the relationship ensures all items are deleted
    when the routine is deleted.
    """
    routine = get_routine(db, user, routine_id)
    db.delete(routine)
    db.commit()
