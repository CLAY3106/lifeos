from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse
from app.dependencies import get_current_user
from app.models.user import User
from app.services import expenses_service
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter(prefix="/expenses", tags=["expenses"])

class ExpenseListResponse(BaseModel):
    expenses: List[ExpenseResponse]
    monthly_budget: float

class ExpenseSummaryResponse(BaseModel):
    period: dict
    total: float
    by_category: dict
    by_group: dict
    budget: dict
    transaction_count: int

@router.post("", response_model=ExpenseResponse)
def create_expense(
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return expenses_service.create_expense(db, current_user, data)

@router.get("/summary", response_model=ExpenseSummaryResponse)
def get_expense_summary(
    period: str = Query("month", pattern="^(week|month|quarter|year)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return expenses_service.get_expense_summary(db, current_user, period)

@router.get("", response_model=ExpenseListResponse)
def get_expenses(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Expense).filter(Expense.user_id == current_user.id)

    if start_date:
        query = query.filter(Expense.spent_at >= start_date)
    if end_date:
        query = query.filter(Expense.spent_at <= end_date)

    expenses = query.order_by(Expense.spent_at.desc()).all()
    return {
        "expenses": expenses,
        "monthly_budget": current_user.monthly_budget or 0
    }

@router.patch("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: uuid.UUID,
    data: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return expenses_service.update_expense(db, current_user, expense_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{expense_id}")
def delete_expense(
    expense_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted"}