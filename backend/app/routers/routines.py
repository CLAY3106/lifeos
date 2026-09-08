import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.routine import Routine, RoutineItem
from app.schemas.routine import (
    RoutineCreate, RoutineUpdate, RoutineResponse,
    RoutineItemCreate, RoutineItemResponse,
)
from app.dependencies import get_current_user
from app.models.user import User
from app.services import routines_service
from typing import List

router = APIRouter(prefix="/routines", tags=["routines"])


@router.post("", response_model=RoutineResponse)
def create_routine(
    data: RoutineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return routines_service.create_routine(db, current_user, data)


@router.get("", response_model=List[RoutineResponse])
def get_routines(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Routine).options(
        joinedload(Routine.items)
    ).filter(
        Routine.user_id == current_user.id
    ).order_by(Routine.created_at.desc()).all()


@router.get("/{routine_id}", response_model=RoutineResponse)
def get_routine(
    routine_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        routine = routines_service.get_routine(db, current_user, routine_id)
        return routine
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{routine_id}", response_model=RoutineResponse)
def update_routine(
    routine_id: uuid.UUID,
    data: RoutineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return routines_service.update_routine(db, current_user, routine_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{routine_id}")
def delete_routine(
    routine_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        routines_service.delete_routine(db, current_user, routine_id)
        return {"message": "Routine deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{routine_id}/items", response_model=RoutineItemResponse)
def add_routine_item(
    routine_id: uuid.UUID,
    data: RoutineItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        routine = routines_service.get_routine(db, current_user, routine_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    item = RoutineItem(
        id=uuid.uuid4(),
        routine_id=routine.id,
        exercise_name=data.exercise_name,
        sets=data.sets,
        reps=data.reps,
        duration_mins=data.duration_mins,
        day_of_week=data.day_of_week,
        order_index=data.order_index,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{routine_id}/items/{item_id}")
def delete_routine_item(
    routine_id: uuid.UUID,
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        routines_service.get_routine(db, current_user, routine_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    item = db.query(RoutineItem).filter(
        RoutineItem.id == item_id,
        RoutineItem.routine_id == routine_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    return {"message": "Item deleted"}
