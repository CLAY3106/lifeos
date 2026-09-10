"""
Activity Log Service — Track User Actions

This module provides functions for logging and retrieving user activities:
- log_activity: Record a user action in the activity log
- get_recent_activities: Get recent activities for a user

Activity logging is used across all services to track what users do
in the application (e.g., "Added job application", "Logged expense").
"""

from uuid import UUID
from sqlalchemy.orm import Session
from app.models.activity_log import ActivityLog


def log_activity(db: Session, user_id: UUID, action: str, entity_type: str, entity_id: UUID = None, details: str = None):
    """
    Record a user action in the activity log.
    
    This function is called by all services to track user actions.
    It creates a new ActivityLog entry with:
    - user_id: Who did the action
    - action: What they did (e.g., "Added job application")
    - entity_type: What type of entity (e.g., "job", "expense")
    - entity_id: ID of the specific entity (optional)
    - details: Additional context (optional)
    
    Args:
        db: Database session
        user_id: ID of the user performing the action
        action: Description of the action
        entity_type: Type of entity (job, expense, assignment, etc.)
        entity_id: ID of the specific entity (optional)
        details: Additional context about the action (optional)
    """
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
    """
    Get recent activities for a user.
    
    Returns the most recent activities ordered by timestamp (newest first).
    Used by the activity feed in the frontend.
    
    Args:
        db: Database session
        user_id: ID of the user
        limit: Maximum number of activities to return (default 20)
    
    Returns:
        List of ActivityLog entries
    """
    return (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
        .all()
    )
