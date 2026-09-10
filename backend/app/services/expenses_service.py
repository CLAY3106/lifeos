"""
Expenses Service — CRUD, Summary, and Period Filtering

This module handles expense management including:
1. Creating expenses with automatic budget group assignment
2. Updating expenses
3. Generating period-based summaries (week/month/quarter/year)
4. Providing period bounds for date filtering

Key concepts:
- CATEGORY_TO_GROUP: Maps expense categories to budget groups (needs/wants/savings)
- Period bounds: Returns start/end dates for half-open interval queries (>= start AND < end)
- Budget groups: Used for 50/30/20 envelope budgeting visualization
"""

import uuid
from datetime import datetime, timezone, timedelta, date
from sqlalchemy.orm import Session
from app.models.expense import Expense, ExpenseCategory
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.services.activity_log_service import log_activity

# Maps expense categories to budget groups for 50/30/20 envelope budgeting
# "needs" = essential expenses (food, transport, study)
# "wants" = discretionary expenses (fitness, other)
# "savings" = not used by default, but available for manual override
CATEGORY_TO_GROUP = {
    ExpenseCategory.food: "needs",
    ExpenseCategory.transport: "needs",
    ExpenseCategory.study: "needs",
    ExpenseCategory.fitness: "wants",
    ExpenseCategory.other: "wants",
}


def get_period_bounds(period: str) -> tuple[date, date]:
    """
    Return (start, end) dates for a given period using half-open intervals.
    
    Half-open intervals mean:
    - start is inclusive (>= start)
    - end is exclusive (< end)
    
    This is cleaner than inclusive end dates because:
    - Sept 30 at 23:59:59 is still < Oct 1, so it's included
    - Oct 1 at 00:00:00 is NOT < Oct 1, so it's excluded
    
    Args:
        period: One of "week", "month", "quarter", "year"
    
    Returns:
        Tuple of (start_date, end_date)
    
    Raises:
        ValueError: If period is not one of the valid options
    """
    today = date.today()
    
    if period == "week":
        # Start = Monday of this week, End = Monday of next week
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(weeks=1)
    elif period == "month":
        # Start = 1st of this month, End = 1st of next month
        start = today.replace(day=1)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
    elif period == "quarter":
        # Start = 1st of current quarter, End = 1st of next quarter
        quarter = (today.month - 1) // 3
        start = today.replace(month=quarter * 3 + 1, day=1)
        if start.month + 3 > 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 3)
    elif period == "year":
        # Start = Jan 1 of this year, End = Jan 1 of next year
        start = today.replace(month=1, day=1)
        end = start.replace(year=start.year + 1)
    else:
        raise ValueError("Invalid period")
    
    return start, end


def create_expense(db: Session, user: User, data: ExpenseCreate) -> Expense:
    """
    Create a new expense with automatic budget group assignment.
    
    If the user provides a group_override, use that.
    Otherwise, auto-assign based on CATEGORY_TO_GROUP mapping.
    This wires the previously dead CATEGORY_TO_GROUP dict into actual logic.
    """
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
    """
    Update an expense by ID. Only updates fields that are explicitly set.
    
    Uses Pydantic's model_dump(exclude_unset=True) to only update
    fields that were actually provided in the request.
    """
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == user.id
    ).first()
    if not expense:
        raise ValueError("Expense not found")

    # Dynamically set only the fields that were provided
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(expense, field, value)

    db.commit()
    db.refresh(expense)
    return expense


def get_expense_summary(db: Session, user: User, period: str = "month") -> dict:
    """
    Generate a period-based expense summary with category and budget group breakdowns.
    
    This powers the finance dashboard and provides:
    - Total spending for the period
    - Breakdown by category (food, transport, study, fitness, other)
    - Breakdown by budget group (needs, wants, savings)
    - Budget utilization metrics (monthly budget, spent, remaining, percent)
    - Transaction count
    
    The summary uses a single loop through expenses for efficiency,
    populating both by_category and by_group simultaneously.
    
    Args:
        db: Database session
        user: Authenticated user
        period: One of "week", "month", "quarter", "year"
    
    Returns:
        Dictionary with period, totals, breakdowns, and budget info
    """
    # Get the start and end dates for the period
    start, end = get_period_bounds(period)

    # Query all expenses within the period using half-open interval
    expenses = db.query(Expense).filter(
        Expense.user_id == user.id,
        Expense.spent_at >= start,
        Expense.spent_at < end
    ).all()

    # Calculate total amount spent
    total = sum(expense.amount for expense in expenses)

    # Initialize groupings
    by_category = {}  # e.g., {"food": 450.20, "transport": 120.00}
    by_group = {"needs": 0.0, "wants": 0.0, "savings": 0.0}  # e.g., {"needs": 570.20, "wants": 480.30}

    # Single loop to populate both groupings (efficient)
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
