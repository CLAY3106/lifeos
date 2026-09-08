from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.expense import ExpenseCategory, BudgetGroup

class ExpenseCreate(BaseModel):
    amount: float
    category: ExpenseCategory = ExpenseCategory.other
    note: Optional[str] = None
    location: Optional[str] = None
    spent_at: Optional[datetime] = None
    group_override: Optional[BudgetGroup] = None

class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    category: Optional[ExpenseCategory] = None
    note: Optional[str] = None
    location: Optional[str] = None
    group_override: Optional[BudgetGroup] = None

class ExpenseResponse(BaseModel):
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
        from_attributes = True