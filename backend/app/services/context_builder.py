from sqlalchemy.orm import Session
from app.models.user import User
from app.models.assignment import Assignment, AssignmentStatus
from app.models.job import JobApplication, JobStatus
from app.models.workout import Workout
from app.models.expense import Expense
from datetime import datetime, timezone, timedelta

def build_context(db: Session, user: User) -> dict:
    now = datetime.now(timezone.utc)
    week_from_now = now + timedelta(days=7)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0)

    # assignments due this week
    upcoming = db.query(Assignment).filter(
        Assignment.user_id == user.id,
        Assignment.deleted_at == None,
        Assignment.status == AssignmentStatus.pending,
        Assignment.due_date <= week_from_now
    ).order_by(Assignment.due_date).all()

    weekly_load_hours = sum(a.estimated_hours for a in upcoming)
    load_percent = round((weekly_load_hours / user.weekly_capacity_hours) * 100, 1) if user.weekly_capacity_hours else 0

    # overdue assignments
    overdue = db.query(Assignment).filter(
        Assignment.user_id == user.id,
        Assignment.deleted_at == None,
        Assignment.status == AssignmentStatus.pending,
        Assignment.due_date < now
    ).count()

    # job followups
    overdue_followups = db.query(JobApplication).filter(
        JobApplication.user_id == user.id,
        JobApplication.followup_date < now,
        JobApplication.status == JobStatus.applied
    ).count()

    total_applications = db.query(JobApplication).filter(
        JobApplication.user_id == user.id
    ).count()

    # fitness
    last_workout = db.query(Workout).filter(
        Workout.user_id == user.id
    ).order_by(Workout.logged_at.desc()).first()

    days_since_workout = None
    if last_workout and last_workout.logged_at:
        days_since_workout = (now - last_workout.logged_at.replace(tzinfo=timezone.utc)).days

    # finance
    monthly_expenses = db.query(Expense).filter(
        Expense.user_id == user.id,
        Expense.spent_at >= start_of_month
    ).all()

    total_spent = sum(e.amount for e in monthly_expenses)
    budget_percent = round((total_spent / user.monthly_budget) * 100, 1) if user.monthly_budget else 0

    return {
        "user_name": user.name,
        "assignments": {
            "upcoming_count": len(upcoming),
            "upcoming_titles": [a.title for a in upcoming[:3]],
            "weekly_load_hours": weekly_load_hours,
            "weekly_capacity_hours": user.weekly_capacity_hours,
            "load_percent": load_percent,
            "overdue_count": overdue
        },
        "jobs": {
            "total_applications": total_applications,
            "overdue_followups": overdue_followups
        },
        "fitness": {
            "days_since_workout": days_since_workout
        },
        "finance": {
            "total_spent": total_spent,
            "monthly_budget": user.monthly_budget,
            "budget_percent": budget_percent,
            "days_left_in_month": (start_of_month + timedelta(days=32)).replace(day=1) - now
        }
    }