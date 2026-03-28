from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.expense import ExpenseCategory

class ExpenseCreate(BaseModel):
    amount: float
    category: ExpenseCategory = ExpenseCategory.other
    note: Optional[str] = None
    spent_at: Optional[datetime] = None

class ExpenseResponse(BaseModel):
    id: UUID
    user_id: UUID
    amount: float
    category: ExpenseCategory
    note: Optional[str] = None
    spent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True