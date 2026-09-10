import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.expense import Expense, ExpenseCategory
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.services.activity_log_service import log_activity

CATEGORY_TO_GROUP = {
    ExpenseCategory.food: "needs",
    ExpenseCategory.transport: "needs",
    ExpenseCategory.study: "needs",
    ExpenseCategory.fitness: "wants",
    ExpenseCategory.other: "wants",
}


def create_expense(db: Session, user: User, data: ExpenseCreate) -> Expense:
    expense = Expense(
        id=uuid.uuid4(),
        user_id=user.id,
        amount=data.amount,
        category=data.category,
        note=data.note,
        location=data.location,
        spent_at=data.spent_at or datetime.now(timezone.utc),
        group_override=data.group_override
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    log_activity(db, user.id, "Logged expense", "expense", expense.id, f"${data.amount} on {data.category.value}")
    return expense


def update_expense(db: Session, user: User, expense_id: uuid.UUID, data: ExpenseUpdate) -> Expense:
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == user.id
    ).first()
    if not expense:
        raise ValueError("Expense not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(expense, field, value)

    db.commit()
    db.refresh(expense)
    return expense
