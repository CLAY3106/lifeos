"""
Expense Schemas — Request/Response Validation

This module defines Pydantic models for expense operations:
1. ExpenseCreate: Create a new expense
2. ExpenseUpdate: Update an existing expense
3. ExpenseResponse: Return expense data

These schemas validate incoming requests and serialize responses,
ensuring type safety and consistent API contracts.
"""

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.expense import ExpenseCategory, BudgetGroup


class ExpenseCreate(BaseModel):
    """
    Schema for creating a new expense.
    
    Required fields:
    - amount: How much was spent
    
    Optional fields:
    - category: Expense category (default: other)
    - note: What was purchased
    - location: Where it was purchased
    - spent_at: When it was spent (default: now)
    - group_override: Override the default budget group
    """
    amount: float
    category: ExpenseCategory = ExpenseCategory.other
    note: Optional[str] = None
    location: Optional[str] = None
    spent_at: Optional[datetime] = None
    group_override: Optional[BudgetGroup] = None


class ExpenseUpdate(BaseModel):
    """
    Schema for updating an existing expense.
    
    All fields are optional — only provided fields are updated.
    This allows partial updates (e.g., just changing the note).
    """
    amount: Optional[float] = None
    category: Optional[ExpenseCategory] = None
    note: Optional[str] = None
    location: Optional[str] = None
    group_override: Optional[BudgetGroup] = None


class ExpenseResponse(BaseModel):
    """
    Schema for returning expense data.
    
    Includes:
    - All expense fields
    - id: Expense UUID
    - user_id: Owner UUID
    - created_at: Creation timestamp
    
    Config: from_attributes = True allows creating from SQLAlchemy models.
    """
    id: UUID
    user_id: UUID
    amount: float
    category: ExpenseCategory
    note: Optional[str] = None
    location: Optional[str] = None
    spent_at: Optional[datetime] = None
    group_override: Optional[BudgetGroup] = None
    created_at: datetime

    class Config:
        from_attributes = True  # Allow creating from SQLAlchemy model
