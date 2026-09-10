"""
Assignments Router — CRUD for Academic Tasks

This module handles assignment management endpoints:
1. POST / — Create a new assignment
2. GET / — List all assignments (sorted by status, then due date)
3. PATCH /:id — Update an assignment
4. DELETE /:id — Soft delete an assignment

Assignments are sorted by status (pending → overdue → done),
then by due date. This ensures the most urgent items appear first.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import case
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
    """
    Create a new assignment.
    
    The assignment is automatically assigned to the current user
    and gets default values for status, importance, and estimated hours.
    """
    return assignments_service.create_assignment(db, current_user, data)


@router.get("", response_model=List[AssignmentResponse])
def get_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all assignments for the current user.
    
    Sorted by:
    1. Status: pending → overdue → done
    2. Due date: earliest first
    
    Soft-deleted assignments are excluded.
    """
    # Custom sort order: pending (0) → overdue (1) → done (2)
    status_order = case(
        (Assignment.status == AssignmentStatus.pending, 0),
        (Assignment.status == AssignmentStatus.overdue, 1),
        (Assignment.status == AssignmentStatus.done, 2),
    )
    return db.query(Assignment).filter(
        Assignment.user_id == current_user.id,
        Assignment.deleted_at == None
    ).order_by(status_order, Assignment.due_date).all()


@router.patch("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: uuid.UUID,
    data: AssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an assignment. Only updates fields that are explicitly set.
    
    Raises 404 if assignment not found.
    """
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
    """
    Soft delete an assignment.
    
    Sets deleted_at timestamp instead of actually deleting the row.
    This preserves data for historical analysis and prevents
    orphaned references.
    """
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id,
        Assignment.user_id == current_user.id,
        Assignment.deleted_at == None
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Soft delete — set timestamp instead of actually deleting
    assignment.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Assignment deleted"}
