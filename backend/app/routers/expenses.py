from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseResponse
from app.dependencies import get_current_user
from app.models.user import User
from app.services import expenses_service
from typing import List
import uuid

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.post("", response_model=ExpenseResponse)
def create_expense(
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return expenses_service.create_expense(db, current_user, data)

@router.get("", response_model=List[ExpenseResponse])
def get_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Expense).filter(
        Expense.user_id == current_user.id
    ).order_by(Expense.spent_at.desc()).all()

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