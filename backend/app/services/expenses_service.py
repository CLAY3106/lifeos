import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.expense import Expense
from app.models.user import User
from app.schemas.expense import ExpenseCreate


def create_expense(db: Session, user: User, data: ExpenseCreate) -> Expense:
    expense = Expense(
        id=uuid.uuid4(),
        user_id=user.id,
        amount=data.amount,
        category=data.category,
        note=data.note,
        spent_at=data.spent_at or datetime.now(timezone.utc)
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense
