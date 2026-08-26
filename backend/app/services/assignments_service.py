import uuid
from sqlalchemy.orm import Session
from app.models.assignment import Assignment
from app.models.user import User
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate


def create_assignment(db: Session, user: User, data: AssignmentCreate) -> Assignment:
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
    return assignment


def update_assignment(db: Session, user: User, assignment_id: uuid.UUID, data: AssignmentUpdate) -> Assignment:
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id,
        Assignment.user_id == user.id,
        Assignment.deleted_at == None
    ).first()
    if not assignment:
        raise ValueError("Assignment not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(assignment, field, value)

    db.commit()
    db.refresh(assignment)
    return assignment
