import uuid
from sqlalchemy import Column, Float, DateTime, Text, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from app.database import Base
from app.models.base import TimestampMixin
import enum

class ExpenseCategory(enum.Enum):
    food = "food"
    transport = "transport"
    study = "study"
    fitness = "fitness"
    other = "other"

class BudgetGroup(enum.Enum):
    needs = "needs"
    wants = "wants"
    savings = "savings"

class Expense(Base, TimestampMixin):
    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(Enum(ExpenseCategory), default=ExpenseCategory.other)
    note = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    spent_at = Column(DateTime, nullable=True)
    group_override = Column(Enum(BudgetGroup), nullable=True)