"""
Assignment Model — Academic Task Tracking

This module defines the data model for academic assignments:
- AssignmentStatus: pending, done, overdue
- AssignmentImportance: low, high (for priority sorting)
- Assignment: Main model for tracking assignments

Assignments are the core of the academic domain in the AI briefing.
They drive urgency scoring and weekly load calculations.
"""

import uuid
from sqlalchemy import Column, String, Float, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from app.database import Base
from app.models.base import TimestampMixin
import enum


class AssignmentStatus(enum.Enum):
    """
    Possible statuses for an assignment.
    
    - pending: Not yet submitted (default)
    - done: Successfully submitted
    - overdue: Past due date (auto-set by system)
    """
    pending = "pending"
    done = "done"
    overdue = "overdue"


class AssignmentImportance(enum.Enum):
    """
    Importance level for assignment prioritization.
    
    - low: Regular assignment (default)
    - high: High-stakes assignment (exam, project, etc.)
    
    Used for sorting in the frontend — high importance items appear first.
    """
    low = "low"
    high = "high"


class Assignment(Base, TimestampMixin):
    """
    Academic assignment with tracking and prioritization.
    
    Each row represents one assignment with:
    - Title and course info
    - Due date and estimated hours
    - Status (pending/done/overdue)
    - Importance (low/high) for priority sorting
    - Soft delete support (deleted_at)
    
    The estimated_hours field is used for weekly load calculations
    in the AI briefing and dashboard.
    """
    __tablename__ = "assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    course = Column(String, nullable=True)
    due_date = Column(DateTime, nullable=False)
    estimated_hours = Column(Float, default=1.0)  # Used for weekly load calculation
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.pending)
    importance = Column(Enum(AssignmentImportance), default=AssignmentImportance.low, nullable=False)
    importance_set_manually = Column(Boolean, default=False, nullable=False)  # Track if user set importance
    deleted_at = Column(DateTime, nullable=True)  # Soft delete support
