import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.document_chunk import DocumentChunk
from app.services.embedding import get_embedding

def ingest_entity(db: Session, user_id, entity_type: str, entity_id, text: str):
    """Embed a single chunk and store it in document_chunks."""
    
    # Check if chunk already exists for this entity (update case)
    existing = db.query(DocumentChunk).filter(
        DocumentChunk.user_id == user_id,
        DocumentChunk.entity_type == entity_type,
        DocumentChunk.entity_id == entity_id
    ).first()
    
    # Embed the text
    embedding = get_embedding(text)
    embedding_json = json.dumps(embedding) if embedding else None
    
    if existing:
        # Update existing chunk
        existing.content = text
        existing.embedding = embedding_json
        existing.updated_at = datetime.now(timezone.utc)
    else:
        # Create new chunk
        chunk = DocumentChunk(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            content=text,
            embedding=embedding_json,
        )
        db.add(chunk)
    
    db.commit()


def ingest_all(db: Session, user):
    """Process all entities for a user and build the search index."""
    from app.models.assignment import Assignment
    from app.models.job import JobApplication
    from app.models.expense import Expense
    from app.models.workout import Workout
    
    # Clear existing chunks for this user (fresh rebuild)
    db.query(DocumentChunk).filter(DocumentChunk.user_id == user.id).delete()
    db.commit()
    
    # Ingest assignments
    for a in db.query(Assignment).filter(Assignment.user_id == user.id, Assignment.deleted_at == None).all():
        ingest_entity(db, user.id, "assignment", a.id, chunk_assignment(a))
    
    # Ingest jobs
    for j in db.query(JobApplication).filter(JobApplication.user_id == user.id).all():
        ingest_entity(db, user.id, "job", j.id, chunk_job(j))
    
    # Ingest expenses
    for e in db.query(Expense).filter(Expense.user_id == user.id).all():
        ingest_entity(db, user.id, "expense", e.id, chunk_expense(e))
    
    # Ingest workouts
    for w in db.query(Workout).filter(Workout.user_id == user.id).all():
        ingest_entity(db, user.id, "workout", w.id, chunk_workout(w))
    
    count = db.query(DocumentChunk).filter(DocumentChunk.user_id == user.id).count()
    print(f"Ingested {count} chunks for {user.name}")

def chunk_assignment(assignment) -> str:
    course_part = f" for {assignment.course}" if assignment.course else ""
    return (
        f"Assignment: {assignment.title}{course_part}, "
        f"due {assignment.due_date.strftime('%b %d')}, "
        f"status: {assignment.status.value}, "
        f"estimated {assignment.estimated_hours}h"
    )

def chunk_expense(expense) -> str:
    return (
        f"Expense: ${expense.amount:.2f} spend on {expense.note if expense.note else 'None'}, "
        f"{expense.category.value}, "
        f"{expense.group_override.value if expense.group_override else 'None'}, "
        f"spent at {expense.spent_at.strftime('%b %d') if expense.spent_at else 'None'}"
    )

def chunk_job(job) -> str:
    location_part = f", {job.location}" if job.location else ""
    notes_part = f", {job.notes}" if job.notes else ""
    return (
        f"Job Application: {job.role} at {job.company}, "
        f"applied {job.applied_date.strftime('%b %d')}, "
        f"status: {job.status.value}{location_part}{notes_part}"
    )

def chunk_workout(workout) -> str:
    notes_part = f", {workout.notes}" if workout.notes else ""
    return (
        f"Workout: {workout.type} for {workout.duration_mins}min{notes_part}"
    )