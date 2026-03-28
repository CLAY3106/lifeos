import uuid
from sqlalchemy import Column, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from app.database import Base
from app.models.base import TimestampMixin
import enum

class InsightType(enum.Enum):
    daily = "daily"
    weekly = "weekly"

class AIInsight(Base, TimestampMixin):
    __tablename__ = "ai_insights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(Enum(InsightType), nullable=False)
    content = Column(Text, nullable=False)
    generated_at = Column(DateTime, nullable=True)