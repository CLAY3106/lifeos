import uuid
from sqlalchemy import Column, String, Float, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from app.database import Base
from app.models.base import TimestampMixin
import enum

class AssignmentStatus(enum.Enum):
    pending = "pending"
    done = "done"
    overdue = "overdue"

class Assignment(Base, TimestampMixin):
    __tablename__ = "assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    course = Column(String, nullable=True)
    due_date = Column(DateTime, nullable=False)
    estimated_hours = Column(Float, default=1.0)
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.pending)
    deleted_at = Column(DateTime, nullable=True)