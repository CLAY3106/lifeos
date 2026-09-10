"""
Assignments Service — CRUD for Academic Tasks

This module handles assignment management including:
1. Creating assignments with default values
2. Updating assignments (including status changes)
3. Activity logging for all changes

Assignments are the core of the academic domain in the AI briefing.
They drive urgency scoring and weekly load calculations.
"""

import uuid
from sqlalchemy.orm import Session
from app.models.assignment import Assignment
from app.models.user import User
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate
from app.services.activity_log_service import log_activity


def create_assignment(db: Session, user: User, data: AssignmentCreate) -> Assignment:
    """
    Create a new assignment.
    
    Sets default values for:
    - status: pending (default)
    - importance: low (default)
    - estimated_hours: 1.0 (default)
    """
    assignment = Assignment(
        id=uuid.uuid4(),
        user_id=user.id,
        title=data.title,
        course=data.course,
        due_date=data.due_date,
        estimated_hours=data.estimated_hours
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    log_activity(db, user.id, "Added assignment", "assignment", assignment.id, data.title)
    return assignment


def update_assignment(db: Session, user: User, assignment_id: uuid.UUID, data: AssignmentUpdate) -> Assignment:
    """
    Update an assignment. Only updates fields that are explicitly set.
    
    If status is updated, logs the change to the activity log.
    Uses soft delete (deleted_at) — deleted assignments are excluded from queries.
    """
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id,
        Assignment.user_id == user.id,
        Assignment.deleted_at == None  # Exclude soft-deleted assignments
    ).first()
    if not assignment:
        raise ValueError("Assignment not found")

    # Dynamically set only the fields that were provided
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(assignment, field, value)

    db.commit()
    db.refresh(assignment)
    if data.status:
        log_activity(db, user.id, f"Updated assignment to {data.status}", "assignment", assignment.id)
    return assignment
