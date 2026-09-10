"""
Expense Model — Financial Tracking

This module defines the data model for expenses:
- ExpenseCategory: food, transport, study, fitness, other
- BudgetGroup: needs, wants, savings (for 50/30/20 envelope budgeting)
- Expense: Main model for tracking expenses

Expenses are the core of the finance domain in the AI briefing.
They drive budget utilization scoring and spending summaries.
"""

import uuid
from sqlalchemy import Column, Float, DateTime, Text, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from app.database import Base
from app.models.base import TimestampMixin
import enum


class ExpenseCategory(enum.Enum):
    """
    Categories for expense classification.
    
    - food: Grocery, restaurant, delivery
    - transport: Gas, public transit, ride-share
    - study: Books, supplies, software
    - fitness: Gym, equipment, supplements
    - other: Everything else
    """
    food = "food"
    transport = "transport"
    study = "study"
    fitness = "fitness"
    other = "other"


class BudgetGroup(enum.Enum):
    """
    Budget groups for 50/30/20 envelope budgeting.
    
    - needs: Essential expenses (50% target)
    - wants: Discretionary expenses (30% target)
    - savings: Savings and investments (20% target)
    
    The group is auto-assigned from CATEGORY_TO_GROUP in the service layer,
    but can be overridden per-expense if needed.
    """
    needs = "needs"
    wants = "wants"
    savings = "savings"


class Expense(Base, TimestampMixin):
    """
    Expense with amount, category, and budget group.
    
    Each row represents one expense with:
    - amount: How much was spent
    - category: What type of expense (food, transport, etc.)
    - note: Optional description
    - location: Optional location
    - spent_at: When the expense happened (nullable)
    - group_override: Manual budget group override (nullable)
    
    The group_override field allows users to manually assign a budget group
    instead of using the CATEGORY_TO_GROUP mapping. This is useful for
    edge cases like "I bought food but it was for a party (wants)".
    """
    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(Enum(ExpenseCategory), default=ExpenseCategory.other)
    note = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    spent_at = Column(DateTime, nullable=True)  # When the expense happened
    group_override = Column(Enum(BudgetGroup), nullable=True)  # Manual override for budget group
