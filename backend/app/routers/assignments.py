from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.assignment import Assignment, AssignmentStatus
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate, AssignmentResponse
from app.dependencies import get_current_user
from app.models.user import User
from app.services import assignments_service
from typing import List
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/assignments", tags=["assignments"])

@router.post("", response_model=AssignmentResponse)
def create_assignment(
    data: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return assignments_service.create_assignment(db, current_user, data)

@router.get("", response_model=List[AssignmentResponse])
def get_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Assignment).filter(
        Assignment.user_id == current_user.id,
        Assignment.deleted_at == None
    ).order_by(Assignment.due_date).all()

@router.patch("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: uuid.UUID,
    data: AssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return assignments_service.update_assignment(db, current_user, assignment_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{assignment_id}")
def delete_assignment(
    assignment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id,
        Assignment.user_id == current_user.id,
        Assignment.deleted_at == None
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    assignment.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Assignment deleted"}