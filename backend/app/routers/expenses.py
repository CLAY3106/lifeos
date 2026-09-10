"""
Expenses Router — CRUD, Summary, and Period Filtering

Endpoints:
- POST /expenses — Create a new expense (auto-assigns budget group)
- GET /expenses/summary — Get period-based summary (week/month/quarter/year)
- GET /expenses — List expenses with optional date range filtering
- PATCH /expenses/:id — Update an expense
- DELETE /expenses/:id — Delete an expense

The summary endpoint powers the finance dashboard and provides:
- Total spending for the period
- Breakdown by category and budget group
- Budget utilization metrics
"""

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
    """Response for listing expenses — includes expenses and monthly budget."""
    expenses: List[ExpenseResponse]
    monthly_budget: float


class ExpenseSummaryResponse(BaseModel):
    """
    Response for expense summary — includes period, totals, breakdowns, and budget info.
    
    The by_category dict maps category names to amounts (e.g., {"food": 450.20}).
    The by_group dict maps budget groups to amounts (e.g., {"needs": 570.20}).
    The budget dict includes monthly budget, spent, remaining, and percent.
    """
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
    """Create a new expense. Budget group is auto-assigned from CATEGORY_TO_GROUP if not provided."""
    return expenses_service.create_expense(db, current_user, data)


@router.get("/summary", response_model=ExpenseSummaryResponse)
def get_expense_summary(
    period: str = Query("month", pattern="^(week|month|quarter|year)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get period-based expense summary.
    
    The period parameter uses half-open intervals:
    - "week": Monday to Monday
    - "month": 1st to 1st
    - "quarter": Quarter start to quarter start
    - "year": Jan 1 to Jan 1
    """
    return expenses_service.get_expense_summary(db, current_user, period)


@router.get("", response_model=ExpenseListResponse)
def get_expenses(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List expenses with optional date range filtering.
    
    If start_date and/or end_date are provided, filters expenses within that range.
    If not provided, returns all expenses for the user.
    
    This is the "period boundaries" feature — you can query "show me Q3 expenses"
    or "show me this week" by providing the appropriate dates.
    """
    query = db.query(Expense).filter(Expense.user_id == current_user.id)

    # Apply optional date range filters
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
    """Update an expense by ID. Only updates fields that are explicitly set."""
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
    """Delete an expense by ID."""
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted"}
