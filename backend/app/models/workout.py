"""
Workout Model — Fitness Tracking

This module defines the data model for workout sessions:
- Workout: Main model for tracking workouts

Workouts are the core of the fitness domain in the AI briefing.
They drive the "days since last workout" scoring in the AI briefing.
"""

import uuid
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from app.database import Base
from app.models.base import TimestampMixin


class Workout(Base, TimestampMixin):
    """
    Workout session with type, duration, and notes.
    
    Each row represents one workout session with:
    - type: What kind of workout (e.g., "push", "pull", "cardio")
    - duration_mins: How long the workout lasted
    - notes: Optional notes about the session
    - logged_at: When the workout happened (nullable)
    - routine_id: Optional link to a routine (for structured workouts)
    
    The logged_at field is used for "days since last workout"
    calculations in the AI briefing and dashboard.
    """
    __tablename__ = "workouts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    routine_id = Column(UUID(as_uuid=True), ForeignKey("routines.id", ondelete="SET NULL"), nullable=True)
    type = Column(String, nullable=False)  # e.g., "push", "pull", "cardio"
    duration_mins = Column(Integer, nullable=False)
    notes = Column(String, nullable=True)
    logged_at = Column(DateTime, nullable=True)  # When the workout happened
