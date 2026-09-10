import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.expense import Expense, ExpenseCategory, BudgetGroup
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


def get_period_bounds(period: str = "month") -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    if period == "week":
        start = now - timedelta(days=now.weekday())
    elif period == "quarter":
        quarter = (now.month - 1) // 3
        start = now.replace(month=quarter * 3 + 1, day=1)
    elif period == "year":
        start = now.replace(month=1, day=1)
    else:
        start = now.replace(day=1)
    return start.replace(hour=0, minute=0, second=0, tzinfo=timezone.utc), now


def get_expense_summary(db: Session, user: User, period: str = "month") -> dict:
    start, end = get_period_bounds(period)

    expenses = db.query(Expense).filter(
        Expense.user_id == user.id,
        Expense.spent_at >= start,
        Expense.spent_at <= end
    ).all()

    total = sum(e.amount for e in expenses)
    by_category = {}
    by_group = {"needs": 0.0, "wants": 0.0, "savings": 0.0}

    for e in expenses:
        cat = e.category.value
        by_category[cat] = by_category.get(cat, 0.0) + e.amount

        if e.group_override:
            group = e.group_override.value
        else:
            group = CATEGORY_TO_GROUP.get(e.category, "wants")
        by_group[group] += e.amount

    budget = user.monthly_budget or 0
    return {
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "total": round(total, 2),
        "by_category": {k: round(v, 2) for k, v in by_category.items()},
        "by_group": {k: round(v, 2) for k, v in by_group.items()},
        "budget": {
            "monthly": budget,
            "spent": round(total, 2),
            "remaining": round(budget - total, 2),
            "percent": round((total / budget * 100) if budget > 0 else 0, 1)
        },
        "transaction_count": len(expenses)
    }


def create_expense(db: Session, user: User, data: ExpenseCreate) -> Expense:
    group = data.group_override or CATEGORY_TO_GROUP.get(data.category)

    expense = Expense(
        id=uuid.uuid4(),
        user_id=user.id,
        amount=data.amount,
        category=data.category,
        note=data.note,
        location=data.location,
        spent_at=data.spent_at or datetime.now(timezone.utc),
        group_override=group
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
