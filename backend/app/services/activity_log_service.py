from uuid import UUID
from sqlalchemy.orm import Session
from app.models.activity_log import ActivityLog

def log_activity(db: Session, user_id: UUID, action: str, entity_type: str, entity_id: UUID = None, details: str = None):
    entry = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.add(entry)
    db.commit()

def get_recent_activities(db: Session, user_id: UUID, limit: int = 20):
    return (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
        .all()
    )
