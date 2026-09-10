"""
Activity Log Model — Track User Actions

This module defines the data model for activity logging:
- ActivityLog: Stores user actions for audit trail and activity feed

Activity logging tracks what users do in the application,
providing an audit trail and powering the activity feed.
"""

import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from app.database import Base
from app.models.base import TimestampMixin


class ActivityLog(Base, TimestampMixin):
    """
    Activity log entry for tracking user actions.
    
    Each row represents one user action with:
    - user_id: Who did the action
    - action: What they did (e.g., "Added job application")
    - entity_type: What type of entity (e.g., "job", "expense")
    - entity_id: ID of the specific entity (optional)
    - details: Additional context (optional)
    
    This provides:
    - Audit trail for debugging
    - Activity feed in the frontend
    - Usage analytics for product insights
    """
    __tablename__ = "activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)  # e.g., "Added job application"
    entity_type = Column(String, nullable=False)  # e.g., "job", "expense"
    entity_id = Column(UUID(as_uuid=True), nullable=True)  # ID of the specific entity
    details = Column(String, nullable=True)  # Additional context
