"""
Routine Models — Workout Templates

This module defines the data models for workout routines:
1. Routine: A workout template with a name
2. RoutineItem: An exercise within a routine (sets, reps, duration)

Routines are templates that users can reuse across workouts.
They define a set of exercises with:
- Exercise name
- Sets and reps (optional)
- Duration in minutes (optional)
- Day of week (optional)
- Order index for sorting
"""

import uuid
from sqlalchemy import Column, String, Integer, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin
import enum


class RoutineDayOfWeek(enum.Enum):
    """
    Days of the week for routine scheduling.
    
    Used to organize routines by day (e.g., "Monday: Chest day").
    """
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"


class Routine(Base, TimestampMixin):
    """
    Workout routine (template) model.
    
    A routine is a collection of exercises that can be reused
    across multiple workouts. It has:
    - user_id: Who owns this routine
    - name: Routine name (e.g., "Push Day", "Leg Day")
    - items: List of exercises in this routine
    
    Items are ordered by order_index and cascade-deleted
    when the routine is deleted.
    """
    __tablename__ = "routines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    # Cascade delete: deleting a routine deletes all its items
    # Order by order_index for consistent exercise ordering
    items = relationship("RoutineItem", cascade="all, delete-orphan", order_by="RoutineItem.order_index")


class RoutineItem(Base, TimestampMixin):
    """
    Individual exercise within a routine.
    
    Each item represents one exercise with:
    - exercise_name: What exercise (e.g., "Bench Press")
    - sets: Number of sets (optional)
    - reps: Reps per set (optional)
    - duration_mins: Duration in minutes (optional, for cardio)
    - day_of_week: Which day to do this exercise (optional)
    - order_index: Position in the routine (for sorting)
    """
    __tablename__ = "routine_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    routine_id = Column(UUID(as_uuid=True), ForeignKey("routines.id", ondelete="CASCADE"), nullable=False)
    exercise_name = Column(String, nullable=False)
    sets = Column(Integer, nullable=True)  # Optional: for strength exercises
    reps = Column(Integer, nullable=True)  # Optional: for strength exercises
    duration_mins = Column(Integer, nullable=True)  # Optional: for cardio
    day_of_week = Column(Enum(RoutineDayOfWeek), nullable=True)  # Optional: for scheduling
    order_index = Column(Integer, default=0, nullable=False)  # For sorting exercises
