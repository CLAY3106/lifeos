import uuid
from sqlalchemy import Column, String, Integer, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin
import enum

class RoutineDayOfWeek(enum.Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"

class Routine(Base, TimestampMixin):
    __tablename__ = "routines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    items = relationship("RoutineItem", cascade="all, delete-orphan", order_by="RoutineItem.order_index")

class RoutineItem(Base, TimestampMixin):
    __tablename__ = "routine_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    routine_id = Column(UUID(as_uuid=True), ForeignKey("routines.id", ondelete="CASCADE"), nullable=False)
    exercise_name = Column(String, nullable=False)
    sets = Column(Integer, nullable=True)
    reps = Column(Integer, nullable=True)
    duration_mins = Column(Integer, nullable=True)
    day_of_week = Column(Enum(RoutineDayOfWeek), nullable=True)
    order_index = Column(Integer, default=0, nullable=False)
