from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.assignment import Assignment, AssignmentStatus
from app.models.job import JobApplication, JobStatus
from app.models.workout import Workout
from app.models.expense import Expense
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    now = datetime.now(timezone.utc)
    week_from_now = now + timedelta(days=7)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0)

    # assignments due in next 7 days
    upcoming_assignments = db.query(Assignment).filter(
        Assignment.user_id == current_user.id,
        Assignment.deleted_at == None,
        Assignment.status == AssignmentStatus.pending,
        Assignment.due_date <= week_from_now
    ).order_by(Assignment.due_date).all()

    # weekly load hours
    weekly_load_hours = sum(a.estimated_hours for a in upcoming_assignments)

    # overdue job followups
    overdue_followups = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id,
        JobApplication.followup_date < now,
        JobApplication.status == JobStatus.applied
    ).count()

    # last workout
    last_workout = db.query(Workout).filter(
        Workout.user_id == current_user.id
    ).order_by(Workout.logged_at.desc()).first()

    days_since_workout = None
    if last_workout and last_workout.logged_at:
        days_since_workout = (now - last_workout.logged_at.replace(tzinfo=timezone.utc)).days

    # monthly spending
    monthly_expenses = db.query(Expense).filter(
        Expense.user_id == current_user.id,
        Expense.spent_at >= start_of_month
    ).all()

    total_spent = sum(e.amount for e in monthly_expenses)
    budget_percent = round((total_spent / current_user.monthly_budget) * 100, 1) if current_user.monthly_budget else 0

    return {
        "user": {"name": current_user.name, "email": current_user.email},
        "assignments": {
            "upcoming": [{"id": str(a.id), "title": a.title, "course": a.course, "due_date": a.due_date, "estimated_hours": a.estimated_hours} for a in upcoming_assignments],
            "weekly_load_hours": weekly_load_hours,
            "weekly_capacity_hours": current_user.weekly_capacity_hours,
            "load_percent": round((weekly_load_hours / current_user.weekly_capacity_hours) * 100, 1) if current_user.weekly_capacity_hours else 0
        },
        "jobs": {
            "overdue_followups": overdue_followups
        },
        "fitness": {
            "days_since_workout": days_since_workout
        },
        "finance": {
            "total_spent": total_spent,
            "monthly_budget": current_user.monthly_budget,
            "budget_percent": budget_percent
        }
    }