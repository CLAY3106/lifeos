import uuid
from datetime import datetime, timezone, timedelta, date
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

def get_period_bounds(period: str) -> tuple[date, date]:
    today = date.today()
    if period == "week":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(weeks=1)
    elif period == "month":
        start = today.replace(day=1)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
    elif period == "quarter":
        quarter = (today.month - 1) // 3
        start = today.replace(month=quarter * 3 + 1, day=1)
        if start.month + 3 > 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 3)
    elif period == "year":
        start = today.replace(month=1, day=1)
        end = start.replace(year=start.year + 1)
    else:
        raise ValueError("Invalid period")
    return start, end

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

def get_expense_summary(db: Session, user: User, period: str = "month") -> dict:
    # Get the start and end dates for the period
    start, end = get_period_bounds(period)

    # Query all expenses within the period
    expenses = db.query(Expense).filter(
        Expense.user_id == user.id,
        Expense.spent_at >= start,
        Expense.spent_at < end
    ).all()

    # Calculate total amount spent
    total = sum(expense.amount for expense in expenses)

    # Group expenses by category (food, transport, study, fitness, other)
    by_category = {}
    # Group expenses by budget group (needs, wants, savings)
    by_group = {"needs": 0.0, "wants": 0.0, "savings": 0.0}

    # Single loop to populate both groupings
    for e in expenses:
        # Use enum value for string key (e.g., ExpenseCategory.food -> "food")
        cat = e.category.value
        by_category[cat] = by_category.get(cat, 0.0) + e.amount

        # Determine budget group: use override if set, otherwise use mapping
        if e.group_override:
            group = e.group_override.value
        else:
            group = CATEGORY_TO_GROUP[e.category]
        by_group[group] += e.amount

    # Round all values to 2 decimal places for currency
    by_category = {k: round(v, 2) for k, v in by_category.items()}
    by_group = {k: round(v, 2) for k, v in by_group.items()}

    # Calculate budget utilization
    budget = user.monthly_budget or 0

    return {
        "period": {"start": start, "end": end},
        "total": round(total, 2),
        "by_category": by_category,
        "by_group": by_group,
        "budget": {
            "monthly": budget,
            "spent": round(total, 2),
            "remaining": round(budget - total, 2),
            "percent": round((total / budget * 100) if budget else 0, 2)
        },
        "transaction_count": len(expenses)
    }
